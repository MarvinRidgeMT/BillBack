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


# ---------- live-mode checks: say clearly why a document can't be read as a policy ----------

MIN_POLICY_CHARS = 800  # the shortest real policy we've seen is several pages; a page of text is ~2,000 chars


class DocumentError(ValueError):
    """The document can't be read as a policy. `code` is stable for the UI; the message is safe to show."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _check_encryption(pdf_bytes: bytes) -> None:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except (PdfReadError, ValueError, OSError) as exc:
        raise DocumentError("that PDF is damaged or empty", "pdf_empty") from exc
    if reader.is_encrypted:
        try:
            ok = reader.decrypt("")  # owner-password-only PDFs still open
        except Exception:  # pypdf raises several types for unsupported encryption
            ok = 0
        if not ok:
            raise DocumentError("that PDF is password-protected", "pdf_encrypted")


def _text_checks(text: str) -> None:
    from .fetch import looks_like_policy

    stripped = text.strip()
    if not stripped:
        raise DocumentError("that PDF has no readable text", "pdf_empty")
    if len(stripped) < MIN_POLICY_CHARS:
        raise DocumentError("that document is too short to be a financial assistance policy", "too_short")
    if not looks_like_policy(stripped):
        raise DocumentError("that document doesn't look like a financial assistance policy", "not_policy")


def _has_images(pdf_bytes: bytes) -> bool:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return any(page.images for page in pdf.pages)


def extract_checked(pdf_bytes: bytes) -> ExtractedDoc:
    """extract_pages + checks for password protection, empty/damaged files, too-short or off-topic text."""
    _check_encryption(pdf_bytes)
    try:
        doc = extract_pages(pdf_bytes)
    except Exception as exc:  # pdfplumber/pdfminer raise many types on damaged files
        raise DocumentError("that PDF is damaged or empty", "pdf_empty") from exc
    if doc.page_count == 0:
        raise DocumentError("that PDF has no pages", "pdf_empty")
    if all(not p.text.strip() for p in doc.pages) and not _has_images(pdf_bytes):
        raise DocumentError("that PDF is blank", "pdf_empty")
    if not doc.needs_raw_pdf:  # scanned pages without OCR go to the model as a PDF; we can't judge their text
        _text_checks("\n".join(p.text for p in doc.pages))
    return doc


def doc_from_text(text: str) -> ExtractedDoc:
    """A policy published as a web page: one 'page' of text."""
    _text_checks(text)
    return ExtractedDoc((PageText(1, text, "text"),), needs_raw_pdf=False, warnings=("read from a web page, not a PDF",))
