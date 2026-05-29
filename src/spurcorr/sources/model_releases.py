# SPDX-License-Identifier: Apache-2.0
"""Load and query the curated model-release timeline (data/model_releases.yaml)."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import pandas as pd
import yaml

from ..paths import MODEL_RELEASES_YAML


@dataclass(frozen=True)
class Release:
    date: dt.date
    lab: str
    model: str
    family: str
    landmark: bool = False


def load_releases(path=MODEL_RELEASES_YAML) -> list[Release]:
    raw = yaml.safe_load(open(path, encoding="utf-8"))
    out: list[Release] = []
    for r in raw.get("releases", []):
        d = r["date"]
        date = d if isinstance(d, dt.date) else dt.date.fromisoformat(str(d))
        out.append(Release(date=date, lab=r["lab"], model=r["model"],
                           family=r["family"], landmark=bool(r.get("landmark", False))))
    return sorted(out, key=lambda x: x.date)


def family_dates(releases: list[Release], family: str) -> list[pd.Timestamp]:
    return [pd.Timestamp(r.date) for r in releases if r.family == family]


def landmark_dates(releases: list[Release]) -> list[pd.Timestamp]:
    """Dates most useful as the single anchor for interrupted-time-series tests."""
    lm = [pd.Timestamp(r.date) for r in releases if r.landmark]
    return lm or [pd.Timestamp("2022-11-30")]  # ChatGPT as the default anchor
