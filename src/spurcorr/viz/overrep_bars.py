# SPDX-License-Identifier: Apache-2.0
"""The GPTZero-style over-representation leaderboard: 'N× more frequent in AI'."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..paths import CHARTS_DIR
from . import theme


def plot_overrep_leaderboard(df: pd.DataFrame, top: int = 25, outdir: Path = CHARTS_DIR,
                             fmt: str = "png") -> Path:
    """Horizontal ranked bars of phrase over-representation ratios.

    ``df`` needs columns ``phrase`` and ``ratio``. Suspected-OCR rows (if a
    ``suspect`` column exists) are hatched to signal "needs review".
    """
    import matplotlib.pyplot as plt

    d = df.sort_values("ratio", ascending=True).tail(top)
    outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, max(5, 0.32 * len(d))), dpi=130)
    fig.patch.set_facecolor(theme.BG)
    ax.set_facecolor(theme.BG)

    suspect = d["suspect"] if "suspect" in d.columns else pd.Series(False, index=d.index)
    colors = [theme.MARKER_COLOR if s else theme.WORD_COLOR for s in suspect]
    bars = ax.barh(d["phrase"], d["ratio"], color=colors)
    for s, bar in zip(suspect, bars):
        if s:
            bar.set_hatch("//")

    for bar, val in zip(bars, d["ratio"]):
        ax.text(bar.get_width() + max(d["ratio"]) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}×", va="center", fontsize=8, color=theme.RELEASE_COLOR)

    ax.set_xlabel("times more frequent in AI text than human text")
    ax.set_title("AI vocabulary over-representation (top phrases)", fontsize=13,
                 fontweight="bold", loc="left")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    path = outdir / f"overrep_leaderboard.{fmt}"
    fig.savefig(path, bbox_inches="tight", facecolor=theme.BG)
    plt.close(fig)
    return path
