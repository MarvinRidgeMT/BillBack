"""The hospital's own financial assistance application form, appended to the packet when we have it on file.

Public forms only (data/forms/). Built in memory; nothing is written. We fill only what we know for sure
(today's date as the signature date). Names, addresses, SSNs, income by source and signatures stay blank.
"""

from __future__ import annotations

import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pypdf import PdfReader, PdfWriter

from backend.policy_reader.cache import REPO_ROOT

FORMS_DIR = REPO_ROOT / "data" / "forms"


@dataclass(frozen=True)
class HospitalForm:
    hospital: str
    path: Path
    fillable: bool
    fill: tuple[tuple[str, str], ...]


@lru_cache(maxsize=1)
def _sources() -> dict[str, Any]:
    path = FORMS_DIR / "sources.json"
    return json.loads(path.read_text())["forms"] if path.exists() else {}


def form_for(slug: str, lang: str) -> Optional[HospitalForm]:
    """The form in the patient's language (or English), if one is on file and its checksum still matches."""
    entry = _sources().get(slug)
    if not isinstance(entry, dict):
        return None
    for code in (lang, "en"):
        spec = entry.get(code)
        if not spec:
            continue
        path = FORMS_DIR / spec["file"]
        if path.parent != FORMS_DIR or not path.exists():
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            continue
        return HospitalForm(entry["hospital"], path, bool(spec.get("fillable")), tuple(spec.get("fill", {}).items()))
    return None


def _date_parts(today: date) -> dict[str, str]:
    return {"month": f"{today.month:02d}", "day": f"{today.day:02d}", "year": str(today.year)}


def filled_form(form: HospitalForm, today: Optional[date] = None) -> bytes:
    """The form with only the known fields filled. Non-fillable forms come back as published."""
    writer = PdfWriter(clone_from=PdfReader(form.path))
    if form.fillable and form.fill:
        parts = _date_parts(today or date.today())
        values = {field: parts[what] for field, what in form.fill if what in parts}
        for page in writer.pages:
            writer.update_page_form_field_values(page, values, auto_regenerate=False)
        writer.set_need_appearances_writer(True)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def append_form(packet_pdf: bytes, form: HospitalForm, today: Optional[date] = None) -> bytes:
    """Packet pages first, then the hospital's own form (its fields stay fillable)."""
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(packet_pdf)))
    writer.append(PdfReader(io.BytesIO(filled_form(form, today))))
    if form.fillable:
        writer.set_need_appearances_writer(True)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
