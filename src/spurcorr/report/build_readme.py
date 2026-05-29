# SPDX-License-Identifier: Apache-2.0
"""Assemble README.md — the product surface — from a pipeline run.

The README leads with the visuals (flagship dual-axis charts + the over-representation
leaderboard), then the findings table, concept clusters, methodology, an FAQ modelled
on GPTZero's, and a productization/pricing appendix. Static prose lives in this module;
the numbers and chart references come from the run.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..paths import ROOT
from ..sources.model_releases import Release

DISCLAIMER = (
    "> **Correlation is not causation.** This project is named *Spurious Correlations in AI* "
    "for a reason: most of what follows is, by construction, spurious. Two lines both sloping "
    "up since 2022 will always correlate. We label a term `candidate-causal` **only** when a big "
    "correlation is backed by a real *post-release break from the word's own prior trend* "
    "(interrupted time series) and survival of a confound control — and even then a human reviews "
    "it before we believe it."
)


def _findings_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No correlations computed this run._"
    cols = ["term", "cluster", "overrep_ratio", "pearson_r", "jump_ratio", "best_lag",
            "partial_r", "label", "score"]
    d = df[cols].copy().sort_values("score", ascending=False)
    head = "| Term | Cluster | AI over-rep | r | level jump | lag (yr) | partial r | verdict | score |\n"
    head += "|---|---|--:|--:|--:|--:|--:|---|--:|\n"
    rows = []
    for _, r in d.iterrows():
        over = f"{r['overrep_ratio']:.0f}×" if pd.notna(r["overrep_ratio"]) else "—"
        jump = f"{r['jump_ratio']:.1f}×" if pd.notna(r["jump_ratio"]) else "—"
        rows.append(
            f"| `{r['term']}` | {r['cluster']} | {over} | {r['pearson_r']:+.2f} | {jump} | "
            f"{int(r['best_lag']) if pd.notna(r['best_lag']) else '—'} | "
            f"{r['partial_r']:+.2f} | {r['label']} | {r['score']:.2f} |"
        )
    return head + "\n".join(rows)


def _flagship_charts(df: pd.DataFrame, chart_paths: dict[str, Path]) -> str:
    """Embed up to three highest-scoring (non-control) charts."""
    ranked = df[df["label"] != "control-anomaly"].sort_values("score", ascending=False)
    out = []
    for _, r in ranked.head(3).iterrows():
        p = chart_paths.get(r["term"])
        if p:
            rel = Path(p).relative_to(ROOT).as_posix()
            out.append(f"### “{r['term']}” — {r['label']} (r = {r['pearson_r']:+.2f})\n\n"
                       f"![{r['term']} correlation]({rel})\n")
    return "\n".join(out) if out else "_No flagship charts this run._"


FAQ = """## FAQ

**What is "AI vocabulary"?**
Words and turns of phrase that large language models produce far more often than
people do — "delve", "a nuanced understanding", "underscores the importance",
"a stark reminder". GPTZero calls its list "a kind of encyclopedia of AI language."

**What does the over-representation ratio mean?**
"182× more frequent in AI" means the phrase appears ~182 times as often in
AI-generated text as in comparable human text. Ratios here come from GPTZero's
published top-100 and from peer-reviewed corpora (Kobak et al. 2025; Liang et al. 2024),
not from us guessing.

**How do you decide a word is "AI-influenced" rather than just trending?**
A correlation alone proves nothing. We require: (1) a structural break in the word's
trajectory that lands *after* a model release, (2) the rise to lag the release (diffusion),
and (3) the correlation to survive a confound control that removes general "everything-AI-
went-up" drift. Words that pass are `candidate-causal` and still get human review.

**Why do you include obviously unrelated control words?**
Words like "umbrella" and "Saturday" are negative controls. They should show *no*
post-release signal. If a control ever lights up, our method is broken — and the
pipeline flags it for review.

**What data do you use?**
PubMed abstract word-frequencies (Kobak et al., yearly, real and reproducible),
plus — where reachable — Wikipedia & Wiktionary pageviews (daily), GDELT news volume,
and Hacker News mentions. Google Trends enters via manual CSV export. See METHODOLOGY.md.

**Is this the same as an AI detector?**
No. We are not scoring whether *your* text is AI-written. We track how AI-favoured
language is diffusing into human discourse over time.
"""

PRICING = """## Appendix — reverse-engineering GPTZero, and what this could sell for

GPTZero's AI-Vocabulary feature sits on top of a paid AI-detection business
(Free → Essential $15/mo → Premium $24/mo → Professional $35/mo; classroom/API tiers
on contract). The underlying vocabulary list is derived from ~3.3M texts comparing AI
vs human writing.

The AI-content-detection market was ~$1.08B in 2025 and is projected at ~$7.84B by 2035
(~26% CAGR). A *trend-data* product — "how AI is reshaping human language over time" —
is an under-served adjacency. Plausible B2B pricing for such a data/API offering:
$199–$500/mo (startup) → $1–5k/mo (mid) → $5–25k/mo (enterprise/SLA).

Cheapest credible comparable for sourcing the social signal: **Brand24 (~$199/mo)**,
which recently added by-model AI mention tracking. SerpApi / Glimpse / X-API were
evaluated and are **skip-for-now** — free Wikipedia/Wiktionary/GDELT/Hacker-News
proxies cover v1. This appendix is a documented backlog item, **not** a launch.
"""


def build_readme(
    corr_df: pd.DataFrame,
    overrep_df: pd.DataFrame,
    releases: list[Release],
    chart_paths: dict[str, Path],
    cluster_chart: Path | None,
    leaderboard_chart: Path | None,
    run_date: str,
    env_note: str,
    sources_used: list[str],
) -> Path:
    lb_rel = Path(leaderboard_chart).relative_to(ROOT).as_posix() if leaderboard_chart else ""
    cl_rel = Path(cluster_chart).relative_to(ROOT).as_posix() if cluster_chart else ""
    n_candidates = int((corr_df["label"] == "candidate-causal").sum()) if not corr_df.empty else 0
    n_review = int((corr_df["needs_review"] == 1).sum()) if not corr_df.empty else 0

    md = f"""# Spurious Correlations in AI

*Finding — and stress-testing — correlations between AI model releases and the rise of
"AI-slop" vocabulary in human discourse.* In the spirit of
[tylervigen.com/spurious-correlations](https://tylervigen.com/spurious-correlations) for the
charts, and [gptzero.me/ai-vocabulary](https://gptzero.me/ai-vocabulary) for the
"N× more frequent in AI" framing — but with our own data and an explicit
spurious-vs-candidate-causal test.

_Last run: **{run_date}** · {len(corr_df) if not corr_df.empty else 0} terms ·
{n_candidates} `candidate-causal` · {n_review} flagged for review · updates weekly (Saturdays)._

{DISCLAIMER}

## The over-representation leaderboard

The phrases LLMs overuse most, vs. humans (GPTZero top-100 snapshot + peer-reviewed corpora).
Hatched bars are suspected transcription errors held for review.

![AI vocabulary over-representation]({lb_rel})

## Flagship correlations

{_flagship_charts(corr_df, chart_paths)}

## All tracked terms this run

{_findings_table(corr_df)}

## Concept clusters

We group AI-favoured vocabulary into concepts so we can talk about *ideas* diffusing,
not just words. z-scored mean trajectory per cluster:

![Concept clusters]({cl_rel})

## Methodology (short version)

For each term we build its interest time-series and the cumulative model-release series,
then compute: Pearson/Spearman correlation, a single-breakpoint changepoint and its
alignment to releases, the best diffusion lag, and a **partial correlation** that removes
general AI-era drift (estimated from negative-control words). The verdict combines all of
these — see [METHODOLOGY.md](METHODOLOGY.md). Hypotheses tracked: diffusion lag, stylistic
markers, definition-seeking (Wiktionary), backlash inflection, cross-model synchrony.

{FAQ}

## Data sources & provenance

This run used: **{', '.join(sources_used) or 'none'}**.
{env_note}
Reference data: model-release timeline (`data/model_releases.yaml`), GPTZero top-100
(`data/gptzero_vocabulary.yaml`), Kobak et al. excess-vocabulary dataset.
The growing dictionary is versioned under `data/catalog/` (one JSON snapshot per run).

{PRICING}

---
*Generated by the `spurcorr` pipeline. Reproduce with `python -m spurcorr.pipeline`.
Apache-2.0. Not affiliated with GPTZero or Tyler Vigen.*
"""
    path = ROOT / "README.md"
    path.write_text(md)
    return path
