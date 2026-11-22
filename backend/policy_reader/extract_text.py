"""PDF -> page-numbered text. Tables become pipe rows. Scanned pages go to OCR."""

from __future__ import annotations

import io
import logging
import shutil
from dataclasses import dataclass
from typing import Literal

import pdfplumber

log = logging.getLogger(__name__)

SCANNED_PAGE_MAX_CHARS = 50
OCR_DPI = 300
MIN_USEFUL_OCR_CHARS = 50
RAW_PDF_WARNING = "sent as raw PDF: some pages had no text layer and OCR was unavailable or unreadable"


@dataclass(frozen=True)
class PageText:
    number: int
    text: str
    method: Literal["text", "ocr", "none"]


@dataclass(frozen=True)
class ExtractedDoc:
    pages: tuple[PageText, ...]
    needs_raw_pdf: bool
    warnings: tuple[str, ...]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def page_map(self) -> dict[int, str]:
        return {p.number: p.text for p in self.pages}


def ocr_available() -> bool:
    return shutil.which("tesseract") is not None and shutil.which("pdftoppm") is not None


def ocr_page(pdf_bytes: bytes, page_number: int) -> str:
    from pdf2image import convert_from_bytes
    import pytesseract

    images = convert_from_bytes(pdf_bytes, dpi=OCR_DPI, first_page=page_number, last_page=page_number)
    return "\n".join(pytesseract.image_to_string(img) for img in images)


def _tables_as_text(page: pdfplumber.page.Page) -> str:
    rows = []
    for table in page.extract_tables() or []:
        for row in table:
            cells = [(c or "").replace("\n", " ").strip() for c in row]
            if any(cells):
                rows.append("| " + " | ".join(cells) + " |")
        rows.append("")
    return "\n".join(rows).strip()


def _page_text(page: pdfplumber.page.Page) -> str:
    text = (page.extract_text() or "").strip()
    tables = _tables_as_text(page)
    return f"{text}\n\n[TABLES]\n{tables}" if tables else text


def _ocr_or_none(pdf_bytes: bytes, number: int) -> PageText:
    if not ocr_available():
        return PageText(number, "", "none")
    try:
        text = ocr_page(pdf_bytes, number).strip()
    except Exception as exc:  # OCR is best-effort; raw-PDF fallback covers failures
        log.warning("OCR failed on page %s: %s", number, exc)
        return PageText(number, "", "none")
    if len(text) < MIN_USEFUL_OCR_CHARS:
        return PageText(number, text, "none")
    return PageText(number, text, "ocr")


def extract_pages(pdf_bytes: bytes) -> ExtractedDoc:
    pages: list[PageText] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = _page_text(page)
            if len(text) >= SCANNED_PAGE_MAX_CHARS:
                pages.append(PageText(number, text, "text"))
            else:
                pages.append(_ocr_or_none(pdf_bytes, number))

    needs_raw = any(p.method == "none" for p in pages)
    warnings = (RAW_PDF_WARNING,) if needs_raw else ()
    if any(p.method == "ocr" for p in pages):
        warnings = warnings + ("some pages were read with OCR; quotes on them may not match exactly",)
    return ExtractedDoc(tuple(pages), needs_raw, warnings)


def to_prompt_text(doc: ExtractedDoc) -> str:
    blocks = []
    for p in doc.pages:
        body = p.text if p.text else "[no text layer on this page — read it from the attached PDF]"
        blocks.append(f"=== PAGE {p.number} ===\n{body}")
    return "\n\n".join(blocks)
