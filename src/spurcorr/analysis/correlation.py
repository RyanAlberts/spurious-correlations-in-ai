# SPDX-License-Identifier: Apache-2.0
"""Correlation primitives + building the model-release reference series.

The "release-driven" series we correlate a word against is the **cumulative count
of model releases** up to each date: a monotone step function that encodes "how
much AI is out in the world." Correlating a word's interest against it answers the
Tyler-Vigen question — and we then stress-test that *r* with the rigor layer
(changepoint, lead-lag, confound) so we don't mistake a shared upward drift for a
mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class CorrResult:
    pearson_r: float
    pearson_p: float
    spearman_r: float
    spearman_p: float
    n: int


def cumulative_releases(index: pd.DatetimeIndex, release_dates: list[pd.Timestamp]) -> pd.Series:
    """Step function: number of releases on or before each point in ``index``."""
    dates = np.sort(np.array([np.datetime64(d) for d in release_dates]))
    idx_np = index.values.astype("datetime64[ns]")
    counts = np.searchsorted(dates.astype("datetime64[ns]"), idx_np, side="right")
    return pd.Series(counts.astype(float), index=index, name="cumulative_releases")


def align(a: pd.Series, b: pd.Series, freq: str | None = None) -> tuple[pd.Series, pd.Series]:
    """Align two series onto a common time grid.

    If ``freq`` is given, both are resampled (mean) to that frequency; otherwise we
    use the union of dates with linear interpolation, then keep the overlap. This
    lets a yearly word series be compared with a daily release step function.
    """
    if freq:
        a = a.resample(freq).mean()
        b = b.resample(freq).mean()
        df = pd.concat([a, b], axis=1).dropna()
        return df.iloc[:, 0], df.iloc[:, 1]

    union = a.index.union(b.index)
    ai = a.reindex(union).interpolate(method="time").reindex(a.index.union(b.index))
    bi = b.reindex(union).interpolate(method="time")
    df = pd.concat([ai.rename("a"), bi.rename("b")], axis=1).dropna()
    return df["a"], df["b"]


def correlate(a: pd.Series, b: pd.Series) -> CorrResult:
    """Pearson + Spearman between two already-aligned series."""
    df = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(df) < 3:
        return CorrResult(np.nan, np.nan, np.nan, np.nan, len(df))
    pr, pp = stats.pearsonr(df["a"], df["b"])
    sr, sp = stats.spearmanr(df["a"], df["b"])
    return CorrResult(float(pr), float(pp), float(sr), float(sp), len(df))
