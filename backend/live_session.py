"""Live-mode policies, kept in this server process's memory only: never written to disk, gone on restart.

Keyed by slug "live-<sha16>" (read from a link or upload) or "live-manual-<hash16>" (limits typed in by the patient).
Entries expire after TTL_SECONDS and the store holds at most MAX_ENTRIES (oldest dropped first).
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Callable, Optional

from backend.policy_reader.schema import PolicyRules

TTL_SECONDS = 2 * 60 * 60
MAX_ENTRIES = 200
PREFIX = "live-"
SLUG_HEX = 16  # 64 bits of the document's sha256: crafting a colliding document is impractical

_lock = threading.Lock()
_store: "OrderedDict[str, tuple[float, PolicyRules]]" = OrderedDict()
_clock: Callable[[], float] = time.monotonic


def is_live_slug(slug: str) -> bool:
    return isinstance(slug, str) and slug.startswith(PREFIX)


def _expire(now: float) -> None:
    for slug in [s for s, (at, _) in _store.items() if now - at > TTL_SECONDS]:
        del _store[slug]


def put(slug: str, rules: PolicyRules) -> str:
    if not is_live_slug(slug):
        raise ValueError(f"live slugs start with {PREFIX!r}")
    with _lock:
        now = _clock()
        _expire(now)
        _store[slug] = (now, rules)
        _store.move_to_end(slug)
        while len(_store) > MAX_ENTRIES:
            _store.popitem(last=False)
    return slug


def get(slug: str) -> Optional[PolicyRules]:
    with _lock:
        _expire(_clock())
        hit = _store.get(slug)
        return hit[1] if hit else None


def clear() -> None:
    with _lock:
        _store.clear()


def size() -> int:
    with _lock:
        return len(_store)
