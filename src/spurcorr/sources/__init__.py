# SPDX-License-Identifier: Apache-2.0
"""Curated reference data: the model-release timeline and over-representation ratios."""
from __future__ import annotations

from .model_releases import Release, load_releases, family_dates, landmark_dates
from .overrep import OverRep, load_overrep

__all__ = ["Release", "load_releases", "family_dates", "landmark_dates", "OverRep", "load_overrep"]
