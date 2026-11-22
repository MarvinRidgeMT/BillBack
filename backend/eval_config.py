"""Eval settings. ONE place to change how "policy doesn't mention it" is scored.

B's answer key may label "not mentioned" (no asset test / no residency rule) as null or as false.
Set NOT_STATED_ANSWER_KEY_VALUE to match B's key; the eval compares predictions through comparable_value().
"""

from __future__ import annotations

from typing import Any, Optional

# None -> answer key uses null for "not mentioned"; False -> answer key uses false. Pending B's confirmation.
NOT_STATED_ANSWER_KEY_VALUE: Optional[bool] = None


def comparable_value(predicted: Any, status: str) -> Any:
    """Map a predicted field value to the answer key's convention before comparing."""
    if status == "not_stated" and predicted is None:
        return NOT_STATED_ANSWER_KEY_VALUE
    return predicted
