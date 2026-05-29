# SPDX-License-Identifier: Apache-2.0
"""Interrupted-time-series + changepoint detection.

The real test of "did a model release move this word" is not the correlation
coefficient (two rising lines always correlate) but whether the word's trajectory
**breaks away from its own pre-release trend** after a release.

The primary, discriminating test is :func:`interrupted_time_series`: fit the word's
pre-release (log-linear) trend, extrapolate it past the anchor release, and measure
the *excess* (observed / counterfactual). Because every word is judged against its
own prior trend, "everything went up in 2023" is controlled for automatically — AI
words show large excess, ordinary words show ~1. This mirrors the excess-frequency
method of Kobak et al. (2025). :func:`detect_changepoint` is retained as a secondary
descriptor (and for daily live series where a roaming break is meaningful).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import ruptures as rpt


@dataclass
class ITSResult:
    anchor: pd.Timestamp | None
    excess_ratio: float          # mean(observed_post / counterfactual_post); ~1 means no break
    observed_post_mean: float
    expected_post_mean: float
    takeoff: pd.Timestamp | None # post point with the largest excess
    aligned: bool                # excess materially > 1, i.e. a real post-release break
    n_pre: int
    n_post: int


def interrupted_time_series(
    series: pd.Series,
    anchor: pd.Timestamp,
    *,
    excess_threshold: float = 1.5,
) -> ITSResult:
    """Excess of the post-anchor data over the extrapolated pre-anchor trend.

    Fits ``log(value) ~ year`` on points before ``anchor`` and extrapolates to the
    points on/after it; ``excess_ratio`` is the mean observed/expected over the post
    window. ``aligned`` is True when that excess clears ``excess_threshold``.
    """
    s = series.dropna()
    s = s[s > 0]
    if len(s) < 4:
        return ITSResult(anchor, float("nan"), float("nan"), float("nan"), None, False, 0, 0)
    years = np.array([d.year + (d.dayofyear - 1) / 365.0 for d in s.index])
    vals = s.values.astype(float)
    pre = s.index < anchor
    post = ~pre
    if pre.sum() < 3 or post.sum() < 1:
        return ITSResult(anchor, float("nan"), float("nan"), float("nan"), None, False,
                         int(pre.sum()), int(post.sum()))
    b, a = np.polyfit(years[pre], np.log(vals[pre]), 1)
    expected = np.exp(a + b * years[post])
    ratios = vals[post] / expected
    excess = float(np.mean(ratios))
    takeoff = s.index[post][int(np.argmax(ratios))]
    return ITSResult(
        anchor=anchor,
        excess_ratio=excess,
        observed_post_mean=float(np.mean(vals[post])),
        expected_post_mean=float(np.mean(expected)),
        takeoff=takeoff,
        aligned=excess >= excess_threshold,
        n_pre=int(pre.sum()),
        n_post=int(post.sum()),
    )


@dataclass
class ChangepointResult:
    breakpoint: pd.Timestamp | None
    pre_mean: float
    post_mean: float
    jump_ratio: float           # post_mean / pre_mean (how big the break is)


def detect_changepoint(series: pd.Series) -> ChangepointResult:
    """Find the single most likely level shift in ``series``."""
    s = series.dropna()
    if len(s) < 4:
        return ChangepointResult(None, np.nan, np.nan, np.nan)
    signal = s.values.astype(float).reshape(-1, 1)
    # Binary segmentation with an L2 cost finds the dominant mean shift; robust for
    # short (yearly) series where Pelt's penalty tuning is finicky.
    algo = rpt.Binseg(model="l2").fit(signal)
    bkps = algo.predict(n_bkps=1)        # returns [idx, len]
    idx = bkps[0]
    if idx <= 0 or idx >= len(s):
        return ChangepointResult(None, np.nan, np.nan, np.nan)
    pre = float(np.mean(signal[:idx]))
    post = float(np.mean(signal[idx:]))
    jump = post / pre if pre else np.inf
    return ChangepointResult(s.index[idx], pre, post, jump)


def release_alignment(
    cp: ChangepointResult,
    release_dates: list[pd.Timestamp],
    window_days: int = 540,
) -> dict:
    """Does the breakpoint fall within ``window_days`` AFTER any release?

    Returns the nearest release, the signed gap in days (positive = break is after
    the release, consistent with diffusion), and an ``aligned`` boolean.
    """
    if cp.breakpoint is None or not release_dates:
        return {"aligned": False, "nearest_release": None, "gap_days": None}
    bp = pd.Timestamp(cp.breakpoint)
    after = [(bp - d).days for d in release_dates if (bp - d).days >= 0]
    if not after:
        nearest = min(release_dates, key=lambda d: abs((bp - d).days))
        return {"aligned": False, "nearest_release": nearest, "gap_days": int((bp - nearest).days)}
    gap = min(after)
    nearest = next(d for d in release_dates if (bp - d).days == gap)
    return {"aligned": gap <= window_days, "nearest_release": nearest, "gap_days": int(gap)}
