"""Read the committed public Schedule H cross-check dataset."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "schedule_h.json"


@lru_cache(maxsize=1)
def _records() -> dict[str, dict[str, Any]]:
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("Schedule H data must contain a records list")
    return {
        record["hospital_slug"]: record
        for record in records
        if isinstance(record, dict) and isinstance(record.get("hospital_slug"), str)
    }


def for_hospital(slug: str) -> dict[str, Any] | None:
    """Return a public filing cross-check or None when no conservative match exists."""
    return _records().get(slug)
