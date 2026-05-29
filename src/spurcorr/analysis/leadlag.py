# SPDX-License-Identifier: Apache-2.0
"""Lead-lag cross-correlation — testing the diffusion-lag hypothesis (H1).

If AI influence is real, a word's interest should rise *after* releases, with some
lag, as the usage diffuses through human writing. We shift the word series against
the release-driven series across a range of lags and report the lag that maximises
correlation. A positive best-lag is consistent with diffusion; a zero/negative lag
weakens the causal story.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class LagResult:
    best_lag_steps: int        # in units of the series' sampling step (years/months)
    best_corr: float
    unit: str


def best_lag(word: pd.Series, reference: pd.Series, max_lag: int = 3, unit: str = "years") -> LagResult:
    """Shift ``word`` backward by 0..max_lag steps and correlate with ``reference``.

    Both series are first put on a common index. Lag *k* means "word at time t+k vs
    reference at time t" — i.e. the word responds k steps after the reference moves.
    """
    df = pd.concat([word.rename("w"), reference.rename("r")], axis=1).dropna()
    if len(df) < 4:
        return LagResult(0, float("nan"), unit)
    best = (0, -2.0)
    for k in range(0, max_lag + 1):
        w = df["w"].shift(-k)
        pair = pd.concat([w, df["r"]], axis=1).dropna()
        if len(pair) < 3:
            continue
        c = np.corrcoef(pair.iloc[:, 0], pair.iloc[:, 1])[0, 1]
        if not np.isnan(c) and c > best[1]:
            best = (k, float(c))
    return LagResult(best[0], best[1], unit)
