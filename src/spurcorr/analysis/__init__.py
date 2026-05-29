# SPDX-License-Identifier: Apache-2.0
"""Statistical analysis: correlation, changepoints, lead-lag, confound control, classification."""
from __future__ import annotations

from .changepoint import (
    ChangepointResult,
    ITSResult,
    detect_changepoint,
    interrupted_time_series,
    release_alignment,
)
from .classify import Classification, classify
from .cluster import CLUSTER_LABELS, cluster_trajectories
from .confound import control_from_series, partial_correlation
from .correlation import CorrResult, align, correlate, cumulative_releases
from .leadlag import LagResult, best_lag

__all__ = [
    "CorrResult", "align", "correlate", "cumulative_releases",
    "ChangepointResult", "detect_changepoint", "release_alignment",
    "ITSResult", "interrupted_time_series",
    "LagResult", "best_lag",
    "partial_correlation", "control_from_series",
    "Classification", "classify",
    "CLUSTER_LABELS", "cluster_trajectories",
]
