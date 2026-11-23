"""Policy PDF -> validated rules JSON. One model call per policy; code does all checking."""

from __future__ import annotations

import dataclasses
import logging
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from backend import pricing

from . import cache, extract_text, validate
from .llm_clients import ModelClient, ModelResult, PolicyReaderError, PromptInput, default_client
from .schema import PolicyRules, Source

__all__ = ["ModelResult", "PolicyReaderError", "ReadResult", "read_policy"]

log = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "policy_reader.md"


@dataclass(frozen=True)
class ReadResult:
    rules: PolicyRules
    cached: bool
    seconds: float
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cache_path: Optional[Path] = None
    extraction_warnings: tuple[str, ...] = field(default_factory=tuple)

    def estimated_cost_usd(self) -> Optional[float]:
        return pricing.estimate_cost_usd(self.model, self.input_tokens, self.output_tokens)


def _raw_path(cache_dir: Path, sha: str) -> Path:
    return Path(cache_dir) / "raw" / f"{sha[:8]}.raw.json"


def _finish(
    raw: PolicyRules, doc: extract_text.ExtractedDoc, sha: str, url: Optional[str], retrieved_at: Optional[str] = None
) -> PolicyRules:
    with_source = raw.model_copy(
        update={
            "source": Source(url=url, sha256=sha, retrieved_at=retrieved_at or date.today().isoformat(),
                             page_count=doc.page_count),
            "warnings": list(doc.warnings) + list(raw.warnings),
        }
    )
    return validate.post_validate(with_source, doc.page_map())


def revalidate_cached(
    pdf_bytes: bytes, *, url: Optional[str] = None, cache_dir: Path = cache.DEFAULT_CACHE_DIR
) -> Optional[PolicyRules]:
    """Re-run code validation on the saved raw model output (no API call). None if no raw output saved."""
    sha = cache.sha256_bytes(pdf_bytes)
    raw_file = _raw_path(cache_dir, sha)
    if not raw_file.exists():
        return None
    previous = cache.lookup(sha, cache_dir)
    url = url or (previous.source.url if previous and previous.source else None)
    retrieved = previous.source.retrieved_at if previous and previous.source else None  # keep the download date
    raw = PolicyRules.model_validate_json(raw_file.read_text())
    rules = _finish(raw, extract_text.extract_pages(pdf_bytes), sha, url, retrieved_at=retrieved)
    cache.save(rules, cache_dir)
    return rules


def _generate(client: ModelClient, prompt: PromptInput) -> ModelResult:
    from backend.llm_retry import POLICY_TOTAL_TIMEOUT_S, generate_with_retry

    return generate_with_retry(client, prompt, total_timeout_s=POLICY_TOTAL_TIMEOUT_S)


def _parse_with_retry(client: ModelClient, prompt: PromptInput) -> tuple[PolicyRules, ModelResult, int, int]:
    result = _generate(client, prompt)
    tokens_in, tokens_out = result.input_tokens, result.output_tokens
    try:
        return PolicyRules.model_validate_json(result.text), result, tokens_in, tokens_out
    except ValidationError as exc:
        log.warning("model output failed validation, retrying once: %s", exc.errors()[:3])
        retry = dataclasses.replace(
            prompt,
            correction=f"Your previous answer was not valid for the schema. Error:\n{exc}\nReturn the corrected JSON only.",
        )
    result = _generate(client, retry)
    tokens_in += result.input_tokens
    tokens_out += result.output_tokens
    try:
        return PolicyRules.model_validate_json(result.text), result, tokens_in, tokens_out
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
    prompt = PromptInput(
        instructions=PROMPT_PATH.read_text(),
        policy_text=extract_text.to_prompt_text(doc),
        pdf_bytes=pdf_bytes if doc.needs_raw_pdf else None,
    )
    raw, last, tokens_in, tokens_out = _parse_with_retry(client or default_client(), prompt)
    raw_file = _raw_path(cache_dir, sha)
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    raw_file.write_text(raw.model_dump_json(indent=2) + "\n")  # model output before code checks

    rules = _finish(raw, doc, sha, url)
    path = cache.save(rules, cache_dir)
    return ReadResult(
        rules=rules,
        cached=False,
        seconds=time.perf_counter() - start,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        model=last.model,
        cache_path=path,
        extraction_warnings=doc.warnings,
    )
