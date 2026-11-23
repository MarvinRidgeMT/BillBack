"""Strict EOB extraction contract. Deliberately excludes patient/member identifiers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CONFIRM_THRESHOLD = 0.8
MAX_CLAIMS = 20

ClaimStatus = Literal["paid", "denied", "pending", "unknown"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class EobField(_Model):
    value: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    location: str = Field("", max_length=300)
    note: str = Field("", max_length=500)
    # Set by plain code: cents for money and ISO date for service_date.
    normalized: int | str | None = None

    @field_validator("confidence", mode="before")
    @classmethod
    def _clamp(cls, value: Any) -> Any:
        return min(max(float(value), 0.0), 1.0) if isinstance(value, (int, float)) else value


class RemarkCode(_Model):
    code: str = Field("", max_length=40)
    text: str = Field("", max_length=1000)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    location: str = Field("", max_length=300)


class EobClaim(_Model):
    service_date: EobField
    provider: EobField
    billed_amount: EobField
    allowed_amount: EobField
    plan_paid: EobField
    patient_responsibility: EobField
    deductible: EobField
    copay: EobField
    coinsurance: EobField
    status: ClaimStatus
    status_confidence: float = Field(0.0, ge=0.0, le=1.0)
    status_location: str = Field("", max_length=300)
    remark_codes: list[RemarkCode] = Field(default_factory=list, max_length=12)


class EobDocument(_Model):
    plan_name: EobField
    claims: list[EobClaim] = Field(min_length=1, max_length=MAX_CLAIMS)


_FIELD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "value": {"type": "string", "description": 'Exactly as printed; "" if absent.'},
        "confidence": {"type": "number", "description": "0.0 to 1.0"},
        "location": {"type": "string", "description": "Page and section/table/row where this value appears."},
        "note": {"type": "string", "description": "Why uncertain; never include patient/member details."},
    },
    "required": ["value", "confidence", "location", "note"],
    "additionalProperties": False,
}

_REMARK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "text": {"type": "string"},
        "confidence": {"type": "number"},
        "location": {"type": "string"},
    },
    "required": ["code", "text", "confidence", "location"],
    "additionalProperties": False,
}


def eob_strict_schema() -> dict[str, Any]:
    claim_properties = {
        name: dict(_FIELD_SCHEMA)
        for name in (
            "service_date",
            "provider",
            "billed_amount",
            "allowed_amount",
            "plan_paid",
            "patient_responsibility",
            "deductible",
            "copay",
            "coinsurance",
        )
    }
    claim_properties.update(
        {
            "status": {"type": "string", "enum": ["paid", "denied", "pending", "unknown"]},
            "status_confidence": {"type": "number"},
            "status_location": {"type": "string"},
            "remark_codes": {"type": "array", "items": _REMARK_SCHEMA, "maxItems": 12},
        }
    )
    return {
        "type": "object",
        "properties": {
            "plan_name": dict(_FIELD_SCHEMA),
            "claims": {
                "type": "array",
                "minItems": 1,
                "maxItems": MAX_CLAIMS,
                "items": {
                    "type": "object",
                    "properties": claim_properties,
                    "required": list(claim_properties),
                    "additionalProperties": False,
                },
            },
        },
        "required": ["plan_name", "claims"],
        "additionalProperties": False,
    }

