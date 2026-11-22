"""Policy PDF -> validated rules JSON. One Gemini call per policy; code does all checking."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional, Protocol

from pydantic import ValidationError

from . import cache, extract_text, validate
from .schema import PolicyRules, Source, llm_json_schema

log = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "policy_reader.md"
RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_BACKOFF_SECONDS = 4.0


class PolicyReaderError(RuntimeError):
    """The model output could not be turned into valid rules JSON."""


@dataclass(frozen=True)
class ModelResult:
    text: str
    input_tokens: int
    output_tokens: int
    seconds: float


class ModelClient(Protocol):
    def generate(self, parts: list[Any], schema: dict[str, Any]) -> ModelResult: ...


@dataclass(frozen=True)
class ReadResult:
    rules: PolicyRules
    cached: bool
    seconds: float
    input_tokens: int = 0
    output_tokens: int = 0
    cache_path: Optional[Path] = None
    extraction_warnings: tuple[str, ...] = field(default_factory=tuple)

    def estimated_cost_usd(self) -> Optional[float]:
        price_in = os.getenv("GEMINI_PRICE_IN_PER_M")
        price_out = os.getenv("GEMINI_PRICE_OUT_PER_M")
        if not price_in or not price_out:
            return None
        return self.input_tokens / 1e6 * float(price_in) + self.output_tokens / 1e6 * float(price_out)


class GeminiClient:
    """Thin wrapper over google-genai so tests can swap in a fake."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from dotenv import load_dotenv
        from google import genai

        load_dotenv()
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL")
        if not api_key:
            raise PolicyReaderError("GEMINI_API_KEY is not set (put it in .env)")
        if not self.model:
            raise PolicyReaderError("GEMINI_MODEL is not set (see .env.example)")
        self._client = genai.Client(api_key=api_key)

    def _config(self, schema: dict[str, Any]):
        from google.genai import types

        thinking_level = os.getenv("GEMINI_THINKING_LEVEL")
        return types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=schema,
            thinking_config=types.ThinkingConfig(thinking_level=thinking_level) if thinking_level else None,
        )

    def generate(self, parts: list[Any], schema: dict[str, Any]) -> ModelResult:
        from google.genai import errors

        config = self._config(schema)
        for attempt in (1, 2):
            start = time.perf_counter()
            try:
                resp = self._client.models.generate_content(model=self.model, contents=parts, config=config)
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                if attempt == 1 and code in RETRY_STATUS_CODES:
                    log.warning("Gemini %s, retrying in %ss", code, RETRY_BACKOFF_SECONDS)
                    time.sleep(RETRY_BACKOFF_SECONDS)
                    continue
                raise PolicyReaderError(f"Gemini API error {code}: {exc}") from exc
            usage = resp.usage_metadata
            output_tokens = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0) if usage else 0
            return ModelResult(
                text=resp.text or "",
                input_tokens=(usage.prompt_token_count or 0) if usage else 0,
                output_tokens=output_tokens,
                seconds=time.perf_counter() - start,
            )
        raise PolicyReaderError("Gemini call failed after retry")


def _build_parts(doc: extract_text.ExtractedDoc, pdf_bytes: bytes) -> list[Any]:
    prompt = PROMPT_PATH.read_text()
    parts: list[Any] = [prompt]
    if doc.needs_raw_pdf:
        from google.genai import types

        parts.append(types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
    parts.append(extract_text.to_prompt_text(doc))
    return parts


def _parse_with_retry(client: ModelClient, parts: list[Any], schema: dict[str, Any]) -> tuple[PolicyRules, int, int]:
    result = client.generate(parts, schema)
    tokens_in, tokens_out = result.input_tokens, result.output_tokens
    try:
        return PolicyRules.model_validate_json(result.text), tokens_in, tokens_out
    except ValidationError as exc:
        log.warning("model output failed validation, retrying once: %s", exc.errors()[:3])
        retry_parts = parts + [
            f"Your previous answer was not valid for the schema. Error:\n{exc}\nReturn the corrected JSON only."
        ]
    result = client.generate(retry_parts, schema)
    tokens_in += result.input_tokens
    tokens_out += result.output_tokens
    try:
        return PolicyRules.model_validate_json(result.text), tokens_in, tokens_out
    except ValidationError as exc:
        raise PolicyReaderError(f"model output invalid after retry: {exc}") from exc


def read_policy(
    pdf_bytes: bytes,
    *,
    url: Optional[str] = None,
    client: Optional[ModelClient] = None,
    cache_dir: Path = cache.DEFAULT_CACHE_DIR,
    use_cache: bool = True,
) -> ReadResult:
    start = time.perf_counter()
    sha = cache.sha256_bytes(pdf_bytes)
    if use_cache:
        hit = cache.lookup(sha, cache_dir)
        if hit is not None:
            return ReadResult(rules=hit, cached=True, seconds=time.perf_counter() - start)

    doc = extract_text.extract_pages(pdf_bytes)
    client = client or GeminiClient()
    raw, tokens_in, tokens_out = _parse_with_retry(client, _build_parts(doc, pdf_bytes), llm_json_schema())

    with_source = raw.model_copy(
        update={
            "source": Source(url=url, sha256=sha, retrieved_at=date.today().isoformat(), page_count=doc.page_count),
            "warnings": list(doc.warnings) + list(raw.warnings),
        }
    )
    rules = validate.post_validate(with_source, doc.page_map())
    path = cache.save(rules, cache_dir)
    return ReadResult(
        rules=rules,
        cached=False,
        seconds=time.perf_counter() - start,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        cache_path=path,
        extraction_warnings=doc.warnings,
    )
