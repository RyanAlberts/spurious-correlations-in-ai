# SPDX-License-Identifier: Apache-2.0
"""Shared chart styling — a clean homage to tylervigen.com/spurious-correlations:
two independently-scaled axes, a prominent correlation coefficient, vertical markers
for events. Uses the non-interactive Agg backend so it runs headless in CI."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

WORD_COLOR = "#c0392b"     # the AI-vocabulary series (warm red)
RELEASE_COLOR = "#2c3e50"  # the model-release series (slate)
MARKER_COLOR = "#7f8c8d"
ACCENT = "#16a085"
BG = "#ffffff"


def base_fig(figsize=(10, 5)):
    fig, ax = plt.subplots(figsize=figsize, dpi=130)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for spine in ("top",):
        ax.spines[spine].set_visible(False)
    ax.grid(True, axis="y", alpha=0.15)
    return fig, ax


def annotate_r(ax, r: float, label: str = "correlation") -> None:
    """The Tyler-Vigen move: state the coefficient, big and unmissable."""
    ax.text(
        0.015, 0.95, f"r = {r:+.2f}", transform=ax.transAxes,
        fontsize=20, fontweight="bold", va="top", color=ACCENT,
    )
    ax.text(0.015, 0.875, label, transform=ax.transAxes, fontsize=9,
            va="top", color=MARKER_COLOR)
