"""Federal Poverty Guidelines (HHS) lookups. Plain code — the AI never does this math.

Data: data/fpl_2026.json, copied from the official HHS ASPE page (source_url + retrieved_at inside).
Alaska and Hawaii have their own rows; every other state and DC uses the 48-contiguous-states row.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

DEFAULT_TABLE_PATH = Path(__file__).resolve().parents[1] / "data" / "fpl_2026.json"
REQUIRED_ROWS = ("contiguous", "AK", "HI")
BASE_SIZES = tuple(str(n) for n in range(1, 9))
_STATE_RE = re.compile(r"^[A-Za-z]{2}$")


def load_table(path: Path = DEFAULT_TABLE_PATH) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    tables = data.get("tables", {})
    for row in REQUIRED_ROWS:
        entry = tables.get(row)
        if not entry or any(size not in entry.get("base", {}) for size in BASE_SIZES):
            raise ValueError(f"FPL table {path} is missing household sizes 1-8 for '{row}'")
        if not isinstance(entry.get("additional_person"), (int, float)):
            raise ValueError(f"FPL table {path} is missing additional_person for '{row}'")
    return data


@lru_cache(maxsize=1)
def _default_table() -> dict[str, Any]:
    if not DEFAULT_TABLE_PATH.exists():
        raise FileNotFoundError(f"{DEFAULT_TABLE_PATH} not found; add the official HHS 2026 table")
    return load_table(DEFAULT_TABLE_PATH)


def _row_key(state: str) -> str:
    if not isinstance(state, str) or not _STATE_RE.match(state.strip()):
        raise ValueError(f"state must be a two-letter code like 'OH', got {state!r}")
    code = state.strip().upper()
    return code if code in ("AK", "HI") else "contiguous"


def _check_household(household_size: Any) -> int:
    if isinstance(household_size, bool) or not isinstance(household_size, int) or household_size < 1:
        raise ValueError(f"household_size must be a whole number of at least 1, got {household_size!r}")
    return household_size


def poverty_line(household_size: int, state: str, table: Optional[dict[str, Any]] = None) -> int:
    """Annual poverty guideline in dollars for this household size and state."""
    size = _check_household(household_size)
    row = (table or _default_table())["tables"][_row_key(state)]
    if size <= 8:
        return int(row["base"][str(size)])
    return int(row["base"]["8"] + (size - 8) * row["additional_person"])


def percent_of_fpl(
    annual_income: float, household_size: int, state: str, table: Optional[dict[str, Any]] = None
) -> float:
    """Household income as a percent of the poverty guideline (200.0 means exactly 200%). Not rounded."""
    if isinstance(annual_income, bool) or not isinstance(annual_income, (int, float)) or annual_income < 0:
        raise ValueError(f"annual_income must be a number of at least 0, got {annual_income!r}")
    return annual_income * 100 / poverty_line(household_size, state, table)
