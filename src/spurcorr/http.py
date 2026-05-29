# SPDX-License-Identifier: Apache-2.0
"""A small, polite, on-disk-cached HTTP client.

Design goals:
- One place that sets a contact User-Agent (Wikimedia/GDELT etiquette).
- Transparent on-disk caching so the weekly pipeline is cheap and reproducible,
  and so a network outage (or an allowlisted sandbox) degrades gracefully.
- Exponential backoff on transient failures.

This is deliberately dependency-light (``requests`` only) — see CONTRIBUTING.md
for why we avoid heavier frameworks.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests

from .paths import CACHE_DIR, USER_AGENT


class FetchError(RuntimeError):
    """Raised when a URL cannot be retrieved (after retries) and no cache exists."""


def _cache_path(url: str, params: dict | None, suffix: str) -> Path:
    key = url + "?" + json.dumps(params or {}, sort_keys=True)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{digest}{suffix}"


def get_bytes(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    timeout: int = 30,
    retries: int = 4,
    use_cache: bool = True,
    max_age_s: float | None = None,
) -> bytes:
    """Fetch ``url`` and return the raw body.

    Falls back to a cached copy on network failure. ``max_age_s`` lets callers
    treat a fresh-enough cache entry as authoritative without hitting the network.
    """
    cache = _cache_path(url, params, ".bin")

    if use_cache and cache.exists():
        if max_age_s is not None and (time.time() - cache.stat().st_mtime) < max_age_s:
            return cache.read_bytes()

    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)

    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, headers=hdrs, timeout=timeout)
            resp.raise_for_status()
            if use_cache:
                cache.write_bytes(resp.content)
            return resp.content
        except Exception as exc:  # noqa: BLE001 - we want to retry on anything transient
            last_err = exc
            time.sleep(2 ** attempt)

    if use_cache and cache.exists():
        # Network is down/blocked but we have a previous good copy: use it.
        return cache.read_bytes()
    raise FetchError(f"could not fetch {url}: {last_err}")


def get_text(url: str, **kwargs: Any) -> str:
    return get_bytes(url, **kwargs).decode("utf-8", errors="replace")


def get_json(url: str, **kwargs: Any) -> Any:
    return json.loads(get_bytes(url, **kwargs))
