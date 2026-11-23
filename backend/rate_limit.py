"""A small per-client rate limit for the endpoints that cost money or memory (live policy reads).

In memory, per server process; keyed by the client IP (never stored or logged). Enough to stop one client
from filling the live-policy store or running up model costs; a real deployment would also limit at the edge.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from backend.errors import AppError

LIMITS: dict[str, tuple[int, float]] = {  # name -> (requests, per seconds)
    "policy_read": (10, 600.0),
    "policy_manual": (30, 600.0),
}
_lock = threading.Lock()
_hits: dict[tuple[str, str], deque] = defaultdict(deque)


def check(request: Request, name: str) -> None:
    limit, window = LIMITS[name]
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    with _lock:
        hits = _hits[(name, client)]
        while hits and now - hits[0] > window:
            hits.popleft()
        if len(hits) >= limit:
            raise AppError("rate_limited", "too many policy reads from here; please wait a few minutes")
        hits.append(now)


def reset() -> None:
    with _lock:
        _hits.clear()
