# SPDX-License-Identifier: Apache-2.0
"""The flagship chart: a word's interest vs the model-release timeline on dual axes."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..paths import CHARTS_DIR
from . import theme


def plot_dual_axis(
    term: str,
    word_series: pd.Series,
    release_series: pd.Series,
    release_markers: list[tuple[pd.Timestamp, str]],
    r: float,
    *,
    word_units: str = "interest",
    label: str = "",
    classification: str = "",
    outdir: Path = CHARTS_DIR,
    fmt: str = "png",
) -> Path:
    """Render and save the dual-axis correlation chart for ``term``.

    Left axis: the word's measured interest. Right axis: cumulative model releases.
    Vertical markers flag landmark releases. The correlation coefficient is shown
    large, Tyler-Vigen style.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    fig, ax1 = theme.base_fig()

    ax1.plot(word_series.index, word_series.values, color=theme.WORD_COLOR,
             lw=2.4, marker="o", ms=3, label=term)
    ax1.set_ylabel(f"“{term}” — {word_units}", color=theme.WORD_COLOR)
    ax1.tick_params(axis="y", labelcolor=theme.WORD_COLOR)

    ax2 = ax1.twinx()
    ax2.spines["top"].set_visible(False)
    ax2.plot(release_series.index, release_series.values, color=theme.RELEASE_COLOR,
             lw=2.0, ls="--", label="cumulative AI model releases")
    ax2.set_ylabel("cumulative AI model releases", color=theme.RELEASE_COLOR)
    ax2.tick_params(axis="y", labelcolor=theme.RELEASE_COLOR)

    for ts, name in release_markers:
        ax1.axvline(ts, color=theme.MARKER_COLOR, lw=1.0, alpha=0.5)
        ax1.text(ts, ax1.get_ylim()[1], f" {name}", rotation=90, va="top",
                 ha="left", fontsize=7, color=theme.MARKER_COLOR)

    theme.annotate_r(ax1, r)
    title = f"Is “{term}” an AI word?"
    if classification:
        title += f"   [{classification}]"
    ax1.set_title(title, fontsize=13, fontweight="bold", loc="left")
    if label:
        fig.text(0.015, -0.02, label, fontsize=7.5, color=theme.MARKER_COLOR)

    fig.tight_layout()
    slug = "".join(c if c.isalnum() else "_" for c in term.lower()).strip("_")
    path = outdir / f"corr_{slug}.{fmt}"
    fig.savefig(path, bbox_inches="tight", facecolor=theme.BG)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path
