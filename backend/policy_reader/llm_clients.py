"""Model clients. Each turns a PromptInput into JSON text matching the rules schema.

LLM_PROVIDER=anthropic (default) or gemini. The AI only extracts; code decides eligibility.
"""

from __future__ import annotations

import base64
import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Protocol

from .schema import llm_json_schema, strict_json_schema

log = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
RETRY_BACKOFF_SECONDS = 4.0
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-5-5"
DEFAULT_ANTHROPIC_EFFORT = "medium"
ANTHROPIC_MAX_TOKENS = 16000
ANTHROPIC_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class PolicyReaderError(RuntimeError):
    """The model call failed or its output could not be turned into valid rules JSON."""


@dataclass(frozen=True)
class PromptInput:
    instructions: str
    policy_text: str
    pdf_bytes: Optional[bytes] = None  # attached only when some pages have no text layer
    correction: Optional[str] = None  # set on the one retry after a validation error


@dataclass(frozen=True)
class ModelResult:
    text: str
    input_tokens: int
    output_tokens: int
    seconds: float
    model: str = ""


class ModelClient(Protocol):
    def generate(self, prompt: PromptInput) -> ModelResult: ...


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv()


class AnthropicClient:
    """Claude via structured outputs. Thinking stays adaptive (Sonnet 5.5 rejects sampling params)."""

    def __init__(self, model: Optional[str] = None, effort: Optional[str] = None):
        import anthropic

        _load_env()
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise PolicyReaderError("ANTHROPIC_API_KEY is not set (put it in .env)")
        self.model = model or os.getenv("ANTHROPIC_MODEL") or DEFAULT_ANTHROPIC_MODEL
        self.effort = effort or os.getenv("ANTHROPIC_EFFORT") or DEFAULT_ANTHROPIC_EFFORT
        # SDK retries 408/409/429/5xx and connection errors on its own.
        self._client = anthropic.Anthropic(max_retries=2, timeout=180.0)
        self._schema = strict_json_schema()

    def _content(self, prompt: PromptInput) -> list[dict]:
        blocks: list[dict] = []
        if prompt.pdf_bytes:
            blocks.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(prompt.pdf_bytes).decode("ascii"),
                    },
                }
            )
        blocks.append({"type": "text", "text": prompt.policy_text})
        if prompt.correction:
            blocks.append({"type": "text", "text": prompt.correction})
        return blocks

    def generate(self, prompt: PromptInput) -> ModelResult:
        import anthropic

        start = time.perf_counter()
        try:
            resp = self._client.beta.messages.create(
                model=self.model,
                max_tokens=ANTHROPIC_MAX_TOKENS,
                betas=[ANTHROPIC_FALLBACK_BETA],
                fallbacks="default",
                system=prompt.instructions,
                messages=[{"role": "user", "content": self._content(prompt)}],
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": self._schema}},
            )
        except anthropic.AuthenticationError as exc:
            raise PolicyReaderError("Anthropic rejected the API key (check ANTHROPIC_API_KEY)") from exc
        except anthropic.BadRequestError as exc:
            raise PolicyReaderError(f"Anthropic bad request: {exc.message}") from exc
        except anthropic.RateLimitError as exc:
            raise PolicyReaderError("Anthropic rate limit hit after retries; try again shortly") from exc
        except anthropic.APIStatusError as exc:
            raise PolicyReaderError(f"Anthropic API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise PolicyReaderError("could not reach the Anthropic API") from exc

        if resp.stop_reason == "refusal":
            raise PolicyReaderError("model declined this document (refusal)")
        if resp.stop_reason == "max_tokens":
            raise PolicyReaderError("model output was cut off (max_tokens)")
        text = next((b.text for b in resp.content if b.type == "text"), "")
        usage = resp.usage
        return ModelResult(
            text=text,
            input_tokens=(usage.input_tokens or 0) + (getattr(usage, "cache_read_input_tokens", 0) or 0),
            output_tokens=usage.output_tokens or 0,
            seconds=time.perf_counter() - start,
            model=resp.model,
        )


class GeminiClient:
    """Gemini via google-genai structured output (kept as an alternative provider)."""

    def __init__(self, model: Optional[str] = None):
        from google import genai

        _load_env()
        api_key = os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL")
        if not api_key:
            raise PolicyReaderError("GEMINI_API_KEY is not set (put it in .env)")
        if not self.model:
            raise PolicyReaderError("GEMINI_MODEL is not set (see .env.example)")
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: PromptInput) -> ModelResult:
        from google.genai import errors, types

        parts: list = [prompt.instructions]
        if prompt.pdf_bytes:
            parts.append(types.Part.from_bytes(data=prompt.pdf_bytes, mime_type="application/pdf"))
        parts.append(prompt.policy_text)
        if prompt.correction:
            parts.append(prompt.correction)
        config = types.GenerateContentConfig(
            temperature=0, response_mime_type="application/json", response_json_schema=llm_json_schema()
        )
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
            out_tokens = ((usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)) if usage else 0
            return ModelResult(
                text=resp.text or "",
                input_tokens=(usage.prompt_token_count or 0) if usage else 0,
                output_tokens=out_tokens,
                seconds=time.perf_counter() - start,
                model=self.model,
            )
        raise PolicyReaderError("Gemini call failed after retry")


def default_client() -> ModelClient:
    _load_env()
    provider = (os.getenv("LLM_PROVIDER") or "anthropic").lower()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "gemini":
        return GeminiClient()
    raise PolicyReaderError(f"unknown LLM_PROVIDER={provider!r} (use anthropic or gemini)")
