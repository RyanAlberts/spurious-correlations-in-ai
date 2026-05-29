# SPDX-License-Identifier: Apache-2.0
"""Confound control via partial correlation.

The obvious objection to any AI-vocabulary correlation: *everything* trended up in
2023-24 (general AI hype, corpus growth, indexing changes). To isolate per-word
signal we partial out a **control series** — for the PubMed back-test we use the
average trajectory of in-domain negative-control words, which captures corpus-wide
drift without being AI-specific. A word whose correlation survives this control is
a stronger ``candidate-causal``; one that collapses is likely riding the tide.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def control_from_series(controls: list[pd.Series]) -> pd.Series | None:
    """Average several control-word series into one normalised drift series."""
    norm = []
    for s in controls:
        s = s.dropna()
        if s.empty or s.std(ddof=0) == 0:
            continue
        norm.append((s - s.mean()) / s.std(ddof=0))
    if not norm:
        return None
    df = pd.concat(norm, axis=1)
    return df.mean(axis=1).rename("control")


def partial_correlation(x: pd.Series, y: pd.Series, z: pd.Series) -> tuple[float, float]:
    """Partial correlation of x and y controlling for z (all aligned on shared index).

    Returns (r, p). Computed by regressing x~z and y~z and correlating the residuals.
    """
    df = pd.concat([x.rename("x"), y.rename("y"), z.rename("z")], axis=1).dropna()
    if len(df) < 4:
        return (float("nan"), float("nan"))
    zc = np.c_[np.ones(len(df)), df["z"].values]

    def resid(col: str) -> np.ndarray:
        beta, *_ = np.linalg.lstsq(zc, df[col].values, rcond=None)
        return df[col].values - zc @ beta

    rx, ry = resid("x"), resid("y")
    if np.std(rx) == 0 or np.std(ry) == 0:
        return (float("nan"), float("nan"))
    r, p = stats.pearsonr(rx, ry)
    return (float(r), float(p))
