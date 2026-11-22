"""Code checks on model-extracted bill fields. A failed check caps confidence at 0.5."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from backend.policy_reader.validate import normalize

from .schema import CONFIRM_THRESHOLD, FIELD_NAMES, BillField, BillModelOutput

FAILED_CHECK_CAP = 0.5
_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9-]{4,30}$")
_AMOUNT_RE = re.compile(r"^\$?\s*(\d{1,3}(,\d{3})+|\d+)(\.\d{1,2})?$")
_DATE_FORMATS = ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%m-%d-%Y", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%b %d %Y")


def parse_cents(value: str) -> Optional[int]:
    text = value.strip().replace("USD", "").strip()
    if not _AMOUNT_RE.match(text):
        return None
    dollars = text.replace("$", "").replace(",", "").strip()
    whole, _, frac = dollars.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def parse_service_date(value: str, today: Optional[date] = None) -> Optional[str]:
    text = re.sub(r"\s+", " ", value.strip())
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt).date()
        except ValueError:
            continue
        return parsed.isoformat() if parsed <= (today or date.today()) else None
    return None


def valid_account_number(value: str) -> bool:
    return bool(_ACCOUNT_RE.match(value.strip()))


def _in_text(field: str, f: BillField, text_n: str) -> bool:
    candidates = [f.value or ""]
    if field == "amount_due" and isinstance(f.normalized, int):
        candidates += [f"{f.normalized / 100:,.2f}", f"{f.normalized / 100:.2f}"]
    if field == "service_date" and isinstance(f.normalized, str):
        d = date.fromisoformat(f.normalized)
        candidates += [f.normalized, d.strftime("%m/%d/%Y"), f"{d.month}/{d.day}/{d.year}"]
    return any(normalize(c) and normalize(c) in text_n for c in candidates)


def _check(field: str, f: BillField) -> tuple[BillField, Optional[str]]:
    """Return (field with normalized value, failure reason or None)."""
    if f.value is None:
        return f, None
    if field == "amount_due":
        cents = parse_cents(f.value)
        return f.model_copy(update={"normalized": cents}), None if cents is not None else "amount is not a dollar amount"
    if field == "service_date":
        iso = parse_service_date(f.value)
        return f.model_copy(update={"normalized": iso}), None if iso else "date is unreadable or in the future"
    if field == "account_number" and not valid_account_number(f.value):
        return f, "account number should be 4-30 letters, digits or dashes"
    return f, None


def _cap(f: BillField, reason: str) -> BillField:
    note = f"{f.note}; {reason}".strip("; ")
    return f.model_copy(update={"confidence": min(f.confidence, FAILED_CHECK_CAP), "note": note})


def validate_fields(raw: BillModelOutput, pdf_text: Optional[str]) -> dict[str, BillField]:
    text_n = normalize(pdf_text) if pdf_text else None
    out: dict[str, BillField] = {}
    for name in FIELD_NAMES:
        field, problem = _check(name, getattr(raw, name))
        if problem:
            field = _cap(field, problem)
        if text_n is not None and field.value is not None and not _in_text(name, field, text_n):
            field = _cap(field, "value not found in the PDF text")
        out[name] = field
    return out


def fields_to_confirm(fields: dict[str, BillField]) -> list[str]:
    return [n for n in FIELD_NAMES if fields[n].value is None or fields[n].confidence < CONFIRM_THRESHOLD]
