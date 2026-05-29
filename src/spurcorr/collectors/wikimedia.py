# SPDX-License-Identifier: Apache-2.0
"""Wikimedia Pageviews collectors (Wikipedia + Wiktionary).

Wikipedia pageviews proxy *public interest* in a concept; Wiktionary pageviews
proxy *definition-seeking* — people looking up what an unfamiliar word means,
the purest form of the project's "desire to become familiar" hypothesis (H3).

API: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...
Free, no key, daily granularity, history since 2015-07-01, ~24h lag.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from .. import http
from .base import Collector, SeriesResult

_REST = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
_PROBE = "https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/en.wikipedia/all-access/user/daily/2024010100/2024010200"


class _WikimediaBase(Collector):
    project = "en.wikipedia"   # or "en.wiktionary"
    cfg_key = "wiki"           # which term_cfg field holds the article title
    granularity = "daily"

    def __init__(self, start: str = "2015070100", end: str | None = None) -> None:
        self.start = start
        self.end = end or dt.date.today().strftime("%Y%m%d00")

    def available(self) -> bool:
        try:
            http.get_bytes(_PROBE, timeout=12, use_cache=False)
            return True
        except Exception:
            return False

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        title = term_cfg.get(self.cfg_key)
        if not title:
            return None
        article = str(title).replace(" ", "_")
        url = (
            f"{_REST}/{self.project}/all-access/user/{article}/daily/"
            f"{self.start}/{self.end}"
        )
        try:
            data = http.get_json(url, max_age_s=24 * 3600)
        except Exception:
            return None
        items = data.get("items", [])
        if not items:
            return None
        idx = pd.to_datetime([it["timestamp"][:8] for it in items], format="%Y%m%d")
        vals = [it["views"] for it in items]
        return SeriesResult(
            term=term_cfg["term"],
            source=self.source_id,
            granularity="daily",
            series=pd.Series(vals, index=idx),
            real=True,
            provenance=f"Wikimedia Pageviews API ({self.project}, article '{title}', daily user views).",
            meta={"article": article, "project": self.project},
        )


class WikipediaPageviewsCollector(_WikimediaBase):
    source_id = "wikipedia"
    project = "en.wikipedia"
    cfg_key = "wiki"


class WiktionaryPageviewsCollector(_WikimediaBase):
    source_id = "wiktionary"
    project = "en.wiktionary"
    cfg_key = "wiktionary"
