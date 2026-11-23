"""Photo/PDF EOB -> structured claims. In memory only; never written to disk."""

from __future__ import annotations

import dataclasses
import io
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber
from pydantic import ValidationError

from backend.bill_reader import image_prep
from backend.bill_reader.validate import parse_cents, parse_service_date
from backend.policy_reader.llm_clients import ModelClient, ModelResult, PolicyReaderError, PromptInput, default_client

from .schema import CONFIRM_THRESHOLD, EobDocument, EobField, eob_strict_schema

log = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "eob_reader.md"
MAX_EOB_BYTES = 15 * 1024 * 1024
TEXT_PDF_MIN_CHARS = 50
IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/heic", "image/heif", "image/webp"}
MONEY_FIELDS = {
    "billed_amount",
    "allowed_amount",
    "plan_paid",
    "patient_responsibility",
    "deductible",
    "copay",
    "coinsurance",
}


class EobReadError(ValueError):
    """The upload cannot be read as an insurance statement. Safe to show users."""


@dataclass(frozen=True)
class EobResult:
    document: EobDocument
    fields_to_confirm: list[str]
    seconds: float
    model: str
    input_tokens: int = 0
    output_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document.model_dump(mode="json"),
            "fields_to_confirm": self.fields_to_confirm,
            "seconds": round(self.seconds, 2),
            "model": self.model,
        }


def _pdf_text(data: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join((page.extract_text() or "") for page in pdf.pages[:8])
    except Exception as exc:
        raise EobReadError("could not open that insurance statement PDF") from exc


def _build_prompt(data: bytes, content_type: str) -> tuple[PromptInput, str | None]:
    schema = eob_strict_schema()
    base = PromptInput(
        instructions=PROMPT_PATH.read_text(),
        policy_text="",
        strict_schema=schema,
        loose_schema=schema,
    )
    if data.startswith(b"%PDF"):
        text = _pdf_text(data)
        if len(text.strip()) >= TEXT_PDF_MIN_CHARS:
            return dataclasses.replace(base, policy_text=f"=== INSURANCE STATEMENT TEXT ===\n{text}"), text
        return dataclasses.replace(base, pdf_bytes=data), None
    if content_type.lower() not in IMAGE_TYPES:
        raise EobReadError("upload a photo or PDF of the insurance statement")
    try:
        image = image_prep.prepare_image(data)
    except image_prep.ImageError as exc:
        raise EobReadError(str(exc)) from exc
    return dataclasses.replace(base, images=(image,)), None


def _describe_invalid(exc: ValidationError | json.JSONDecodeError) -> str:
    if isinstance(exc, json.JSONDecodeError):
        return f"not valid JSON ({exc.msg} at char {exc.pos})"
    return "; ".join(f"{'.'.join(str(x) for x in err['loc'])}: {err['type']}" for err in exc.errors())


def _with_validation(field: EobField, name: str, pdf_text: str | None) -> EobField:
    value = field.value.strip()
    note = field.note.strip()
    confidence = field.confidence
    normalized: int | str | None = None
    if not value:
        confidence = min(confidence, 0.5)
        note = note or "not found on the insurance statement"
    elif name in MONEY_FIELDS:
        normalized = parse_cents(value)
        if normalized is None:
            confidence = min(confidence, 0.5)
            note = note or "amount could not be checked"
    elif name == "service_date":
        normalized = parse_service_date(value)
        if normalized is None:
            confidence = min(confidence, 0.5)
            note = note or "date could not be checked"
    if value and not field.location.strip():
        confidence = min(confidence, 0.5)
        note = note or "source location is missing"
    if value and pdf_text and value.casefold() not in pdf_text.casefold():
        # Do not reject formatting-normalized values; hand them to the user instead.
        confidence = min(confidence, 0.79)
        note = note or "value was not found exactly in the extracted text"
    return field.model_copy(update={"value": value, "confidence": confidence, "note": note, "normalized": normalized})


def validate_document(raw: EobDocument, pdf_text: str | None) -> tuple[EobDocument, list[str]]:
    plan = _with_validation(raw.plan_name, "plan_name", pdf_text)
    claims = []
    confirm: list[str] = []
    if plan.confidence < CONFIRM_THRESHOLD:
        confirm.append("plan_name")
    for index, claim in enumerate(raw.claims):
        updates: dict[str, Any] = {}
        for name in MONEY_FIELDS | {"service_date", "provider"}:
            field = _with_validation(getattr(claim, name), name, pdf_text)
            updates[name] = field
            if field.confidence < CONFIRM_THRESHOLD:
                confirm.append(f"claims.{index}.{name}")
        status_confidence = claim.status_confidence
        if not claim.status_location.strip():
            status_confidence = min(status_confidence, 0.5)
        if status_confidence < CONFIRM_THRESHOLD:
            confirm.append(f"claims.{index}.status")
        remarks = []
        for remark_index, remark in enumerate(claim.remark_codes):
            confidence = remark.confidence
            if not remark.location.strip() or (not remark.code.strip() and not remark.text.strip()):
                confidence = min(confidence, 0.5)
            if confidence < CONFIRM_THRESHOLD:
                confirm.append(f"claims.{index}.remark_codes.{remark_index}")
            remarks.append(remark.model_copy(update={"confidence": confidence}))
        claims.append(claim.model_copy(update={**updates, "status_confidence": status_confidence, "remark_codes": remarks}))
    return EobDocument(plan_name=plan, claims=claims), confirm


def read_eob(data: bytes, content_type: str, *, client: ModelClient | None = None) -> EobResult:
    if not data:
        raise EobReadError("the file is empty")
    if len(data) > MAX_EOB_BYTES:
        raise EobReadError("file is larger than 15 MB")
    start = time.perf_counter()
    prompt, pdf_text = _build_prompt(data, content_type)
    client = client or default_client()
    result: ModelResult = client.generate(prompt)
    input_tokens, output_tokens = result.input_tokens, result.output_tokens
    try:
        raw = EobDocument.model_validate_json(result.text)
    except (ValidationError, json.JSONDecodeError) as exc:
        log.warning("EOB output invalid, retrying once: %s", _describe_invalid(exc))
        result = client.generate(dataclasses.replace(prompt, correction="The JSON did not match the schema. Return corrected JSON only."))
        input_tokens += result.input_tokens
        output_tokens += result.output_tokens
        try:
            raw = EobDocument.model_validate_json(result.text)
        except (ValidationError, json.JSONDecodeError) as exc2:
            raise PolicyReaderError(f"model output for the insurance statement was invalid after retry: {_describe_invalid(exc2)}") from None
    document, confirm = validate_document(raw, pdf_text)
    return EobResult(
        document=document,
        fields_to_confirm=confirm,
        seconds=time.perf_counter() - start,
        model=result.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

