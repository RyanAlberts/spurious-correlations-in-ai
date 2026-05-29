# SPDX-License-Identifier: Apache-2.0
"""Collector interface shared by every data source.

A collector turns a *term* (a word/phrase) into a tidy time series of "interest"
plus provenance metadata. The pipeline does not care how the series was obtained
— only that it is a ``SeriesResult``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

Granularity = Literal["daily", "weekly", "monthly", "yearly"]


@dataclass
class SeriesResult:
    """One term's time series from one source.

    Attributes:
        term: the word/phrase tracked.
        source: short collector id (e.g. ``pubmed_kobak``).
        granularity: native sampling rate of the series.
        series: pandas Series indexed by a ``DatetimeIndex``, values = interest.
        real: True if values are measured from real upstream data; False if
            synthesised/placeholder (the pipeline refuses to publish non-real series).
        provenance: human-readable description of where the numbers came from.
        meta: optional extra fields (units, citation, etc.).
    """

    term: str
    source: str
    granularity: Granularity
    series: pd.Series
    real: bool
    provenance: str
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.series.index, pd.DatetimeIndex):
            self.series.index = pd.to_datetime(self.series.index)
        self.series = self.series.sort_index()
        self.series.name = self.term


class Collector:
    """Base class. Subclasses implement :meth:`collect`."""

    #: short identifier used in the registry and in provenance strings
    source_id: str = "base"
    #: native granularity of the source
    granularity: Granularity = "daily"

    def available(self) -> bool:
        """Whether this collector can run in the current environment.

        Default True; network collectors override to probe their host so the
        pipeline can skip unreachable sources gracefully.
        """
        return True

    def collect(self, term_cfg: dict) -> SeriesResult | None:
        """Return a SeriesResult for ``term_cfg`` or ``None`` if unsupported."""
        raise NotImplementedError
