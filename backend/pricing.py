"""Model prices for cost estimates. The ONE place prices live; every eval and the reader import from here.

USD per 1M tokens (input, output). Source: https://platform.claude.com/docs/en/about-claude/pricing
(Claude Sonnet 5.5 $2 / $10, checked 2026-11-22). Override with PRICE_IN_PER_M / PRICE_OUT_PER_M in .env.
Estimates only: the bill shows real spend.
"""

from __future__ import annotations

import os
from typing import Optional

PRICES_USD_PER_M: dict[str, tuple[float, float]] = {
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-haiku-5-5": (0.10, 0.50),
}
PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing (checked 2026-11-22)"


def prices_for(model: str) -> Optional[tuple[float, float]]:
    env_in, env_out = os.getenv("PRICE_IN_PER_M"), os.getenv("PRICE_OUT_PER_M")
    if env_in and env_out:
        return float(env_in), float(env_out)
    for name, price in PRICES_USD_PER_M.items():
        if model == name or model.startswith(f"{name}-"):  # dated snapshot ids, e.g. claude-sonnet-5-5-20260815
            return price
    return None


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    price = prices_for(model)
    if price is None:
        return None
    return input_tokens / 1e6 * price[0] + output_tokens / 1e6 * price[1]
