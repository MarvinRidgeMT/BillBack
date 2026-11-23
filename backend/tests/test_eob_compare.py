from backend.eob_reader.compare import BillLineItem, BillSnapshot, reconcile
from backend.eob_reader.schema import EobDocument
from backend.tests.test_eob_reader import field


def document(*, patient=20000, status="paid", billed=100000, allowed=70000, second=False):
    def money(cents):
        return {**field(f"${cents / 100:.2f}"), "normalized": cents}

    claim = {
        "service_date": {**field("03/14/2026"), "normalized": "2026-03-14"},
        "provider": field("Sample General Hospital"),
        "billed_amount": money(billed),
        "allowed_amount": money(allowed),
        "plan_paid": money(max(allowed - patient, 0)),
        "patient_responsibility": money(patient),
        "deductible": money(patient),
        "copay": money(0),
        "coinsurance": money(0),
        "status": status,
        "status_confidence": 0.99,
        "status_location": "page 1, claim status",
        "remark_codes": [],
    }
    claims = [claim, dict(claim)] if second else [claim]
    return EobDocument.model_validate({"plan_name": field("Plan"), "claims": claims})


def bill(**overrides):
    data = {
        "provider": "Sample General Hospital",
        "service_date": "2026-03-14",
        "amount_due_cents": 20000,
        "billed_amount_cents": 100000,
        "insurance_adjustment_cents": 30000,
        "itemized": True,
        "line_items": [BillLineItem(code="99283", service_date="2026-03-14", amount_cents=100000)],
    }
    data.update(overrides)
    return BillSnapshot(**data)


def codes(result):
    return [d.code for d in result.discrepancies]


def test_exact_amounts_clean():
    result = reconcile(bill(), document())
    assert result.match_score == 100
    assert result.discrepancies == []


def test_one_cent_rounding_is_not_flagged():
    result = reconcile(bill(amount_due_cents=20001), document(patient=20000))
    assert "more_than_patient_responsibility" not in codes(result)


def test_bill_more_than_patient_responsibility_is_side_by_side():
    result = reconcile(bill(amount_due_cents=25000), document(patient=20000))
    item = next(d for d in result.discrepancies if d.code == "more_than_patient_responsibility")
    assert item.bill_value == "$250.00" and item.eob_value == "$200.00"
    assert "bill" in item.bill_source and "page 1" in item.eob_source


def test_denied_and_pending_claims_are_flagged():
    assert "claim_denied" in codes(reconcile(bill(), document(status="denied")))
    assert "claim_pending" in codes(reconcile(bill(), document(status="pending")))


def test_missing_adjustment_and_no_itemization_are_flagged():
    result = reconcile(bill(insurance_adjustment_cents=None, itemized=False, line_items=[]), document())
    assert {"missing_insurance_adjustment", "no_itemization"}.issubset(codes(result))


def test_duplicate_bill_lines_and_multiple_claims():
    item = BillLineItem(code="99283", service_date="2026-03-14", amount_cents=100000)
    result = reconcile(bill(line_items=[item, item]), document(second=True))
    assert codes(result).count("duplicate_looking_charge") == 2


def test_missing_eob_amount_does_not_invent_overcharge():
    eob = document()
    eob.claims[0].patient_responsibility.normalized = None
    assert "more_than_patient_responsibility" not in codes(reconcile(bill(), eob))
