"""Generate the three clearly fictional insurance-statement fixtures used by tests and demos."""

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen.canvas import Canvas

OUT = Path(__file__).parent

CASES = {
    "eob_clean.pdf": {
        "status": "PAID",
        "billed": "$4,812.00",
        "allowed": "$3,050.00",
        "plan_paid": "$2,430.00",
        "patient": "$620.00",
        "remark": "Processed under sample plan benefits.",
    },
    "eob_discrepancy.pdf": {
        "status": "PAID",
        "billed": "$4,812.00",
        "allowed": "$3,050.00",
        "plan_paid": "$2,430.00",
        "patient": "$620.00",
        "remark": "Provider may not bill above patient responsibility.",
    },
    "eob_denial.pdf": {
        "status": "DENIED",
        "billed": "$4,812.00",
        "allowed": "$0.00",
        "plan_paid": "$0.00",
        "patient": "$4,812.00",
        "remark": "SAMPLE-16: Additional information requested.",
    },
}


def make(path: Path, values: dict[str, str]) -> None:
    canvas = Canvas(str(path), pagesize=LETTER)
    canvas.setTitle("FICTIONAL SAMPLE — Explanation of Benefits")
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(54, 740, "FICTIONAL SAMPLE — NOT A REAL INSURANCE STATEMENT")
    canvas.setFont("Helvetica", 11)
    rows = [
        ("Plan", "Sample Health Plan (fictional)"),
        ("Provider", "Sample General Hospital (fictional)"),
        ("Service date", "08/14/2026"),
        ("Claim status", values["status"]),
        ("Provider billed", values["billed"]),
        ("Plan allowed", values["allowed"]),
        ("Plan paid", values["plan_paid"]),
        ("Deductible", "$200.00"),
        ("Copay", "$20.00"),
        ("Coinsurance", "$400.00"),
        ("Your responsibility", values["patient"]),
        ("Remark", values["remark"]),
    ]
    y = 690
    for label, value in rows:
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(64, y, f"{label}:")
        canvas.setFont("Helvetica", 11)
        canvas.drawString(190, y, value)
        y -= 30
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.drawString(54, 52, "Generated for BillBack automated tests and demonstrations. All names and values are fictional.")
    canvas.save()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, case in CASES.items():
        make(OUT / filename, case)
