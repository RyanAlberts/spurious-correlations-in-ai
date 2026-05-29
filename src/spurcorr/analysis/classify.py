# SPDX-License-Identifier: Apache-2.0
"""Combine the statistical signals into a single, explainable verdict.

We deliberately separate the *hook* (a big correlation) from the *claim* (an AI
release plausibly moved this word). The discriminating evidence is the interrupted-
time-series **excess**: did the word break away from its own pre-release trend after
a release? A term is promoted to ``candidate-causal`` only when a strong correlation
is backed by a real post-release excess and survives the confound control — and even
then it is flagged for human review. Everything else is ``spurious`` (the honest
default here) or ``inconclusive``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .changepoint import ITSResult
from .correlation import CorrResult
from .leadlag import LagResult


@dataclass
class Classification:
    label: str                       # candidate-causal | spurious | inconclusive | control-anomaly
    score: float                     # 0..1 confidence in a real AI link
    reasons: list[str] = field(default_factory=list)
    needs_review: bool = False       # gate for human validation
    out_of_domain: bool = False      # true if relation leaves language/search-frequency


def _ok(x: float) -> bool:
    return x is not None and not (isinstance(x, float) and np.isnan(x))


def classify(
    corr: CorrResult,
    its: ITSResult,
    lag: LagResult,
    partial_r: float,
    *,
    negative_control: bool = False,
    out_of_domain: bool = False,
) -> Classification:
    reasons: list[str] = []

    strong_corr = _ok(corr.pearson_r) and corr.pearson_r >= 0.7
    excess = _ok(its.excess_ratio) and its.aligned          # post-release break vs own trend
    big_excess = _ok(its.excess_ratio) and its.excess_ratio >= 3.0
    diffusion = lag.best_lag_steps >= 0 and _ok(lag.best_corr) and lag.best_corr >= 0.5
    survives = _ok(partial_r) and abs(partial_r) >= 0.4

    if strong_corr:
        reasons.append(f"strong correlation r={corr.pearson_r:.2f}")
    if excess:
        anchor = its.anchor.date() if its.anchor is not None else "?"
        reasons.append(f"post-release excess x{its.excess_ratio:.1f} vs own pre-{anchor} trend")
    elif _ok(its.excess_ratio):
        reasons.append(f"no excess over own trend (x{its.excess_ratio:.1f})")
    if big_excess:
        reasons.append("excess is large (>3x)")
    if diffusion:
        reasons.append(f"diffusion lag {lag.best_lag_steps} {lag.unit}")
    reasons.append(f"survives confound control (partial r={partial_r:.2f})" if survives
                   else "weak under confound control")

    score = (0.20 * strong_corr + 0.40 * excess + 0.20 * big_excess
             + 0.10 * diffusion + 0.10 * survives)
    score = max(0.0, min(1.0, score))

    if negative_control:
        if strong_corr and excess:
            return Classification("control-anomaly", score,
                                  reasons + ["NEGATIVE CONTROL shows AI-like excess — investigate method"],
                                  needs_review=True, out_of_domain=out_of_domain)
        return Classification("spurious", round(1.0 - score, 3),
                              ["negative control behaves as expected (no post-release excess)"],
                              out_of_domain=out_of_domain)

    if strong_corr and excess and survives:
        label, needs_review = "candidate-causal", True
    elif strong_corr and not excess:
        # the Tyler-Vigen case: lines correlate but the word never broke from its own trend
        label, needs_review = "spurious", False
    else:
        label, needs_review = "inconclusive", False

    if out_of_domain:
        needs_review = True  # anything outside language/search-frequency is held for review

    return Classification(label, round(score, 3), reasons,
                          needs_review=needs_review, out_of_domain=out_of_domain)
