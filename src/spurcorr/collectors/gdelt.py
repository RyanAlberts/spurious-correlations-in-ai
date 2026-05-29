# SPDX-License-Identifier: Apache-2.0
"""GDELT DOC 2.0 collector — term frequency in global online news.

`timelinevolraw` returns the raw volume of matching news articles over time
(near-real-time, 15-min resolution; we request daily). GDELT only guarantees a
~3-month rolling window, so this is a *forward-looking* signal that the weekly
pipeline snapshots and appends to the catalog over time (it is not a back-test
source on its own).

API: https://api.gdeltproject.org/api/v2/doc/doc
"""
from __future__ import annotations

import pandas as pd

from .. import http
from .base import Collector, SeriesResult

_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class GdeltCollector(Collector):
    source_id = "gdelt"
    granularity = "daily"

    def __init__(self, timespan: str = "3m") -> None:
        self.timespan = timespan

    def available(self) -> bool:
        try:
            http.get_bytes(
                _URL,
                params={"query": "climate", "mode": "timelinevolraw",
                        "format": "json", "timespan": "1d"},
                timeout=12, use_cache=False,
            )
            return True
        except Exception:
            return False

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        query = term_cfg.get("gdelt_query") or term_cfg["term"]
        params = {
            "query": f"{query} sourcelang:english",
            "mode": "timelinevolraw",
            "format": "json",
            "timespan": self.timespan,
        }
        try:
            data = http.get_json(_URL, params=params, max_age_s=24 * 3600)
        except Exception:
            return None
        timeline = data.get("timeline", [])
        if not timeline:
            return None
        points = timeline[0].get("data", [])
        if not points:
            return None
        idx = pd.to_datetime([p["date"] for p in points])
        vals = [p["value"] for p in points]
        return SeriesResult(
            term=term_cfg["term"],
            source=self.source_id,
            granularity="daily",
            series=pd.Series(vals, index=idx),
            real=True,
            provenance=f"GDELT DOC 2.0 timelinevolraw, query '{query}' (English news article volume).",
            meta={"query": query, "window": self.timespan},
        )
