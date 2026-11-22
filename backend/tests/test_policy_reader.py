import json
import os
from pathlib import Path

import pytest

from backend.policy_reader import cache, extract_text, reader, validate
from backend.policy_reader.schema import PolicyRules, llm_json_schema
from backend.tests.pdf_factory import make_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "sample_rules.json"

PAGES = {
    1: "Example Community Hospital\nFinancial Assistance Policy",
    2: (
        "Patients with household income at or below 200% of the Federal Poverty\n"
        "Guidelines will receive a 100% discount. Patients with household income\n"
        "between 201% and 400% of the Federal Poverty Guidelines will receive a\n"
        "discount according to the sliding scale below."
    ),
    3: "Assets are not considered when determining eligibility.\nApplicants must be residents of the State of Ohio.",
    4: "Patients may apply up to 240 days after the first post-\ndischarge billing statement.",
}


def load_fixture() -> PolicyRules:
    return PolicyRules.model_validate_json(FIXTURE.read_text())


# ---------- schema ----------

def test_schema_round_trip():
    rules = load_fixture()
    again = PolicyRules.model_validate_json(rules.model_dump_json())
    assert again == rules
    assert again.discount.tiers[0].value == 75


def test_llm_schema_is_inlined_and_hides_server_fields():
    schema = llm_json_schema()
    text = json.dumps(schema)
    assert "$ref" not in text and "$defs" not in text
    assert "source" not in schema["properties"]
    assert "needs_human_review" not in schema["properties"]
    evidence = schema["properties"]["free_care"]["properties"]["evidence"]
    assert "verified" not in evidence["properties"]


# ---------- quote verification ----------

def test_exact_quote_verifies():
    ok, page = validate.find_quote("Assets are not considered when determining eligibility.", PAGES, 3)
    assert ok and page == 3


def test_invented_quote_fails():
    ok, _ = validate.find_quote("Patients earning up to 600% FPL receive free care at no cost whatsoever.", PAGES, 2)
    assert not ok


def test_line_breaks_hyphens_and_curly_quotes_still_verify():
    quote = "Patients may apply up to 240 days after the first post‑discharge billing statement."
    ok, page = validate.find_quote(quote, PAGES, 4)
    assert ok and page == 4
    ok, _ = validate.find_quote(
        "Patients with household income at or below 200% of the Federal Poverty Guidelines will receive a 100% discount.",
        PAGES,
        2,
    )
    assert ok


def test_quote_on_wrong_page_is_found_and_page_corrected():
    ok, page = validate.find_quote("Applicants must be residents of the State of Ohio.", PAGES, 1)
    assert ok and page == 3


def test_post_validate_clean_fixture_needs_no_review():
    rules = validate.post_validate(load_fixture(), PAGES)
    assert rules.free_care.evidence.verified is True
    assert rules.needs_human_review is False
    assert rules.warnings == []


def test_post_validate_caps_confidence_for_unverified_quote():
    bad = load_fixture().model_copy(deep=True)
    bad.residency.evidence.quote = "Only residents of Mars may apply for assistance here."
    rules = validate.post_validate(bad, PAGES)
    assert rules.residency.evidence.verified is False
    assert rules.residency.evidence.confidence <= 0.5
    assert rules.needs_human_review is True
    assert "residency" in rules.review_fields
    assert any("residency" in w for w in rules.warnings)


def test_post_validate_does_not_mutate_input():
    original = load_fixture()
    before = original.model_dump()
    validate.post_validate(original, PAGES)
    assert original.model_dump() == before


def test_not_stated_field_is_low_confidence_not_unverified():
    data = json.loads(FIXTURE.read_text())
    data["asset_test"] = {"applies": None, "details": None, "evidence": {"quote": "", "page": None, "confidence": 0.2}}
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert rules.asset_test.evidence.verified is None
    assert "asset_test" in rules.review_fields


# ---------- sanity checks ----------

def test_sanity_flags_free_above_discount():
    data = json.loads(FIXTURE.read_text())
    data["free_care"]["fpl_max_percent"] = 500
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert any("free_care" in w and "discount" in w for w in rules.warnings)
    assert rules.needs_human_review


def test_sanity_flags_overlapping_tiers():
    data = json.loads(FIXTURE.read_text())
    data["discount"]["tiers"][1]["fpl_min_percent"] = 250
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert any("overlap" in w for w in rules.warnings)
    assert rules.discount.evidence.confidence < 0.8


def test_sanity_flags_out_of_range_window_and_percent():
    data = json.loads(FIXTURE.read_text())
    data["application_window"]["days"] = 5
    data["free_care"]["fpl_max_percent"] = 2
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert any("application_window" in w for w in rules.warnings)
    assert any("free_care" in w and "range" in w for w in rules.warnings)


# ---------- text extraction ----------

def test_extract_text_pages_keep_numbers():
    pdf = make_pdf(["Page one text about financial assistance policy rules here.", "Second page with more words in it for sure, well over fifty characters."])
    doc = extract_text.extract_pages(pdf)
    assert [p.number for p in doc.pages] == [1, 2]
    assert "financial assistance" in doc.pages[0].text
    assert "=== PAGE 2 ===" in extract_text.to_prompt_text(doc)
    assert not doc.needs_raw_pdf


def test_scanned_page_triggers_ocr(monkeypatch):
    pdf = make_pdf(["Plenty of real selectable text on this first page of the policy.", ""])
    calls = []
    monkeypatch.setattr(extract_text, "ocr_available", lambda: True)

    def fake_ocr(pdf_bytes, page_number):
        calls.append(page_number)
        return "OCR TEXT: patients with income at or below 250% of FPL receive free care."

    monkeypatch.setattr(extract_text, "ocr_page", fake_ocr)
    doc = extract_text.extract_pages(pdf)
    assert calls == [2]
    assert doc.pages[1].method == "ocr"
    assert "250%" in doc.pages[1].text
    assert not doc.needs_raw_pdf


def test_scanned_page_without_ocr_falls_back_to_raw_pdf(monkeypatch):
    pdf = make_pdf(["Plenty of real selectable text on this first page of the policy.", ""])
    monkeypatch.setattr(extract_text, "ocr_available", lambda: False)
    doc = extract_text.extract_pages(pdf)
    assert doc.needs_raw_pdf
    assert any("raw PDF" in w for w in doc.warnings)


# ---------- reader + cache ----------

class FakeClient:
    def __init__(self, payload: str):
        self.payload = payload
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        return reader.ModelResult(text=self.payload, input_tokens=1000, output_tokens=200, seconds=0.01)


def _policy_pdf() -> bytes:
    return make_pdf([PAGES[1], PAGES[2], PAGES[3], PAGES[4]])


def test_reader_validates_and_saves_to_cache(tmp_path):
    client = FakeClient(FIXTURE.read_text())
    result = reader.read_policy(_policy_pdf(), url="https://example.org/fap.pdf", client=client, cache_dir=tmp_path)
    assert client.calls == 1
    assert not result.cached
    assert result.rules.source.page_count == 4
    assert result.rules.source.url == "https://example.org/fap.pdf"
    assert result.rules.free_care.evidence.verified is True
    saved = list(tmp_path.glob("*.json"))
    assert len(saved) == 1 and saved[0].name.startswith("example-community-hospital__")


def test_cache_hit_skips_model(tmp_path):
    pdf = _policy_pdf()
    reader.read_policy(pdf, client=FakeClient(FIXTURE.read_text()), cache_dir=tmp_path)
    second = FakeClient("this would fail to parse")
    result = reader.read_policy(pdf, client=second, cache_dir=tmp_path)
    assert result.cached
    assert second.calls == 0
    assert result.rules.hospital_name == "Example Community Hospital"


def test_reader_retries_once_on_invalid_json(tmp_path):
    class Flaky(FakeClient):
        def generate(self, prompt):
            self.calls += 1
            text = "{not json" if self.calls == 1 else self.payload
            return reader.ModelResult(text=text, input_tokens=10, output_tokens=10, seconds=0.0)

    client = Flaky(FIXTURE.read_text())
    result = reader.read_policy(_policy_pdf(), client=client, cache_dir=tmp_path, use_cache=False)
    assert client.calls == 2
    assert result.rules.hospital_name == "Example Community Hospital"


def test_cache_lookup_miss_returns_none(tmp_path):
    assert cache.lookup("0" * 64, tmp_path) is None


@pytest.mark.live
@pytest.mark.skipif(not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("GEMINI_API_KEY")), reason="no model API key in env")
def test_live_one_real_policy(tmp_path):
    pdfs = sorted(Path("data/policies").glob("*.pdf"))
    if not pdfs:
        pytest.skip("no policies in data/policies")
    result = reader.read_policy(pdfs[0].read_bytes(), cache_dir=tmp_path, use_cache=False)
    assert result.rules.hospital_name
    assert result.seconds < 120


def test_strict_schema_closes_objects_and_drops_numeric_limits():
    from backend.policy_reader.schema import strict_json_schema

    schema = strict_json_schema()
    text = json.dumps(schema)
    assert "minimum" not in text and "maximum" not in text and "$ref" not in text

    def check(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                assert node["additionalProperties"] is False
                assert set(node["required"]) == set(node["properties"])
            for v in node.values():
                check(v)
        elif isinstance(node, list):
            for v in node:
                check(v)

    check(schema)


def test_raw_pdf_attached_only_when_pages_lack_text(tmp_path, monkeypatch):
    seen = []

    class Recorder(FakeClient):
        def generate(self, prompt):
            seen.append(prompt)
            return super().generate(prompt)

    reader.read_policy(_policy_pdf(), client=Recorder(FIXTURE.read_text()), cache_dir=tmp_path, use_cache=False)
    assert seen[0].pdf_bytes is None
    assert "=== PAGE 3 ===" in seen[0].policy_text


def test_blank_strings_and_zero_page_days_become_null():
    data = json.loads(FIXTURE.read_text())
    data["hospital_state"] = ""
    data["how_to_apply"] = "  "
    data["residency"]["area"] = ""
    data["application_window"]["days"] = 0
    data["asset_test"]["evidence"]["page"] = 0
    rules = PolicyRules.model_validate(data)
    assert rules.hospital_state is None and rules.how_to_apply is None
    assert rules.residency.area is None
    assert rules.application_window.days is None
    assert rules.asset_test.evidence.page is None


def test_strict_schema_fits_claude_union_limit():
    from backend.policy_reader.schema import strict_json_schema

    def count(node):
        if isinstance(node, dict):
            here = 1 if ("anyOf" in node or isinstance(node.get("type"), list)) else 0
            return here + sum(count(v) for v in node.values())
        if isinstance(node, list):
            return sum(count(v) for v in node)
        return 0

    assert count(strict_json_schema()) <= 12


def test_short_table_row_quotes_verify_exactly_but_not_fuzzily():
    pages = {8: "Baptist FAP Discount Summary\n< 200% 100%\n201-250% 95%\n351-400% 80%"}
    assert validate.find_quote("< 200% 100%", pages, 8) == (True, 8)
    assert validate.find_quote("351-400% 80%", pages, 8) == (True, 8)
    assert validate.find_quote("< 250% 100%", pages, 8)[0] is False
    assert validate.find_quote("80%", pages, 8)[0] is False


# ---------- evidence.status (stated / not_stated / unclear) ----------

def _with(field, **evidence):
    data = json.loads(FIXTURE.read_text())
    data[field]["evidence"].update(evidence)
    return data


def test_not_stated_with_high_confidence_needs_no_review():
    data = json.loads(FIXTURE.read_text())
    data["asset_test"] = {"applies": None, "details": None, "evidence": {"quote": "", "page": 0, "confidence": 0.9, "status": "not_stated"}}
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert rules.asset_test.evidence.status == "not_stated"
    assert rules.asset_test.evidence.verified is None
    assert "asset_test" not in rules.review_fields
    assert rules.needs_human_review is False


def test_unclear_always_needs_review():
    data = _with("residency", status="unclear", confidence=0.95)
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert "residency" in rules.review_fields and rules.needs_human_review


def test_not_stated_but_value_given_becomes_unclear():
    data = json.loads(FIXTURE.read_text())
    data["residency"]["evidence"]["status"] = "not_stated"  # but required=True and a quote exist
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert rules.residency.evidence.status == "unclear"
    assert "residency" in rules.review_fields


def test_stated_with_empty_quote_is_unverified():
    data = _with("discount", quote="")
    rules = validate.post_validate(PolicyRules.model_validate(data), PAGES)
    assert rules.discount.evidence.verified is False
    assert "discount" in rules.review_fields


def test_old_json_without_status_still_loads():
    data = json.loads(FIXTURE.read_text())
    assert "status" not in data["free_care"]["evidence"]
    assert PolicyRules.model_validate(data).free_care.evidence.status == "stated"


def test_eval_maps_not_stated_to_one_config_value(monkeypatch):
    from backend import eval_config

    monkeypatch.setattr(eval_config, "NOT_STATED_ANSWER_KEY_VALUE", False)
    assert eval_config.comparable_value(None, "not_stated") is False
    monkeypatch.setattr(eval_config, "NOT_STATED_ANSWER_KEY_VALUE", None)
    assert eval_config.comparable_value(None, "not_stated") is None
    assert eval_config.comparable_value(True, "stated") is True


def test_raw_model_output_saved_and_revalidated_without_model(tmp_path):
    pdf = _policy_pdf()
    reader.read_policy(pdf, client=FakeClient(FIXTURE.read_text()), cache_dir=tmp_path)
    assert list((tmp_path / "raw").glob("*.raw.json"))
    rules = reader.revalidate_cached(pdf, cache_dir=tmp_path)
    assert rules is not None and rules.free_care.evidence.verified is True
