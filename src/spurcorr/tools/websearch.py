# SPDX-License-Identifier: Apache-2.0
"""Discovery tools for finding new candidate AI-vocabulary terms.

Two capabilities:

1. ``discover_candidates`` — mine the Kobak excess-vocabulary list (real, reachable
   data) for single words we are not yet tracking, ranked toward *style* words
   (the non-obvious AI tells the project cares about). This is the dependable,
   offline-capable discovery path used by the weekly run.

2. ``web_search`` — a thin, pluggable web-search interface. The backend is injected
   (e.g. a SerpAPI key, or an agent's own search tool) so the project stays
   provider-agnostic and free by default; with no backend configured it returns an
   empty result rather than failing the pipeline.
"""
from __future__ import annotations

import io
from collections.abc import Callable

import pandas as pd

from .. import http

_EXCESS_URL = "https://raw.githubusercontent.com/berenslab/llm-excess-vocab/main/results/excess_words.csv"

# Optional injected search backend: fn(query, max_results) -> list[dict].
_SEARCH_BACKEND: Callable[[str, int], list[dict]] | None = None


def set_search_backend(fn: Callable[[str, int], list[dict]]) -> None:
    """Register a web-search backend (e.g. SerpAPI). Keeps the core free/agnostic."""
    global _SEARCH_BACKEND
    _SEARCH_BACKEND = fn


def web_search(query: str, max_results: int = 10) -> list[dict]:
    """Run a web search via the configured backend, or return [] if none is set."""
    if _SEARCH_BACKEND is None:
        return []
    return _SEARCH_BACKEND(query, max_results)


def discover_candidates(already_tracked: set[str], limit: int = 25,
                        prefer_style: bool = True) -> pd.DataFrame:
    """Propose new single-word candidates from the Kobak excess-vocabulary list.

    Returns a DataFrame (word, type, part_of_speech, comment) of words not already
    tracked. With ``prefer_style`` the boring/obvious content words are de-prioritised
    in favour of *style* words — the subtle tells the project wants to surface.
    """
    text = http.get_text(_EXCESS_URL, max_age_s=7 * 24 * 3600)
    df = pd.read_csv(io.StringIO(text))
    df["word_l"] = df["word"].astype(str).str.lower()
    df = df[~df["word_l"].isin({w.lower() for w in already_tracked})]
    if prefer_style and "type" in df.columns:
        df["_rank"] = (df["type"] == "style").astype(int)
        df = df.sort_values("_rank", ascending=False)
    return df.drop(columns=[c for c in ("word_l", "_rank") if c in df.columns]).head(limit).reset_index(drop=True)
