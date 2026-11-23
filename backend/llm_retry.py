"""Retry model calls with exponential backoff inside a total time budget.

Only transient failures are retried (rate limit, 5xx, timeout, connection). Bad requests, a rejected key or a
refusal fail at once. After the last try the caller gets a ModelUnavailable it can turn into a clean message.
"""

from __future__ import annotations

import inspect
import logging
import time
from typing import Callable

from backend.policy_reader.llm_clients import ModelClient, ModelResult, PolicyReaderError, PromptInput, TransientModelError

log = logging.getLogger(__name__)

MAX_TRIES = 3
BASE_DELAY_S = 1.0
BILL_TOTAL_TIMEOUT_S = 30.0
POLICY_TOTAL_TIMEOUT_S = 120.0  # one policy read takes 8-40 s, so 30 s would cut off good reads
MIN_TRY_S = 3.0  # don't start a try with less time than this left


class ModelUnavailable(PolicyReaderError):
    """The model couldn't be reached after retries (or the time budget ran out). Safe to show as a generic message."""


def _accepts_timeout(client: ModelClient) -> bool:
    try:
        return "timeout" in inspect.signature(client.generate).parameters
    except (TypeError, ValueError):
        return False


def generate_with_retry(
    client: ModelClient,
    prompt: PromptInput,
    *,
    total_timeout_s: float = BILL_TOTAL_TIMEOUT_S,
    tries: int = MAX_TRIES,
    base_delay_s: float = BASE_DELAY_S,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> ModelResult:
    deadline = clock() + total_timeout_s
    pass_timeout = _accepts_timeout(client)
    last: Exception | None = None
    for attempt in range(1, tries + 1):
        remaining = deadline - clock()
        if remaining < MIN_TRY_S:
            break
        try:
            if pass_timeout:
                return client.generate(prompt, timeout=remaining)  # type: ignore[call-arg]
            return client.generate(prompt)
        except TransientModelError as exc:
            last = exc
            delay = base_delay_s * 2 ** (attempt - 1)
            log.warning("model call failed (try %s/%s): %s; retrying in %.1fs", attempt, tries, exc, delay)
            if attempt == tries or deadline - clock() - delay < MIN_TRY_S:
                break
            sleep(delay)
    raise ModelUnavailable(f"model unavailable after retries: {last}") from last
