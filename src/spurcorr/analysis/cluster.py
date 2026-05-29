# SPDX-License-Identifier: Apache-2.0
"""Concept clustering of AI-favoured vocabulary.

v1 uses the curated concept labels from ``ai_vocabulary.yaml`` (a stable, readable
taxonomy) and aggregates each cluster's normalised trajectory so we can talk about
*concepts* rising, not just words — the unit the future social campaigns will use.
A data-driven KMeans-on-trajectories option is left for the fast-follow.
"""
from __future__ import annotations

import pandas as pd

CLUSTER_LABELS = {
    "academic-hedging": "Academic hedging (delve, nuanced, intricate)",
    "emphasis-structure": "Emphasis & structure (underscore, notably, pivotal)",
    "promotional": "Promotional / boosterish (showcasing, boasts, garnered)",
    "inspirational": "Inspirational (tapestry, testament)",
    "stylistic": "Stylistic markers (em-dash, 'not just X but Y')",
    "control": "Negative controls (umbrella, bicycle, Saturday)",
}


def cluster_trajectories(series_by_term: dict[str, pd.Series], cluster_of: dict[str, str]) -> dict[str, pd.Series]:
    """Mean z-scored trajectory per cluster.

    Each term series is z-scored (so high- and low-volume words contribute equally),
    then averaged within its cluster on the shared time index.
    """
    buckets: dict[str, list[pd.Series]] = {}
    for term, s in series_by_term.items():
        s = s.dropna()
        if s.empty or s.std(ddof=0) == 0:
            continue
        z = (s - s.mean()) / s.std(ddof=0)
        buckets.setdefault(cluster_of.get(term, "uncategorized"), []).append(z)
    out: dict[str, pd.Series] = {}
    for cluster, series_list in buckets.items():
        df = pd.concat(series_list, axis=1)
        out[cluster] = df.mean(axis=1).rename(cluster)
    return out
