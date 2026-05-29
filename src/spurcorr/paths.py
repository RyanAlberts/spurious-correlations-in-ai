# SPDX-License-Identifier: Apache-2.0
"""Central path + constant definitions for the project.

Everything is resolved relative to the repository root so the package works
whether it is run from the repo, from a cron job, or from CI.
"""
from __future__ import annotations

import os
from pathlib import Path

# src/spurcorr/paths.py -> repo root is three parents up.
ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"             # weekly snapshots of upstream data (provenance)
CACHE_DIR = DATA_DIR / "cache"         # HTTP cache (gitignored)
CATALOG_DIR = DATA_DIR / "catalog"     # versioned dictionary (sqlite + dated snapshots)
MANUAL_DIR = DATA_DIR / "manual"       # user-supplied exports (Google Trends, LinkedIn, OpenRouter)
DOCS_DIR = ROOT / "docs"
CHARTS_DIR = DOCS_DIR / "charts"
FIXTURES_DIR = ROOT / "tests" / "fixtures"

MODEL_RELEASES_YAML = DATA_DIR / "model_releases.yaml"
GPTZERO_YAML = DATA_DIR / "gptzero_vocabulary.yaml"
VOCAB_YAML = DATA_DIR / "ai_vocabulary.yaml"

CATALOG_DB = CATALOG_DIR / "catalog.sqlite"

# Polite contact string for User-Agent headers (Wikimedia/GDELT etiquette).
CONTACT = os.environ.get("SPURCORR_CONTACT", "spurious-correlations-in-ai (github.com/ryanalberts)")
USER_AGENT = f"spurcorr/0.1 ({CONTACT})"


def ensure_dirs() -> None:
    """Create the writable runtime directories if they do not exist."""
    for d in (RAW_DIR, CACHE_DIR, CATALOG_DIR, MANUAL_DIR, CHARTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
