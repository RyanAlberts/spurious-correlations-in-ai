# SPDX-License-Identifier: Apache-2.0
"""PubMed excess-vocabulary collector (Kobak et al. 2025).

This is the project's anchor *real-data* source and the one source reachable from
restricted/allowlisted environments (it lives on ``raw.githubusercontent.com``).

Kobak, Gonzalez-Marquez, Horvat & Lause (2025), "Delving into LLM-assisted writing
in biomedical publications through excess vocabulary", Science Advances 11(27).
Data: https://github.com/berenslab/llm-excess-vocab

We download the 362k x 15 matrix of yearly word occurrences (number of PubMed
abstracts per year containing each word) plus a totals row, and turn any word into
a yearly *frequency* series: occurrences / total-abstracts-that-year. That series is
the measured prevalence of the word in the biomedical literature — exactly the signal
the paper uses to show that LLM-favoured words exploded after ChatGPT (Nov 2022).
"""
from __future__ import annotations

import gzip
import io

import pandas as pd

from .. import http
from ..paths import RAW_DIR
from .base import Collector, SeriesResult

_BASE = "https://raw.githubusercontent.com/berenslab/llm-excess-vocab/main/results"
URL_COUNTS = f"{_BASE}/yearly-counts.csv.gz"
URL_EXCESS = f"{_BASE}/excess_words.csv"
CITATION = "Kobak et al. 2025, Science Advances 11(27):eadt3813"


class PubMedKobakCollector(Collector):
    source_id = "pubmed_kobak"
    granularity = "yearly"

    def __init__(self) -> None:
        self._counts: pd.DataFrame | None = None   # words x years (frequency proportion)
        self._totals: pd.Series | None = None      # year -> total abstracts
        self._excess_words: set[str] | None = None

    # -- loading -----------------------------------------------------------
    def _load(self) -> None:
        if self._counts is not None:
            return
        raw = http.get_bytes(URL_COUNTS, max_age_s=7 * 24 * 3600)
        # Snapshot the raw asset for provenance / reproducibility.
        (RAW_DIR / "kobak_yearly-counts.csv.gz").write_bytes(raw)
        text = gzip.decompress(raw).decode("utf-8")
        df = pd.read_csv(io.StringIO(text), keep_default_na=False)
        df = df.rename(columns={df.columns[0]: "word"})
        year_cols = [c for c in df.columns if c != "word"]
        df[year_cols] = df[year_cols].apply(pd.to_numeric, errors="coerce")

        totals_row = df[df["word"] == ""]
        if not totals_row.empty:
            self._totals = totals_row.iloc[0][year_cols].astype(float)
            df = df[df["word"] != ""]
        else:  # fall back to column sums if the totals row is missing
            self._totals = df[year_cols].sum().astype(float)

        df = df.set_index(df["word"].str.lower()).drop(columns=["word"])
        # frequency proportion per (word, year)
        self._counts = df[year_cols].div(self._totals, axis=1)
        self._counts.columns = [int(c) for c in year_cols]
        self._totals.index = [int(c) for c in year_cols]

    def _load_excess(self) -> None:
        if self._excess_words is not None:
            return
        try:
            text = http.get_text(URL_EXCESS, max_age_s=7 * 24 * 3600)
            (RAW_DIR / "kobak_excess_words.csv").write_text(text)
            ex = pd.read_csv(io.StringIO(text))
            self._excess_words = {w.lower() for w in ex["word"].astype(str)}
        except Exception:
            self._excess_words = set()

    def available(self) -> bool:
        try:
            self._load()
            return True
        except Exception:
            return False

    # -- collection --------------------------------------------------------
    def collect(self, term_cfg: dict) -> SeriesResult | None:
        word = term_cfg.get("pubmed_word")
        if not word:
            return None
        self._load()
        self._load_excess()
        key = str(word).lower()
        if key not in self._counts.index:
            return None

        freq = self._counts.loc[key].astype(float)
        # collapse possible duplicate index rows (rare) by summing proportions
        if isinstance(freq, pd.DataFrame):
            freq = freq.sum(axis=0)
        series = pd.Series(
            freq.values,
            index=pd.to_datetime([f"{y}-01-01" for y in freq.index]),
        )

        # A real, interpretable fold-change: 2024 prevalence vs the 2019-2021 baseline.
        baseline_years = [y for y in (2019, 2020, 2021) if y in freq.index]
        base = freq[baseline_years].mean() if baseline_years else float("nan")
        fold_2024 = (freq.get(2024, float("nan")) / base) if base else float("nan")

        return SeriesResult(
            term=term_cfg["term"],
            source=self.source_id,
            granularity="yearly",
            series=series * 1_000_000,  # parts-per-million of abstracts (readable axis)
            real=True,
            provenance=(
                f"PubMed abstract frequency (parts-per-million), {CITATION}. "
                "Value = abstracts containing the word / total abstracts that year."
            ),
            meta={
                "units": "abstracts per million",
                "citation": CITATION,
                "in_excess_list": key in (self._excess_words or set()),
                "fold_change_2024_vs_2019_2021": round(float(fold_2024), 2) if fold_2024 == fold_2024 else None,
            },
        )
