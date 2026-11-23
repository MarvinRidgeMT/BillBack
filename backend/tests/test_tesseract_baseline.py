"""The OCR baseline's text rules (eval/baselines/tesseract_extract.py). Pure text: no Tesseract needed."""

from eval.baselines.tesseract_extract import extract_fields

CLEAN = """USA HEALTH                                PATIENT STATEMENT
1200 Magnolia Grove Blvd, Mobile, AL 36617   Statement date: 09/02/2026
Patient                 Account Number
Dana R. Whitfield       UH-4471902
Date of service
08/14/2026
Emergency department visit, level 4   $2,940.00
Please pay within 30 days of the
statement date.
AMOUNT DUE
$4,812.00
"""


def test_reads_a_clean_layout():
    f = extract_fields(CLEAN)
    assert f == {"hospital_name": "USA HEALTH", "hospital_address": "1200 Magnolia Grove Blvd, Mobile, AL 36617",
                 "amount_due": "$4,812.00", "service_date": "08/14/2026", "account_number": "UH-4471902"}


def test_amount_due_label_beats_an_earlier_please_pay_sentence():
    """Found in the first OCR run: 'Please pay within 30 days' matched first and picked a line item."""
    text = "Please pay within 30 days\nLab work $2,940.00\nAMOUNT DUE $4,812.00\n"
    assert extract_fields(text)["amount_due"] == "$4,812.00"


def test_address_without_commas_and_ocr_dashes():
    text = "FORT HEALTHCARE\n811 Cedar Bluff Rd Fort Atkinson WI 53538\nAccount Number: FH 7720—1145\n"
    f = extract_fields(text)
    assert f["hospital_address"] == "811 Cedar Bluff Rd Fort Atkinson WI 53538"
    assert f["account_number"] == "FH 7720-1145"


def test_ocr_split_money_is_repaired():
    """Seen in real OCR of the angled bill: '$4 931-80' for $4,931.80."""
    assert extract_fields("amount due: $4 931-80\n")["amount_due"] == "$4,931.80"
    assert extract_fields("AMOUNT DUE\n$6 ,200 .00\n")["amount_due"] == "$6,200.00"
