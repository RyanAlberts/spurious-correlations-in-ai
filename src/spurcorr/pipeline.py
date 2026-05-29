# SPDX-License-Identifier: Apache-2.0
"""Weekly pipeline: collect -> analyze -> cluster -> catalog -> visualize -> report.

Run end-to-end with ``python -m spurcorr.pipeline``. Every step is a module under
``spurcorr/`` so the system is modular and re-runnable on a Saturday cron. Collectors
that cannot reach their host are skipped automatically; the run uses whatever real
data is available and never publishes synthesised series.
"""
from __future__ import annotations

import argparse

import pandas as pd
import yaml

from . import analysis as A
from .catalog import Catalog
from .collectors import REGISTRY
from .paths import VOCAB_YAML, ensure_dirs
from .report import build_readme
from .sources import load_overrep, load_releases
from .viz import plot_clusters, plot_dual_axis, plot_overrep_leaderboard

# Which source to prefer as the "primary" series for correlation/charts when several
# are available — longest, most reproducible history first.
PRIMARY_PREFERENCE = [
    "pubmed_kobak", "wikipedia", "gdelt", "wiktionary",
    "hackernews", "google_trends_csv", "linkedin_manual",
]


def _load_terms(path) -> tuple[list[dict], dict[str, str]]:
    raw = yaml.safe_load(open(path, encoding="utf-8"))
    terms = raw.get("terms", [])
    cluster_of = {t["term"]: t.get("cluster", "uncategorized") for t in terms}
    return terms, cluster_of


def run(seeds=VOCAB_YAML, offline: bool = False, top_leaderboard: int = 25,
        notes: str = "") -> dict:
    ensure_dirs()
    terms, cluster_of = _load_terms(seeds)
    releases = load_releases()
    release_dates = [pd.Timestamp(r.date) for r in releases]
    landmark_markers = [(pd.Timestamp(r.date), r.model) for r in releases if r.landmark]
    # Anchor the interrupted-time-series test at the first landmark release (ChatGPT).
    anchor = min((pd.Timestamp(r.date) for r in releases if r.landmark),
                 default=pd.Timestamp("2022-11-30"))
    overrep = load_overrep(attempt_refresh=not offline)

    # --- instantiate reachable collectors ---
    collectors = {}
    for sid, cls in REGISTRY.items():
        if offline and sid != "pubmed_kobak":
            continue
        inst = cls()
        if inst.available():
            collectors[sid] = inst
    sources_used = sorted(collectors)
    print(f"[collect] reachable sources: {sources_used or 'NONE'}")

    cat = Catalog()
    cat.start_run(notes=notes or f"offline={offline}")

    # --- collect every term from every reachable source; pick a primary series ---
    primary: dict[str, tuple] = {}   # term -> (source, SeriesResult)
    for t in terms:
        cat.upsert_term(t["term"], t.get("cluster", "uncategorized"),
                        bool(t.get("negative_control", False)))
        results = {}
        for sid, coll in collectors.items():
            try:
                res = coll.collect(t)
            except Exception as exc:  # one bad term shouldn't kill the run
                print(f"  ! {sid}:{t['term']} failed: {exc}")
                res = None
            if res is not None and res.real and not res.series.dropna().empty:
                results[sid] = res
                cat.write_observations(t["term"], sid, res.series)
        for sid in PRIMARY_PREFERENCE:
            if sid in results:
                primary[t["term"]] = (sid, results[sid])
                break

    if not primary:
        print("[abort] no real series collected for any term; nothing to analyze.")
        cat.close()
        return {"status": "no-data", "sources_used": sources_used}

    # --- build the confound control from negative-control terms ---
    control_series = A.control_from_series([
        sr.series for term, (sid, sr) in primary.items()
        if cluster_of.get(term) == "control"
    ])

    # --- analyze each term ---
    chart_paths: dict = {}
    series_by_term: dict[str, pd.Series] = {}
    for t in terms:
        if t["term"] not in primary:
            continue
        sid, sr = primary[t["term"]]
        word = sr.series.astype(float)
        series_by_term[t["term"]] = word
        rel = A.cumulative_releases(word.index, release_dates)

        corr = A.correlate(word, rel)
        its = A.interrupted_time_series(word, anchor)
        unit = "years" if sr.granularity == "yearly" else sr.granularity
        lag = A.best_lag(word, rel, max_lag=3, unit=unit)
        partial_r = (A.partial_correlation(word, rel, control_series)[0]
                     if control_series is not None else float("nan"))

        verdict = A.classify(
            corr, its, lag, partial_r,
            negative_control=bool(t.get("negative_control", False)),
            out_of_domain=False,  # v1 scope is language/search-frequency only
        )

        excess = its.excess_ratio
        cat.write_correlation({
            "term": t["term"], "cluster": t.get("cluster"), "family": "all",
            "pearson_r": round(corr.pearson_r, 4), "spearman_r": round(corr.spearman_r, 4),
            "jump_ratio": round(excess, 3) if excess == excess else None,
            "changepoint": str(its.takeoff.date()) if its.takeoff is not None else None,
            "gap_days": None, "aligned": int(bool(its.aligned)),
            "best_lag": lag.best_lag_steps, "partial_r": round(partial_r, 4) if partial_r == partial_r else None,
            "overrep_ratio": overrep.ratio_for(t["term"]),
            "label": verdict.label, "score": round(verdict.score, 3),
            "needs_review": int(verdict.needs_review), "provenance": sr.provenance,
        })

        chart_paths[t["term"]] = plot_dual_axis(
            t["term"], word, rel, landmark_markers, corr.pearson_r,
            word_units=sr.meta.get("units", "interest"),
            label="; ".join(verdict.reasons), classification=verdict.label,
        )
        print(f"  · {t['term']:<14} r={corr.pearson_r:+.2f} excess="
              f"{excess if excess == excess else float('nan'):.1f}x "
              f"partial={partial_r:+.2f} -> {verdict.label}")

    # --- clusters, leaderboard, snapshot, README ---
    cluster_series = A.cluster_trajectories(series_by_term, cluster_of)
    cluster_chart = plot_clusters(cluster_series, landmark_markers) if cluster_series else None
    leaderboard_chart = plot_overrep_leaderboard(overrep.df, top=top_leaderboard)

    snap = cat.snapshot_json()
    corr_df = cat.correlations_df()

    env_note = ("Live web collectors were unreachable in this environment, so the run is "
                "anchored on the real, reproducible PubMed/Kobak word-frequency data; "
                "the daily collectors (Wikipedia/Wiktionary/GDELT/Hacker News) run in CI "
                "and locally where those hosts are reachable."
                if sources_used == ["pubmed_kobak"] else "")

    build_readme(
        corr_df, overrep.df, releases, chart_paths, cluster_chart, leaderboard_chart,
        run_date=cat.run_date, env_note=env_note, sources_used=sources_used,
    )
    cat.close()

    n_cand = int((corr_df["label"] == "candidate-causal").sum()) if not corr_df.empty else 0
    print(f"[done] {len(corr_df)} terms · {n_cand} candidate-causal · snapshot {snap.name}")
    return {"status": "ok", "sources_used": sources_used, "n_terms": len(corr_df),
            "n_candidate_causal": n_cand, "snapshot": str(snap)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Spurious Correlations in AI — weekly pipeline")
    ap.add_argument("--seeds", default=str(VOCAB_YAML), help="path to vocabulary YAML")
    ap.add_argument("--offline", action="store_true",
                    help="use only the reproducible PubMed/Kobak source (skip live web collectors)")
    ap.add_argument("--top", type=int, default=25, help="leaderboard size")
    ap.add_argument("--notes", default="", help="run notes recorded in the catalog")
    args = ap.parse_args()
    res = run(seeds=args.seeds, offline=args.offline, top_leaderboard=args.top, notes=args.notes)
    print(res)


if __name__ == "__main__":
    main()
