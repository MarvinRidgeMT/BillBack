"""Deterministic bill/EOB reconciliation. AI is not used here."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .schema import EobDocument

MONEY_TOLERANCE_CENTS = 1


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore")


class BillLineItem(_Model):
    code: str = Field("", max_length=80)
    description: str = Field("", max_length=500)
    service_date: str = Field("", max_length=40)
    amount_cents: int = Field(ge=0, le=1_000_000_000)
    source_location: str = Field("bill line item", max_length=200)


class BillSnapshot(_Model):
    provider: str = Field("", max_length=300)
    service_date: str = Field("", max_length=40)
    amount_due_cents: int | None = Field(None, ge=0, le=1_000_000_000)
    billed_amount_cents: int | None = Field(None, ge=0, le=1_000_000_000)
    insurance_adjustment_cents: int | None = Field(None, ge=0, le=1_000_000_000)
    itemized: bool = False
    line_items: list[BillLineItem] = Field(default_factory=list, max_length=200)


DiscrepancyCode = Literal[
    "more_than_patient_responsibility",
    "claim_denied",
    "claim_pending",
    "missing_insurance_adjustment",
    "duplicate_looking_charge",
    "no_itemization",
    "no_matching_claim",
]


class Discrepancy(_Model):
    code: DiscrepancyCode
    severity: Literal["check", "important"]
    bill_value: str
    eob_value: str
    bill_source: str
    eob_source: str
    claim_index: int | None = None


class ReconciliationResult(_Model):
    matched_claim_index: int | None
    match_score: int
    discrepancies: list[Discrepancy]


def _tokens(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def _money(field) -> int | None:  # EobField without importing a runtime protocol
    value = field.normalized
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _date(field) -> str:
    return field.normalized if isinstance(field.normalized, str) else field.value.strip()


def claim_match_score(bill: BillSnapshot, claim) -> int:
    score = 0
    if bill.service_date and _date(claim.service_date) == bill.service_date:
        score += 45
    provider = _tokens(bill.provider)
    claim_provider = _tokens(claim.provider.value)
    if provider and claim_provider:
        ratio = SequenceMatcher(None, provider, claim_provider).ratio()
        if ratio >= 0.8:
            score += 30
        elif ratio >= 0.55:
            score += 15
    pairs = (
        (bill.billed_amount_cents, _money(claim.billed_amount)),
        (bill.amount_due_cents, _money(claim.patient_responsibility)),
    )
    if any(a is not None and b is not None and abs(a - b) <= MONEY_TOLERANCE_CENTS for a, b in pairs):
        score += 25
    return min(score, 100)


def _money_text(cents: int | None) -> str:
    return "not shown" if cents is None else f"${cents / 100:,.2f}"


def _duplicates(bill: BillSnapshot, eob: EobDocument) -> list[Discrepancy]:
    found: list[Discrepancy] = []
    seen_lines: dict[tuple[str, str, int], int] = {}
    for index, item in enumerate(bill.line_items):
        key = (_tokens(item.code or item.description), item.service_date, item.amount_cents)
        if key in seen_lines:
            found.append(
                Discrepancy(
                    code="duplicate_looking_charge",
                    severity="check",
                    bill_value=f"Two similar bill lines at {_money_text(item.amount_cents)}",
                    eob_value="Compare with the insurer's processed claim",
                    bill_source=f"bill line items {seen_lines[key] + 1} and {index + 1}",
                    eob_source="insurance statement claim table",
                )
            )
        else:
            seen_lines[key] = index
    seen_claims: dict[tuple[str, str, int | None], int] = {}
    for index, claim in enumerate(eob.claims):
        key = (_date(claim.service_date), _tokens(claim.provider.value), _money(claim.billed_amount))
        if key in seen_claims:
            found.append(
                Discrepancy(
                    code="duplicate_looking_charge",
                    severity="check",
                    bill_value="Check whether the bill repeats this service",
                    eob_value=f"Two similar claims at {_money_text(key[2])}",
                    bill_source="bill line items",
                    eob_source=f"insurance statement claims {seen_claims[key] + 1} and {index + 1}",
                    claim_index=index,
                )
            )
        else:
            seen_claims[key] = index
    return found


def reconcile(bill: BillSnapshot, eob: EobDocument) -> ReconciliationResult:
    scores = [claim_match_score(bill, claim) for claim in eob.claims]
    best_index = max(range(len(scores)), key=scores.__getitem__) if scores else None
    best_score = scores[best_index] if best_index is not None else 0
    discrepancies: list[Discrepancy] = []

    if best_index is None or best_score < 30:
        discrepancies.append(
            Discrepancy(
                code="no_matching_claim",
                severity="important",
                bill_value=f"{bill.provider or 'provider not shown'}; {bill.service_date or 'date not shown'}",
                eob_value="No close claim match",
                bill_source="bill summary",
                eob_source="insurance statement claim table",
            )
        )
    else:
        claim = eob.claims[best_index]
        responsibility = _money(claim.patient_responsibility)
        if (
            bill.amount_due_cents is not None
            and responsibility is not None
            and bill.amount_due_cents > responsibility + MONEY_TOLERANCE_CENTS
        ):
            discrepancies.append(
                Discrepancy(
                    code="more_than_patient_responsibility",
                    severity="important",
                    bill_value=_money_text(bill.amount_due_cents),
                    eob_value=_money_text(responsibility),
                    bill_source="bill amount due",
                    eob_source=claim.patient_responsibility.location or "insurance statement patient responsibility",
                    claim_index=best_index,
                )
            )
        if claim.status in {"denied", "pending"}:
            discrepancies.append(
                Discrepancy(
                    code="claim_denied" if claim.status == "denied" else "claim_pending",
                    severity="important",
                    bill_value=_money_text(bill.amount_due_cents),
                    eob_value=claim.status,
                    bill_source="bill amount due",
                    eob_source=claim.status_location or "insurance statement claim status",
                    claim_index=best_index,
                )
            )
        billed = _money(claim.billed_amount)
        allowed = _money(claim.allowed_amount)
        if (
            billed is not None
            and allowed is not None
            and billed > allowed + MONEY_TOLERANCE_CENTS
            and bill.insurance_adjustment_cents is None
        ):
            discrepancies.append(
                Discrepancy(
                    code="missing_insurance_adjustment",
                    severity="check",
                    bill_value="No insurance adjustment shown",
                    eob_value=f"Billed {_money_text(billed)}; allowed {_money_text(allowed)}",
                    bill_source="bill summary",
                    eob_source=claim.allowed_amount.location or "insurance statement allowed amount",
                    claim_index=best_index,
                )
            )

    if not bill.itemized or not bill.line_items:
        discrepancies.append(
            Discrepancy(
                code="no_itemization",
                severity="check",
                bill_value="Only a total is available",
                eob_value="Claim totals cannot verify individual services",
                bill_source="bill summary",
                eob_source="insurance statement claim table",
                claim_index=best_index,
            )
        )
    discrepancies.extend(_duplicates(bill, eob))
    return ReconciliationResult(matched_claim_index=best_index if best_score >= 30 else None, match_score=best_score, discrepancies=discrepancies)
