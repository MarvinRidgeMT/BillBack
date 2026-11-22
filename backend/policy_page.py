"""Policy "receipt": render one page of a hospital's public policy PDF and box the quoted sentence.

Plain code, no AI. Only public policy files under data/policies/ are read; nothing is written.
If the quote can't be located, found=False and no box is drawn (never a box in the wrong place).
"""

from __future__ import annotations

import base64
import hashlib
import io
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import pdfplumber
import pypdfium2 as pdfium

from backend import policies
from backend.policy_reader.cache import REPO_ROOT

POLICY_PDF_DIR = REPO_ROOT / "data" / "policies"
RENDER_SCALE = 2
BOX_PAD_PX = 3
LINE_TOLERANCE_PT = 3
FALLBACK_WORDS = 10
MAX_QUOTE_CHARS = 2000

_QUOTES = str.maketrans({"“": '"', "”": '"', "„": '"', "‘": "'", "’": "'", "­": ""})
_CHAR_CLASS = {'"': '["“”„]', "'": "['‘’]", "-": "[-‐‑–]"}


def normalize(text: str) -> str:
    """Straight quotes, no line-end hyphenation, single spaces."""
    text = text.translate(_QUOTES)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()


def _word_pattern(word: str) -> str:
    return "".join(_CHAR_CLASS.get(ch, re.escape(ch)) for ch in word)


def _words_pattern(words: list[str]) -> str:
    # \s* between words: PDF text sometimes merges words or breaks a hyphenated word across lines.
    return r"\s*".join(_word_pattern(w) for w in words)


@lru_cache(maxsize=1)
def _pdfs_by_sha() -> dict[str, Path]:
    return {hashlib.sha256(p.read_bytes()).hexdigest(): p for p in sorted(POLICY_PDF_DIR.glob("*.pdf"))}


def pdf_path_for(slug: str) -> Optional[Path]:
    """The cached policy's own PDF (matched by sha256). Raises ValueError/LookupError like load_policy."""
    rules, _ = policies.load_policy(slug)
    if rules.source is None:
        return None
    return _pdfs_by_sha().get(rules.source.sha256)


@lru_cache(maxsize=20)
def _render(path: str, page_index: int) -> tuple[str, int, int]:
    doc = pdfium.PdfDocument(path)
    try:
        bitmap = doc[page_index].render(scale=RENDER_SCALE)
        image = bitmap.to_pil()
        buf = io.BytesIO()
        image.save(buf, format="PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii"), image.width, image.height
    finally:
        doc.close()


def _line_boxes(chars: list[dict[str, Any]], width: int, height: int) -> list[dict[str, float]]:
    lines: list[dict[str, float]] = []
    for ch in sorted(chars, key=lambda c: (round(c["top"]), c["x0"])):
        if not ch.get("text", "").strip():
            continue
        for line in lines:
            if abs(line["top"] - ch["top"]) <= LINE_TOLERANCE_PT:
                line["x0"] = min(line["x0"], ch["x0"])
                line["x1"] = max(line["x1"], ch["x1"])
                line["bottom"] = max(line["bottom"], ch["bottom"])
                break
        else:
            lines.append({"x0": ch["x0"], "x1": ch["x1"], "top": ch["top"], "bottom": ch["bottom"]})
    s = RENDER_SCALE
    return [
        {
            "x0": round(max(0.0, ln["x0"] * s - BOX_PAD_PX), 1),
            "y0": round(max(0.0, ln["top"] * s - BOX_PAD_PX), 1),
            "x1": round(min(float(width), ln["x1"] * s + BOX_PAD_PX), 1),
            "y1": round(min(float(height), ln["bottom"] * s + BOX_PAD_PX), 1),
        }
        for ln in sorted(lines, key=lambda ln: ln["top"])
    ]


def _find_chars(page: Any, quote: str) -> list[dict[str, Any]]:
    words = normalize(quote).split(" ")
    if not words or not words[0]:
        return []
    patterns = [_words_pattern(words)]
    if len(words) > 2 * FALLBACK_WORDS:
        gap = len(quote) * 2
        patterns.append(
            _words_pattern(words[:FALLBACK_WORDS]) + rf"[\s\S]{{0,{gap}}}?" + _words_pattern(words[-FALLBACK_WORDS:])
        )
    for pattern in patterns:
        matches = page.search(pattern, regex=True, case=False, return_chars=True)
        if matches:
            return matches[0]["chars"]
    return []


@lru_cache(maxsize=20)
def locate(slug: str, page_number: int, quote: str) -> dict[str, Any]:
    """Page image + one box per matched line. LookupError if the slug, PDF or page doesn't exist."""
    path = pdf_path_for(slug)
    if path is None:
        raise LookupError(f"no policy PDF on file for '{slug}'")
    with pdfplumber.open(path) as pdf:
        if not 1 <= page_number <= len(pdf.pages):
            raise LookupError(f"page {page_number} is not in this policy")
        chars = _find_chars(pdf.pages[page_number - 1], quote[:MAX_QUOTE_CHARS]) if quote.strip() else []
    image, width, height = _render(str(path), page_number - 1)
    boxes = _line_boxes(chars, width, height) if chars else []
    return {"image": image, "width": width, "height": height, "boxes": boxes, "page": page_number, "found": bool(boxes)}
