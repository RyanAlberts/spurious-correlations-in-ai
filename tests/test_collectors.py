# SPDX-License-Identifier: Apache-2.0
"""Collector + source tests that do not touch the network."""
import gzip
import io

import pandas as pd

from spurcorr.collectors.base import SeriesResult
from spurcorr.collectors.manual import _slug
from spurcorr.collectors.pubmed_kobak import PubMedKobakCollector
from spurcorr.sources import load_overrep, load_releases


def test_series_result_normalises_index():
    s = pd.Series([1, 2, 3], index=["2020-01-01", "2021-01-01", "2022-01-01"])
    res = SeriesResult("x", "test", "yearly", s, real=True, provenance="t")
    assert isinstance(res.series.index, pd.DatetimeIndex)
    assert res.series.is_monotonic_increasing


def test_overrep_loads_and_flags_suspects():
    over = load_overrep()
    assert not over.df.empty
    # the headline phrase and ratio survive the round-trip
    assert over.ratio_for("provide a valuable insight") == 182
    # a single word matches a containing phrase
    assert over.ratio_for("pivotal") is not None
    # OCR garbles are flagged, not silently dropped
    suspects = over.suspect_entries()
    assert (suspects["phrase"] == "a serf reminder").any()
    assert suspects["suggested"].notna().any()


def test_model_releases_have_a_landmark():
    rels = load_releases()
    assert any(r.landmark for r in rels)
    assert all(r.date.year >= 2020 for r in rels)


def test_pubmed_collect_from_injected_matrix(monkeypatch):
    """Exercise collect() logic without network by injecting a tiny matrix."""
    years = list(range(2010, 2025))
    rows = {
        "delve": [50] * 13 + [600, 1800],
        "umbrella": [800] * 15,
        "": [1_000_000] * 15,  # totals row
    }
    df = pd.DataFrame({"word": list(rows), **{str(y): [rows[w][i] for w in rows]
                                              for i, y in enumerate(years)}})
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(df.to_csv(index=False).encode())
    payload = buf.getvalue()

    monkeypatch.setattr("spurcorr.collectors.pubmed_kobak.http.get_bytes",
                        lambda *a, **k: payload)
    monkeypatch.setattr("spurcorr.collectors.pubmed_kobak.http.get_text",
                        lambda *a, **k: "word\ndelve\n")

    c = PubMedKobakCollector()
    res = c.collect({"term": "delve", "pubmed_word": "delve"})
    assert res is not None and res.real
    # proportion 1800/1e6 -> 1800 ppm in 2024
    assert abs(res.series.iloc[-1] - 1800) < 1e-6
    assert c.collect({"term": "missing", "pubmed_word": "zzzznotaword"}) is None


def test_slug():
    assert _slug("A Nuanced Understanding!") == "a_nuanced_understanding"
