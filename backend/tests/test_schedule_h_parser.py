from scripts.schedule_h_crosscheck import extract_thresholds, extract_thresholds_from_rendered_html


def test_parses_checkbox_and_other_percentage_schema_variants():
    xml = b"""
    <Return xmlns=\"urn:test\">
      <IRS990ScheduleH>
        <FPGFreeCarePct200Ind>X</FPGFreeCarePct200Ind>
        <FPGDiscountedCareOtherPct>450</FPGDiscountedCareOtherPct>
      </IRS990ScheduleH>
    </Return>
    """
    result = extract_thresholds(xml)
    assert result["free_care"][0]["percent"] == 200
    assert result["discounted_care"][0]["percent"] == 450


def test_zero_and_implausible_percentages_are_ignored():
    xml = b"""
    <Return><FPGFamilyIncmLmtFreeCarePct>000</FPGFamilyIncmLmtFreeCarePct>
    <FPGFamilyIncmLmtDscntCarePct>25000</FPGFamilyIncmLmtDscntCarePct></Return>
    """
    result = extract_thresholds(xml)
    assert result == {"free_care": [], "discounted_care": []}


def test_parses_xml_paths_from_rendered_schedule_h():
    html = b"""
    <input alt="Free care 200%" id="/IRS990ScheduleH/Percent200Ind" checked>
    <span id="/IRS990ScheduleH/Hospital/FPGFamilyIncmLmtFreeCarePct">200.0</span>
    <span id="/IRS990ScheduleH/Hospital/FPGFamilyIncmLmtDscntCarePct">400.0</span>
    <input alt="250% discounted care" id="unused">
    """
    result = extract_thresholds_from_rendered_html(html)
    assert {value["percent"] for value in result["free_care"]} == {200}
    assert result["discounted_care"][0]["percent"] == 400
    assert result["discounted_care"][0]["xml_path"].endswith("FPGFamilyIncmLmtDscntCarePct")
