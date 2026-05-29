# SPDX-License-Identifier: Apache-2.0
"""Manual-import collectors for sources without a free programmatic API.

These read user-supplied exports from ``data/manual/`` so signals that cannot be
fetched (Google Trends since pytrends was archived; LinkedIn behind auth;
OpenRouter usage behind login) can still enter the pipeline. All are
*non-critical-path*: missing files simply yield no series.

Expected layouts (see SCHEDULING.md):
  data/manual/google_trends/<term>.csv   # Google Trends "Interest over time" CSV export
  data/manual/linkedin/<term>.csv        # columns: date,value
  data/manual/openrouter/snapshot.csv    # columns: date,model,tokens
"""
from __future__ import annotations

import io

import pandas as pd

from ..paths import MANUAL_DIR
from .base import Collector, SeriesResult


def _slug(term: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in term.lower()).strip("_")


class GoogleTrendsCSVCollector(Collector):
    source_id = "google_trends_csv"
    granularity = "weekly"

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        path = MANUAL_DIR / "google_trends" / f"{_slug(term_cfg['term'])}.csv"
        if not path.exists():
            return None
        # Google Trends exports have 2 preamble lines before the header row.
        text = path.read_text()
        lines = text.splitlines()
        start = next((i for i, ln in enumerate(lines) if "," in ln and ":" not in ln.split(",")[0]), 2)
        df = pd.read_csv(io.StringIO("\n".join(lines[start:])))
        df.columns = ["date", "value", *df.columns[2:]]
        df["value"] = pd.to_numeric(df["value"].astype(str).str.replace("<1", "0"), errors="coerce")
        series = pd.Series(df["value"].values, index=pd.to_datetime(df["date"])).dropna()
        if series.empty:
            return None
        return SeriesResult(
            term=term_cfg["term"], source=self.source_id, granularity="weekly",
            series=series, real=True,
            provenance=f"Google Trends CSV export (manual), {path.name}.",
        )


class LinkedInManualCollector(Collector):
    source_id = "linkedin_manual"
    granularity = "weekly"

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        path = MANUAL_DIR / "linkedin" / f"{_slug(term_cfg['term'])}.csv"
        if not path.exists():
            return None
        df = pd.read_csv(path)
        series = pd.Series(df["value"].values, index=pd.to_datetime(df["date"])).dropna()
        if series.empty:
            return None
        return SeriesResult(
            term=term_cfg["term"], source=self.source_id, granularity="weekly",
            series=series, real=True,
            provenance=f"LinkedIn export (manual, non-critical), {path.name}.",
        )
