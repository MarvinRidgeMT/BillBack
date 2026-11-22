"""Bill photo/PDF -> 5 fields with confidence. Everything stays in memory; nothing is written to disk."""

from __future__ import annotations

import dataclasses
import io
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pdfplumber
from pydantic import ValidationError

from backend.policy_reader.llm_clients import ModelClient, PolicyReaderError, PromptInput, default_client

from . import image_prep, validate
from .schema import BillField, BillModelOutput, bill_strict_schema

log = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "bill_reader.md"
MAX_BILL_BYTES = 15 * 1024 * 1024
TEXT_PDF_MIN_CHARS = 50
IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif", "image/webp"}


class BillReadError(ValueError):
    """The upload can't be read as a bill. Message is safe to show users."""


@dataclass(frozen=True)
class BillResult:
    fields: dict[str, BillField]
    fields_to_confirm: list[str]
    seconds: float
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": {k: v.model_dump() for k, v in self.fields.items()},
            "fields_to_confirm": self.fields_to_confirm,
            "seconds": round(self.seconds, 2),
            "model": self.model,
        }


def _pdf_text(data: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages[:5])
    except Exception as exc:  # pdfplumber raises many types on corrupt files
        raise BillReadError("could not open that PDF") from exc


def _build_prompt(data: bytes, content_type: str) -> tuple[PromptInput, Optional[str]]:
    """Return the prompt and, for text PDFs, the text used for value checks."""
    base = PromptInput(instructions=PROMPT_PATH.read_text(), policy_text="", strict_schema=bill_strict_schema(),
                       loose_schema=bill_strict_schema())
    if data.startswith(b"%PDF"):
        text = _pdf_text(data)
        if len(text.strip()) >= TEXT_PDF_MIN_CHARS:
            return dataclasses.replace(base, policy_text=f"=== BILL TEXT ===\n{text}"), text
        return dataclasses.replace(base, pdf_bytes=data), None
    if content_type.lower() not in IMAGE_TYPES:
        raise BillReadError("upload a photo (JPG/PNG/HEIC) or a PDF of the bill")
    try:
        part = image_prep.prepare_image(data)
    except image_prep.ImageError as exc:
        raise BillReadError(str(exc)) from exc
    return dataclasses.replace(base, images=(part,)), None


def _parse(text: str) -> BillModelOutput:
    return BillModelOutput.model_validate(json.loads(text))


def _describe_invalid(exc: ValidationError | json.JSONDecodeError) -> str:
    """Which fields failed and why, without the values (pydantic's own message echoes the bill's text)."""
    if isinstance(exc, json.JSONDecodeError):
        return f"not valid JSON ({exc.msg} at char {exc.pos})"
    parts = [f"{'.'.join(str(x) for x in err['loc'])}: {err['type']}" for err in exc.errors()]
    return f"{len(parts)} schema error(s): " + "; ".join(parts)


def read_bill(data: bytes, content_type: str, *, client: Optional[ModelClient] = None) -> BillResult:
    if not data:
        raise BillReadError("the file is empty")
    if len(data) > MAX_BILL_BYTES:
        raise BillReadError("file is larger than 15 MB")
    start = time.perf_counter()
    prompt, pdf_text = _build_prompt(data, content_type)
    client = client or default_client()

    result = client.generate(prompt)
    tokens_in, tokens_out = result.input_tokens, result.output_tokens
    try:
        raw = _parse(result.text)
    except (ValidationError, json.JSONDecodeError) as exc:
        log.warning("bill output invalid, retrying once: %s", _describe_invalid(exc))
        result = client.generate(dataclasses.replace(prompt, correction=f"Invalid JSON for the schema: {exc}. Return corrected JSON only."))
        tokens_in += result.input_tokens
        tokens_out += result.output_tokens
        try:
            raw = _parse(result.text)
        except (ValidationError, json.JSONDecodeError) as exc2:
            # 'from None': the chained pydantic error would put bill values into the server log's traceback.
            raise PolicyReaderError(f"model output for the bill was invalid after retry: {_describe_invalid(exc2)}") from None

    fields = validate.validate_fields(raw, pdf_text)
    return BillResult(
        fields=fields,
        fields_to_confirm=validate.fields_to_confirm(fields),
        seconds=time.perf_counter() - start,
        model=result.model,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
    )
