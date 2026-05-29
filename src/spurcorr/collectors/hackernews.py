# SPDX-License-Identifier: Apache-2.0
"""Hacker News collector via the Algolia search API.

Free, no key, full history. We bucket matching stories+comments by month to build
a term-mention time series — a developer/tech-community discourse signal.

API: https://hn.algolia.com/api/v1/search_by_date
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from .. import http
from .base import Collector, SeriesResult

_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsCollector(Collector):
    source_id = "hackernews"
    granularity = "monthly"

    def __init__(self, since_year: int = 2018) -> None:
        self.since_year = since_year

    def available(self) -> bool:
        try:
            http.get_bytes(_URL, params={"query": "test", "hitsPerPage": 1},
                           timeout=12, use_cache=False)
            return True
        except Exception:
            return False

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        query = term_cfg.get("hn_query") or term_cfg.get("gdelt_query") or term_cfg["term"]
        counts: dict[pd.Timestamp, int] = {}
        today = dt.date.today()
        # Walk month buckets using numericFilters on created_at_i (unix seconds).
        month = dt.date(self.since_year, 1, 1)
        while month <= today:
            nxt = (month.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
            lo = int(dt.datetime(month.year, month.month, 1).timestamp())
            hi = int(dt.datetime(nxt.year, nxt.month, 1).timestamp())
            try:
                data = http.get_json(
                    _URL,
                    params={
                        "query": query,
                        "tags": "(story,comment)",
                        "numericFilters": f"created_at_i>={lo},created_at_i<{hi}",
                        "hitsPerPage": 0,
                    },
                    max_age_s=7 * 24 * 3600,
                )
                counts[pd.Timestamp(month)] = int(data.get("nbHits", 0))
            except Exception:
                pass
            month = nxt
        if not counts:
            return None
        series = pd.Series(counts).sort_index()
        return SeriesResult(
            term=term_cfg["term"],
            source=self.source_id,
            granularity="monthly",
            series=series,
            real=True,
            provenance=f"Hacker News (Algolia) monthly story+comment matches for '{query}'.",
            meta={"query": query},
        )
