# SPDX-License-Identifier: Apache-2.0
"""SQLite-backed catalog plus dated JSON snapshots.

Each weekly run records: the run, every observation (term/source/date/value), and
every correlation verdict. The SQLite DB is the queryable store; a dated JSON
snapshot is committed alongside so the *evolution* of the dictionary is visible in
git history (you can diff what the pipeline believed about "delve" week over week).
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

import pandas as pd

from ..paths import CATALOG_DB, CATALOG_DIR

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT NOT NULL,
    notes TEXT
);
CREATE TABLE IF NOT EXISTS terms (
    term TEXT PRIMARY KEY,
    cluster TEXT,
    negative_control INTEGER DEFAULT 0,
    first_seen TEXT
);
CREATE TABLE IF NOT EXISTS observations (
    term TEXT, source TEXT, date TEXT, value REAL, run_id INTEGER
);
CREATE TABLE IF NOT EXISTS correlations (
    run_id INTEGER, run_date TEXT, term TEXT, cluster TEXT, family TEXT,
    pearson_r REAL, spearman_r REAL, jump_ratio REAL, changepoint TEXT,
    gap_days INTEGER, aligned INTEGER, best_lag INTEGER, partial_r REAL,
    overrep_ratio REAL, label TEXT, score REAL, needs_review INTEGER,
    provenance TEXT
);
CREATE INDEX IF NOT EXISTS idx_obs_term ON observations(term, source);
"""


class Catalog:
    def __init__(self, db_path: Path = CATALOG_DB) -> None:
        CATALOG_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        self.run_id: int | None = None
        self.run_date = dt.date.today().isoformat()

    def start_run(self, notes: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO runs(run_date, notes) VALUES (?, ?)", (self.run_date, notes)
        )
        self.conn.commit()
        self.run_id = int(cur.lastrowid)
        return self.run_id

    def upsert_term(self, term: str, cluster: str, negative_control: bool) -> None:
        self.conn.execute(
            "INSERT INTO terms(term, cluster, negative_control, first_seen) VALUES (?,?,?,?) "
            "ON CONFLICT(term) DO UPDATE SET cluster=excluded.cluster",
            (term, cluster, int(negative_control), self.run_date),
        )
        self.conn.commit()

    def write_observations(self, term: str, source: str, series: pd.Series) -> None:
        rows = [(term, source, idx.date().isoformat(), float(v), self.run_id)
                for idx, v in series.dropna().items()]
        self.conn.executemany(
            "INSERT INTO observations(term, source, date, value, run_id) VALUES (?,?,?,?,?)", rows
        )
        self.conn.commit()

    def write_correlation(self, row: dict) -> None:
        cols = ["run_id", "run_date", "term", "cluster", "family", "pearson_r", "spearman_r",
                "jump_ratio", "changepoint", "gap_days", "aligned", "best_lag", "partial_r",
                "overrep_ratio", "label", "score", "needs_review", "provenance"]
        row = {**row, "run_id": self.run_id, "run_date": self.run_date}
        self.conn.execute(
            f"INSERT INTO correlations({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})",
            [row.get(c) for c in cols],
        )
        self.conn.commit()

    def snapshot_json(self) -> Path:
        """Write a dated snapshot of this run's correlations (committed to git)."""
        df = pd.read_sql_query(
            "SELECT * FROM correlations WHERE run_id = ?", self.conn, params=(self.run_id,)
        )
        path = CATALOG_DIR / f"catalog-{self.run_date}.json"
        payload = {
            "run_date": self.run_date,
            "run_id": self.run_id,
            "n_terms": int(df["term"].nunique()) if not df.empty else 0,
            "correlations": json.loads(df.to_json(orient="records")),
        }
        path.write_text(json.dumps(payload, indent=2))
        # Also refresh a stable "latest" pointer.
        (CATALOG_DIR / "catalog-latest.json").write_text(json.dumps(payload, indent=2))
        return path

    def correlations_df(self) -> pd.DataFrame:
        return pd.read_sql_query(
            "SELECT * FROM correlations WHERE run_id = ?", self.conn, params=(self.run_id,)
        )

    def close(self) -> None:
        self.conn.close()
