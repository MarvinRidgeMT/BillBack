"""Grounded policy reader: quote check in plain code, sanity ranges, derived per-field view, retry-then-fail."""

import json
from pathlib import Path

import pytest

from backend.policy_reader import grounding, reader, validate
from backend.policy_reader.schema import PolicyRules

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sample_rules.json").read_text())
PAGES = {
    1: "Financial Assistance Policy. Example Community Hospital.",
    2: "Patients with household income at or below 200% of the Federal Poverty Guidelines will receive a 100% discount. "
    "Patients with household income between 201% and 400% of the Federal Poverty Guidelines will receive a discount "
    "according to the sliding scale below.",
}


def rules_with(**changes) -> PolicyRules:
    data = json.loads(json.dumps(FIXTURE))
    for path, value in changes.items():
        node = data
        *parents, leaf = path.split("__")
        for key in parents:
            node = node[key]
        node[leaf] = value
    return PolicyRules.model_validate(data)


def test_every_field_has_value_quote_page_confidence():
    view = grounding.grounded_view(validate.post_validate(rules_with(), PAGES))
    assert set(view) == {"free_care", "discount", "asset_test", "residency", "application_window"}
    for field in view.values():
        assert {"value", "source_quote", "page", "confidence", "verified", "needs_checking", "problems"} <= set(field)
    assert view["free_care"]["value"] == 200
    assert view["free_care"]["page"] == 2 and view["free_care"]["verified"] is True


def test_invented_quote_is_unverified_capped_and_needs_checking():
    made_up = "Everyone earning under 500% of poverty gets free care."
    checked = validate.post_validate(rules_with(free_care__evidence__quote=made_up), PAGES)
    field = grounding.grounded_view(checked)["free_care"]
    assert field["verified"] is False
    assert field["confidence"] <= validate.UNVERIFIED_CONFIDENCE_CAP
    assert field["needs_checking"] and grounding.PROBLEM_QUOTE_NOT_FOUND in field["problems"]
    assert "free_care" in checked.review_fields


def test_near_verbatim_quote_passes_fuzzy_check():
    almost = PAGES[2].split(". ")[0].replace("household income", "household  income,") + "."
    checked = validate.post_validate(rules_with(free_care__evidence__quote=almost), PAGES)
    assert checked.free_care.evidence.verified is True


@pytest.mark.parametrize("path,value,field", [
    ("free_care__fpl_max_percent", 650, "free_care"),    # above 600% FPL
    ("free_care__fpl_max_percent", 90, "free_care"),     # below 100% FPL
    ("application_window__days", 400, "application_window"),  # over 365 days
    ("application_window__days", 20, "application_window"),   # under 30 days
])
def test_sanity_ranges_flag_and_never_pass_silently(path, value, field):
    checked = validate.post_validate(rules_with(**{path: value}), PAGES)
    view = grounding.grounded_view(checked)
    assert grounding.PROBLEM_SANITY in view[field]["problems"]
    assert view[field]["needs_checking"]
    assert checked.needs_human_review


def test_free_above_discount_is_flagged():
    view = grounding.grounded_view(validate.post_validate(rules_with(free_care__fpl_max_percent=450), PAGES))
    assert grounding.PROBLEM_SANITY in view["free_care"]["problems"]


def test_free_above_one_tier_top_is_flagged():
    """The Novant shape: free limit under the overall discount limit (400%) but above one tier's top (300%)."""
    data = rules_with(free_care__fpl_max_percent=350)
    view = grounding.grounded_view(validate.post_validate(data, PAGES))
    assert grounding.PROBLEM_SANITY in view["discount"]["problems"]


class _Client:
    def __init__(self, *texts):
        self.texts, self.calls = list(texts), []

    def generate(self, prompt):
        self.calls.append(prompt)
        return reader.ModelResult(text=self.texts.pop(0), input_tokens=10, output_tokens=5, seconds=0.0)


def test_schema_failure_retries_once_with_the_error_then_fails_cleanly(tmp_path):
    from backend.tests.pdf_factory import make_pdf

    client = _Client('{"not": "rules"}', '{"still": "wrong"}')
    with pytest.raises(reader.PolicyReaderError, match="invalid after retry"):
        reader.read_policy(make_pdf(["Financial assistance policy text " * 5]), client=client, cache_dir=tmp_path)
    assert len(client.calls) == 2
    assert client.calls[1].correction and "valid for the schema" in client.calls[1].correction
