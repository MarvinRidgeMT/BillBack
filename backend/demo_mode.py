"""Demo switches (env vars). Recording the video should never depend on a live API call.

DEMO_CACHE_ONLY=1  policies come only from cache/policies (no LLM call for policies); bills still read live.
BILL_CACHE_ONLY=1  bills come only from cache/bills/<sha256>.json (C's 10 fictional sample bills); no LLM at all.
LIVE_MODE=0        disable reading a policy from a URL (POST /api/policy/read with {"url": ...}).

cache/bills is written ONLY by eval/bill_extraction.py for the fictional sample bills. The API never
writes uploads to disk.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from backend.policy_reader.cache import REPO_ROOT

BILL_CACHE_DIR = REPO_ROOT / "cache" / "bills"


def _flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def demo_cache_only() -> bool:
    return _flag("DEMO_CACHE_ONLY")


def bill_cache_only() -> bool:
    return _flag("BILL_CACHE_ONLY")


def live_mode() -> bool:
    return _flag("LIVE_MODE", "1")


def cached_bill(sha256: str) -> Optional[dict[str, Any]]:
    path = BILL_CACHE_DIR / f"{sha256}.json"
    return json.loads(path.read_text()) if path.exists() else None
