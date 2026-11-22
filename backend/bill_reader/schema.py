"""Bill fields contract. Deliberately has NO patient name, date of birth or insurance fields."""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

FIELD_NAMES = ("hospital_name", "hospital_address", "amount_due", "service_date", "account_number")
CONFIRM_THRESHOLD = 0.8


class BillField(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    note: str = ""
    # Set by code: cents (int) for amount_due, ISO date (str) for service_date.
    normalized: Optional[Union[int, str]] = None

    @field_validator("value", mode="before")
    @classmethod
    def _blank_is_none(cls, v: Any) -> Any:
        return None if isinstance(v, str) and not v.strip() else v

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, v: Any) -> Any:
        return min(max(float(v), 0.0), 1.0) if isinstance(v, (int, float)) else v


class BillModelOutput(BaseModel):
    """What the model returns. extra='ignore' drops anything else (e.g. a patient name)."""

    model_config = ConfigDict(extra="ignore")

    hospital_name: BillField
    hospital_address: BillField
    amount_due: BillField
    service_date: BillField
    account_number: BillField


_FIELD_SCHEMA = {
    "type": "object",
    "properties": {
        "value": {"type": "string", "description": 'Exactly as printed on the bill; "" if not visible.'},
        "confidence": {"type": "number", "description": "0.0-1.0"},
        "note": {"type": "string", "description": "Short reason if unsure; never include patient details."},
    },
    "required": ["value", "confidence", "note"],
    "additionalProperties": False,
}


def bill_strict_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {name: dict(_FIELD_SCHEMA) for name in FIELD_NAMES},
        "required": list(FIELD_NAMES),
        "additionalProperties": False,
    }
