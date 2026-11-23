"""Baseline bill reader: Tesseract OCR + regex/heuristics, no AI. Method B in eval/bench_bill_reader.py.

Built to be a fair baseline, not a straw man:
- text PDFs use their text layer (as the AI reader does); photos are OCR'd after EXIF rotation, grayscale,
  autocontrast and upscaling small images, and we try two Tesseract page-segmentation modes and keep the
  read that finds more fields
- each field uses label-anchored rules ("Amount due", "Date of service", "Account number") with sensible
  fallbacks (largest dollar amount, first plausible date, first ID-looking token), the same cues a person uses

Needs the `tesseract` binary (brew install tesseract; for scanned PDFs also poppler). Returns the same five
fields as the AI reader: {field: {"value": str|None}}.
"""

from __future__ import annotations

import io
import re
import shutil
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageOps

FIELDS = ("hospital_name", "hospital_address", "amount_due", "service_date", "account_number")
MIN_OCR_WIDTH = 2000
PSM_MODES = (3, 6)  # 3 = automatic layout, 6 = one uniform block of text

_MONEY = re.compile(r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})|\$\s?\d+(?:\.\d{2})")
_DATE = re.compile(
    r"\b(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",
    re.IGNORECASE,
)
_ADDRESS = re.compile(r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+,\s*[A-Za-z .'-]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b")
_ACCOUNT_TOKEN = re.compile(r"\b([A-Z]{1,5}[- ]?\d[\d-]{3,}\d|\d{6,})\b")
_HOSPITAL_WORDS = re.compile(r"hospital|health|medical|clinic|center|centre|healthcare", re.IGNORECASE)
_TITLE_SUFFIX = re.compile(r"\s*(patient\s*)?(statement|invoice|bill)\b.*$", re.IGNORECASE)
_SKIP_HEADER = re.compile(r"statement|invoice|patient|page \d|bill to|remit|sample", re.IGNORECASE)
AMOUNT_LABELS = ("amount due", "balance due", "total due", "please pay", "amount owed", "patient balance", "you owe")
DATE_LABELS = ("date of service", "service date", "dates of service", "date(s) of service", "dos")
ACCOUNT_LABELS = ("account number", "account no", "account #", "acct", "account")


class OcrUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class OcrRead:
    fields: dict[str, Optional[str]]
    text: str
    method: str  # "pdf_text" | "ocr"


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _prep(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)
    if img.width < MIN_OCR_WIDTH:
        scale = MIN_OCR_WIDTH / img.width
        img = img.resize((MIN_OCR_WIDTH, int(img.height * scale)), Image.LANCZOS)
    return img


def _ocr_images(images: list[Image.Image], psm: int) -> str:
    import pytesseract

    return "\n".join(pytesseract.image_to_string(_prep(i), config=f"--psm {psm}") for i in images)


def _pdf_text(data: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages[:5])


def _images_for(data: bytes) -> list[Image.Image]:
    if data.startswith(b"%PDF"):
        from pdf2image import convert_from_bytes

        return convert_from_bytes(data, dpi=300, first_page=1, last_page=3)
    return [Image.open(io.BytesIO(data))]


def _lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines() if ln.strip()]


def _after_label(lines: list[str], labels: tuple[str, ...], pattern: re.Pattern, lookahead: int = 2) -> Optional[str]:
    """First `pattern` match on a line containing a label (after the label), or on the next `lookahead` lines."""
    for i, line in enumerate(lines):
        low = line.lower()
        for label in labels:
            pos = low.find(label)
            if pos < 0:
                continue
            same = pattern.search(line[pos + len(label):])
            if same:
                return same.group(0)
            for nxt in lines[i + 1 : i + 1 + lookahead]:
                found = pattern.search(nxt)
                if found:
                    return found.group(0)
    return None


def _money_value(text: str) -> float:
    return float(text.replace("$", "").replace(",", "").strip())


def find_amount(lines: list[str]) -> Optional[str]:
    labeled = _after_label(lines, AMOUNT_LABELS, _MONEY)
    if labeled:
        return labeled.replace(" ", "")
    amounts = [m.group(0).replace(" ", "") for ln in lines for m in _MONEY.finditer(ln)]
    return max(amounts, key=_money_value) if amounts else None


def find_service_date(lines: list[str]) -> Optional[str]:
    labeled = _after_label(lines, DATE_LABELS, _DATE)
    if labeled:
        return labeled
    for line in lines:
        if "statement" in line.lower() or "due" in line.lower():
            continue
        found = _DATE.search(line)
        if found:
            return found.group(0)
    return None


def find_account(lines: list[str]) -> Optional[str]:
    labeled = _after_label(lines, ACCOUNT_LABELS, _ACCOUNT_TOKEN)
    if labeled:
        return labeled
    for line in lines:
        found = _ACCOUNT_TOKEN.search(line)
        if found and not _DATE.search(found.group(0)):
            return found.group(0)
    return None


def find_address(lines: list[str]) -> Optional[str]:
    for line in lines[:15]:
        found = _ADDRESS.search(line)
        if found:
            return found.group(0)
    return None


def find_hospital(lines: list[str]) -> Optional[str]:
    """A hospital-sounding line near the top; else the first header line that isn't a label."""
    top = lines[:10]
    for line in top:
        # Header lines often run into a right-aligned title: "BOYS TOWN ... HOSPITALPATIENT STATEMENT".
        name = _TITLE_SUFFIX.sub("", line).strip()
        if (_HOSPITAL_WORDS.search(name) and not _SKIP_HEADER.search(name) and not _ADDRESS.search(name)
                and not _MONEY.search(name)):
            return name
    for line in top:
        if not _SKIP_HEADER.search(line) and not _DATE.search(line) and not _MONEY.search(line) and len(line) > 3:
            return line
    return None


def extract_fields(text: str) -> dict[str, Optional[str]]:
    lines = _lines(text)
    return {
        "hospital_name": find_hospital(lines),
        "hospital_address": find_address(lines),
        "amount_due": find_amount(lines),
        "service_date": find_service_date(lines),
        "account_number": find_account(lines),
    }


def _found(fields: dict[str, Optional[str]]) -> int:
    return sum(v is not None for v in fields.values())


def read_bill(data: bytes) -> OcrRead:
    """OCR + heuristics on one bill (photo or PDF)."""
    if data.startswith(b"%PDF"):
        text = _pdf_text(data)
        if len(text.strip()) >= 50:
            return OcrRead(extract_fields(text), text, "pdf_text")
    if not tesseract_available():
        raise OcrUnavailable("tesseract is not installed (brew install tesseract)")
    images = _images_for(data)
    best: Optional[OcrRead] = None
    for psm in PSM_MODES:
        text = _ocr_images(images, psm)
        read = OcrRead(extract_fields(text), text, "ocr")
        if best is None or _found(read.fields) > _found(best.fields):
            best = read
    assert best is not None
    return best
