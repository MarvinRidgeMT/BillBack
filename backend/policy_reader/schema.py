"""Rules JSON schema: the contract between the policy reader (A) and the rules engine (B).

Change this only after telling B. The model fills everything except the
server-side fields listed in SERVER_ONLY_FIELDS; those are set by code.
"""

from __future__ import annotations

import copy
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0"

DiscountType = Literal[
    "percent_off",
    "pays_percent_of_charges",
    "amount_generally_billed",
    "sliding_scale",
    "other",
]
CountedFrom = Literal[
    "first_post_discharge_billing_statement",
    "date_of_service",
    "discharge",
    "other",
]
IncomeBasis = Literal["fpl_percent", "income_table", "both", "unclear"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def _unset_markers_to_none(cls, data: Any) -> Any:
        """Strict model output can't use many nulls, so "" (text) and 0 (page/days) mean "not stated"."""
        if not isinstance(data, dict):
            return data
        out = dict(data)
        for name, info in cls.model_fields.items():
            value = out.get(name)
            if info.annotation == Optional[str] and isinstance(value, str) and not value.strip():
                out[name] = None
            elif info.annotation == Optional[int] and value == 0 and not isinstance(value, bool):
                out[name] = None
        return out


class Evidence(_Model):
    quote: str = Field(
        "", description="Verbatim sentence(s) copied from the policy, under 60 words. Empty if not stated."
    )
    page: Optional[int] = Field(None, description="1-based page number where the quote appears.")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    # Set by code after quote verification; never filled by the model.
    verified: Optional[bool] = None


class FreeCare(_Model):
    fpl_max_percent: Optional[float] = Field(
        None, description="Income at or below this % of FPL gets 100% free care. null if not stated."
    )
    evidence: Evidence = Field(default_factory=Evidence)


class DiscountTier(_Model):
    fpl_min_percent: Optional[float] = None
    fpl_max_percent: Optional[float] = None
    discount_type: DiscountType
    value: Optional[float] = Field(
        None, description="Number for the discount_type, e.g. 75 for 75% off. null for AGB/sliding scale."
    )
    description: str = ""


class Discount(_Model):
    fpl_max_percent: Optional[float] = Field(
        None, description="Highest income (% FPL) that gets any discount. null if not stated."
    )
    tiers: list[DiscountTier] = Field(default_factory=list)
    evidence: Evidence = Field(default_factory=Evidence)


class AssetTest(_Model):
    applies: Optional[bool] = None
    details: Optional[str] = None
    evidence: Evidence = Field(default_factory=Evidence)


class Residency(_Model):
    required: Optional[bool] = None
    area: Optional[str] = None
    evidence: Evidence = Field(default_factory=Evidence)


class ApplicationWindow(_Model):
    days: Optional[int] = None
    counted_from: Optional[CountedFrom] = None
    evidence: Evidence = Field(default_factory=Evidence)


class Source(_Model):
    url: Optional[str] = None
    sha256: str
    retrieved_at: str
    page_count: int


class PolicyRules(_Model):
    schema_version: str = SCHEMA_VERSION
    hospital_name: str
    hospital_state: Optional[str] = Field(None, description="Two-letter US state code, or null.")
    source: Optional[Source] = None
    policy_effective_date: Optional[str] = None

    # ---- the 6 answer-key fields ----
    free_care: FreeCare
    discount: Discount
    asset_test: AssetTest
    residency: Residency
    application_window: ApplicationWindow

    # ---- helpful extras ----
    income_basis: IncomeBasis = "unclear"
    uses_income_table: bool = False
    insured_patients_eligible: Optional[bool] = None
    presumptive_eligibility: Optional[str] = None
    how_to_apply: Optional[str] = None
    needs_human_review: bool = False
    review_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


EVIDENCE_FIELDS = ("free_care", "discount", "asset_test", "residency", "application_window")
SERVER_ONLY_FIELDS = ("schema_version", "source", "needs_human_review", "review_fields")
_SERVER_ONLY_EVIDENCE_FIELDS = ("verified",)
_DROP_KEYWORDS = ("title", "default")


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            name = node["$ref"].rsplit("/", 1)[-1]
            return _inline_refs(copy.deepcopy(defs[name]), defs)
        return {
            key: _inline_refs(value, defs)
            for key, value in node.items()
            if key not in _DROP_KEYWORDS and key != "$defs"
        }
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    return node


def _without_properties(node: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    props = {k: v for k, v in node.get("properties", {}).items() if k not in names}
    required = [r for r in node.get("required", []) if r not in names]
    return {**node, "properties": props, "required": required}


def llm_json_schema() -> dict[str, Any]:
    """JSON Schema for Gemini structured output: refs inlined, server-only fields removed."""
    raw = PolicyRules.model_json_schema()
    defs = raw.get("$defs", {})
    defs = {
        **defs,
        "Evidence": _without_properties(defs["Evidence"], _SERVER_ONLY_EVIDENCE_FIELDS),
    }
    schema = _inline_refs(raw, defs)
    schema = _without_properties(schema, SERVER_ONLY_FIELDS)
    # Ask the model for every field so it can't silently skip one.
    schema["required"] = list(schema["properties"].keys())
    return schema


_UNSUPPORTED_STRICT_KEYWORDS = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "minLength", "maxLength")


_COLLAPSIBLE_TYPES = {"string": '"" if not stated', "integer": "0 if not stated"}


def _collapse_nullable(node: dict[str, Any]) -> dict[str, Any]:
    """anyOf[string|integer, null] -> plain type ("" / 0 = not stated) to stay under Claude's union limit."""
    options = node.get("anyOf")
    if not isinstance(options, list) or len(options) != 2 or {"type": "null"} not in options:
        return node
    (real,) = [o for o in options if o != {"type": "null"}]
    if real.get("type") not in _COLLAPSIBLE_TYPES or "enum" in real:
        return node
    rest = {k: v for k, v in node.items() if k != "anyOf"}
    note = _COLLAPSIBLE_TYPES[real["type"]]
    description = f"{rest.get('description', '')} Use {note}.".strip()
    return {**real, **rest, "description": description}


def _strict(node: Any) -> Any:
    if isinstance(node, list):
        return [_strict(item) for item in node]
    if not isinstance(node, dict):
        return node
    node = _collapse_nullable(node)
    out = {k: _strict(v) for k, v in node.items() if k not in _UNSUPPORTED_STRICT_KEYWORDS}
    if out.get("type") == "object" and "properties" in out:
        out["additionalProperties"] = False
        out["required"] = list(out["properties"].keys())
    return out


def strict_json_schema() -> dict[str, Any]:
    """llm_json_schema() for strict structured outputs (Claude): every object closed and fully
    required, numeric/string constraints removed (pydantic re-checks them after parsing)."""
    return _strict(llm_json_schema())
