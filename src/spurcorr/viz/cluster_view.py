# SPDX-License-Identifier: Apache-2.0
"""Concept-cluster trajectories — AI-favoured *concepts* rising over time."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..analysis.cluster import CLUSTER_LABELS
from ..paths import CHARTS_DIR
from . import theme


def plot_clusters(cluster_series: dict[str, pd.Series], release_markers, outdir: Path = CHARTS_DIR,
                  fmt: str = "png") -> Path:
    """One line per concept cluster (z-scored mean trajectory)."""
    import matplotlib.pyplot as plt

    outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = theme.base_fig(figsize=(10, 5.5))
    cmap = plt.get_cmap("tab10")
    for i, (cluster, s) in enumerate(sorted(cluster_series.items())):
        ax.plot(s.index, s.values, lw=2.0, marker="o", ms=3,
                color=cmap(i % 10), label=CLUSTER_LABELS.get(cluster, cluster))
    for ts, name in release_markers:
        ax.axvline(ts, color=theme.MARKER_COLOR, lw=1.0, alpha=0.5)
        ax.text(ts, ax.get_ylim()[1], f" {name}", rotation=90, va="top", ha="left",
                fontsize=7, color=theme.MARKER_COLOR)
    ax.set_ylabel("z-scored cluster interest")
    ax.set_title("AI-vocabulary concept clusters over time", fontsize=13,
                 fontweight="bold", loc="left")
    ax.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
    fig.tight_layout()
    path = outdir / f"clusters.{fmt}"
    fig.savefig(path, bbox_inches="tight", facecolor=theme.BG)
    plt.close(fig)
    return path
