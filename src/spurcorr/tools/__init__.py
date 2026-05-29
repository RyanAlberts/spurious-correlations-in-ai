# SPDX-License-Identifier: Apache-2.0
"""Tools for discovering new candidate AI-vocabulary terms and sources."""
from __future__ import annotations

from .websearch import discover_candidates, web_search

__all__ = ["discover_candidates", "web_search"]
