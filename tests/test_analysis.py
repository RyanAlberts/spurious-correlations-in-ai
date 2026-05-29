# SPDX-License-Identifier: Apache-2.0
"""Analysis tests on synthetic series with known structure (no network)."""
import numpy as np
import pandas as pd

from spurcorr.analysis import (
    best_lag,
    classify,
    correlate,
    cumulative_releases,
    interrupted_time_series,
    partial_correlation,
)


def _years(start=2010, end=2024):
    return pd.to_datetime([f"{y}-01-01" for y in range(start, end + 1)])


def test_cumulative_releases_is_monotone_step():
    idx = _years()
    rel = cumulative_releases(idx, [pd.Timestamp("2020-06-01"), pd.Timestamp("2022-11-30")])
    assert rel.loc["2019-01-01"] == 0
    assert rel.loc["2021-01-01"] == 1   # after the 2020 release
    assert rel.loc["2023-01-01"] == 2   # after both
    assert (rel.diff().dropna() >= 0).all()


def test_its_detects_post_anchor_excess():
    idx = _years()
    # flat ~100 until 2022, then explodes — an "AI word"
    vals = [100] * 13 + [600, 1800]
    s = pd.Series(vals, index=idx, dtype=float)
    its = interrupted_time_series(s, pd.Timestamp("2022-11-30"))
    assert its.aligned is True
    assert its.excess_ratio > 3


def test_its_null_for_flat_series():
    idx = _years()
    s = pd.Series(np.full(len(idx), 50.0) + np.random.default_rng(0).normal(0, 1, len(idx)), index=idx)
    its = interrupted_time_series(s, pd.Timestamp("2022-11-30"))
    assert its.aligned is False
    assert its.excess_ratio < 1.5


def test_classify_candidate_vs_spurious():
    idx = _years()
    rel = cumulative_releases(idx, [pd.Timestamp("2022-11-30"), pd.Timestamp("2023-03-14")])

    ai = pd.Series([100] * 13 + [600, 1800], index=idx, dtype=float)
    its_ai = interrupted_time_series(ai, pd.Timestamp("2022-11-30"))
    corr_ai = correlate(ai, rel)
    lag = best_lag(ai, rel)
    verdict = classify(corr_ai, its_ai, lag, partial_r=0.95)
    assert verdict.label == "candidate-causal"
    assert verdict.needs_review is True

    flat = pd.Series(np.linspace(40, 60, len(idx)), index=idx)
    its_flat = interrupted_time_series(flat, pd.Timestamp("2022-11-30"))
    verdict2 = classify(correlate(flat, rel), its_flat, best_lag(flat, rel), partial_r=0.9)
    assert verdict2.label in {"spurious", "inconclusive"}


def test_negative_control_anomaly_flags_review():
    idx = _years()
    rel = cumulative_releases(idx, [pd.Timestamp("2022-11-30")])
    ai = pd.Series([100] * 13 + [600, 1800], index=idx, dtype=float)
    its = interrupted_time_series(ai, pd.Timestamp("2022-11-30"))
    # A negative control that (wrongly) shows the AI pattern must be escalated.
    verdict = classify(correlate(ai, rel), its, best_lag(ai, rel), 0.9, negative_control=True)
    assert verdict.label == "control-anomaly"
    assert verdict.needs_review is True


def test_partial_correlation_removes_shared_trend():
    # Use many points so the residual correlation is stable.
    idx = pd.date_range("2010-01-01", periods=200, freq="MS")
    t = np.arange(len(idx), dtype=float)
    rng = np.random.default_rng(0)
    z = pd.Series(t, index=idx)
    x = pd.Series(t + rng.normal(0, 1.0, len(idx)), index=idx)
    y = pd.Series(t + rng.normal(0, 1.0, len(idx)), index=idx)
    # x and y correlate ~1 only because both follow z; partialling z should collapse it.
    raw = correlate(x, y).pearson_r
    r, _ = partial_correlation(x, y, z)
    assert raw > 0.99
    assert abs(r) < 0.3
