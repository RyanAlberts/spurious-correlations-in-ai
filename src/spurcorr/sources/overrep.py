# SPDX-License-Identifier: Apache-2.0
"""Over-representation ratios — "N times more frequent in AI than human".

Primary source: the GPTZero top-100 snapshot in ``data/gptzero_vocabulary.yaml``
(the live page 403s automated fetchers). ``collectors/gptzero.py``-style refresh is
attempted best-effort here. Academic ratios (Kobak / Liang) can augment the list.

OCR-garbled GPTZero entries are flagged (``suspect``) and carried with a suggested
correction rather than silently rewritten — they surface in VALIDATION for review.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import yaml

from .. import http
from ..paths import GPTZERO_YAML

_GPTZERO_URL = "https://gptzero.me/ai-vocabulary"
# A few browser-ish UAs for the best-effort refresh ("try harder").
_REFRESH_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class OverRep:
    """The over-representation table plus convenience lookups."""
    df: pd.DataFrame                 # columns: phrase, ratio, example, suspect, suggested, source
    snapshot_date: str
    refreshed: bool

    def ratio_for(self, term: str) -> float | None:
        """Best ratio for a term: exact phrase match, else word-contained-in-phrase."""
        t = term.lower().strip()
        exact = self.df[self.df["phrase"].str.lower() == t]
        if not exact.empty:
            return float(exact["ratio"].iloc[0])
        contains = self.df[self.df["phrase"].str.lower().str.contains(rf"\b{t}\b", regex=True)]
        if not contains.empty:
            return float(contains["ratio"].max())
        return None

    def leaderboard(self, top: int = 50) -> pd.DataFrame:
        return self.df.sort_values("ratio", ascending=False).head(top).reset_index(drop=True)

    def suspect_entries(self) -> pd.DataFrame:
        return self.df[self.df["suspect"]].copy()


def _try_refresh() -> bool:
    """Attempt to refresh the GPTZero page. Returns True if it fetched HTML.

    Parsing the live DOM is intentionally not wired up (the layout is JS-rendered);
    this just records whether the page became reachable so we know when to invest
    in a parser. The YAML snapshot remains authoritative until then.
    """
    try:
        html = http.get_text(_GPTZERO_URL, headers=_REFRESH_HEADERS, timeout=15, use_cache=False)
        return "vocabulary" in html.lower()
    except Exception:
        return False


def load_overrep(path=GPTZERO_YAML, attempt_refresh: bool = False) -> OverRep:
    raw = yaml.safe_load(open(path, encoding="utf-8"))
    rows = []
    for p in raw.get("phrases", []):
        rows.append({
            "phrase": p["phrase"],
            "ratio": float(p["ratio"]),
            "example": p.get("example", ""),
            "suspect": bool(p.get("suspect_ocr", False)),
            "suggested": p.get("suggested"),
            "source": raw.get("source", "gptzero.me/ai-vocabulary"),
        })
    df = pd.DataFrame(rows)
    refreshed = _try_refresh() if attempt_refresh else False
    return OverRep(df=df, snapshot_date=str(raw.get("snapshot_date", "")), refreshed=refreshed)
