# SPDX-License-Identifier: Apache-2.0
"""Data collectors. Each module exposes a collector with a uniform interface.

Add a new source by dropping a module here and registering it in ``REGISTRY``.
The pipeline probes ``available()`` at runtime and skips unreachable sources, so
the same registry works in a network-restricted sandbox, in CI, and on a laptop.
"""
from __future__ import annotations

from .base import Collector, SeriesResult
from .gdelt import GdeltCollector
from .hackernews import HackerNewsCollector
from .manual import GoogleTrendsCSVCollector, LinkedInManualCollector
from .pubmed_kobak import PubMedKobakCollector
from .wikimedia import WikipediaPageviewsCollector, WiktionaryPageviewsCollector

REGISTRY: dict[str, type[Collector]] = {
    "pubmed_kobak": PubMedKobakCollector,        # real-data anchor; works everywhere
    "wiktionary": WiktionaryPageviewsCollector,  # definition-seeking signal (H3)
    "wikipedia": WikipediaPageviewsCollector,
    "gdelt": GdeltCollector,
    "hackernews": HackerNewsCollector,
    "google_trends_csv": GoogleTrendsCSVCollector,
    "linkedin_manual": LinkedInManualCollector,
}

__all__ = [
    "Collector", "SeriesResult", "REGISTRY",
    "PubMedKobakCollector", "WikipediaPageviewsCollector", "WiktionaryPageviewsCollector",
    "GdeltCollector", "HackerNewsCollector", "GoogleTrendsCSVCollector", "LinkedInManualCollector",
]
