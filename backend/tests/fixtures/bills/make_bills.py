"""Generate 3 FAKE hospital bills for tests. Every name/number here is fictional.

Run: .venv/bin/python -m backend.tests.fixtures.bills.make_bills
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent

BILL_A = [
    "SAMPLE GENERAL HOSPITAL (FICTIONAL)",
    "100 Example Way, Springfield, OH 45501",
    "PATIENT STATEMENT - TEST DATA ONLY",
    "Patient: Testy McTestface    DOB: 01/01/1900",
    "Insurance ID: FAKE-INS-000",
    "Account Number: ZZ-TEST-0001",
    "Date of Service: 03/14/2026",
    "Total Charges: $4,980.00",
    "Amount Due: $1,234.56",
]
BILL_B = [
    "LAKESIDE PRETEND MEDICAL CENTER",
    "42 Nowhere Rd, Madison, WI 53703",
    "Statement for: Jane Placeholder",
    "Acct #: FAKE998877",
    "Service Date: 2026-02-02",
    "Please pay: $389.10",
]
BILL_C = [
    "DEMO VALLEY HOSPITAL (NOT REAL)",
    "7 Imaginary Blvd, Mobile, AL 36602",
    "Guarantor: Sam Sample   DOB 02/02/1902",
    "Account: TEST-4455-C",
    "Date of service: 01/09/2026",
    "Balance due: $12,750.00",
]


def make_pdf(path: Path, lines: list[str]) -> None:
    c = canvas.Canvas(str(path), pagesize=letter)
    y = 740
    for line in lines:
        c.drawString(60, y, line)
        y -= 22
    c.save()


def make_png(path: Path, lines: list[str], *, rotate: float = 0, low_contrast: bool = False) -> None:
    img = Image.new("RGB", (1700, 1100), (235, 235, 230) if low_contrast else "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 44)
    except OSError:
        font = ImageFont.load_default()
    ink = (170, 170, 165) if low_contrast else "black"
    for i, line in enumerate(lines):
        draw.text((80, 80 + i * 70), line, fill=ink, font=font)
    if rotate:
        img = img.rotate(rotate, expand=True, fillcolor=(235, 235, 230))
    img.save(path)


if __name__ == "__main__":
    make_pdf(OUT / "bill_a_text.pdf", BILL_A)
    make_png(OUT / "bill_b_photo.png", BILL_B)
    make_png(OUT / "bill_c_rotated_lowcontrast.png", BILL_C, rotate=-8, low_contrast=True)
    print("wrote", sorted(p.name for p in OUT.glob("bill_*")))
