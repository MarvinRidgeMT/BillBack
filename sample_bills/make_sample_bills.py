"""Generate 10 FAKE hospital bills for the bill-extraction eval (Person C).

Every patient name, account number and street address here is made up. Hospital names are
the hospitals whose public financial assistance policies are cached in cache/policies/, so the
end-to-end flow can match them. Each page says SAMPLE in the footer.

Outputs (into the folder this script is in):
  bill_01..bill_10 (.jpg "photos" and .pdf files) and answer_key.csv

Run from the repo root:  .venv/bin/python sample_bills/make_sample_bills.py
Needs: pillow, numpy, scipy, reportlab
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from scipy.ndimage import gaussian_filter, map_coordinates

OUT = Path(__file__).parent
W, H = 1700, 2200


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    names = (
        ["DejaVuSansMono-Bold.ttf", "Menlo.ttc"] if mono and bold else
        ["DejaVuSansMono.ttf", "Menlo.ttc"] if mono else
        ["DejaVuSans-Bold.ttf", "Arial Bold.ttf", "Helvetica.ttc"] if bold else
        ["DejaVuSans.ttf", "Arial.ttf", "Helvetica.ttc"]
    )
    dirs = ["/usr/share/fonts/truetype/dejavu/", "/System/Library/Fonts/Supplemental/", "/System/Library/Fonts/", ""]
    for n in names:
        for d in dirs:
            try:
                return ImageFont.truetype(d + n, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


# file, condition, slug, state, hospital, address, patient, acct label, acct, service date (display, iso),
# statement date, line items, insurance adj, payments, amount due
BILLS = [
    ("bill_01_clean.jpg", "clean", "usa-health", "AL", "USA Health", "1200 Magnolia Grove Blvd, Mobile, AL 36617",
     "Dana R. Whitfield", "Account Number", "UH-4471902", ("08/14/2026", "2026-08-14"), "09/02/2026",
     [("Emergency department visit, level 4", 2940.00), ("CT scan, abdomen", 1215.00), ("Laboratory services", 657.00)],
     0.00, 0.00, 4812.00),
    ("bill_02_text.pdf", "pdf", "boys-town-national-research-hospital", "NE", "Boys Town National Research Hospital",
     "5500 Larkspur Ave, Omaha, NE 68131", "Marcus T. Ellery", "Acct #", "BT-00938815", ("07/02/2026", "2026-07-02"),
     "08/01/2026", [("Pediatric clinic visit", 410.00), ("Audiology evaluation", 865.50), ("Hearing aid fitting", 1320.00)],
     -540.25, -100.00, 1955.25),
    ("bill_03_angled.jpg", "angled", "fort-healthcare-inc", "WI", "Fort HealthCare", "811 Cedar Bluff Rd, Fort Atkinson, WI 53538",
     "Priya Nandakumar", "Guarantor Account", "FH 7720-1145", ("09/21/2026", "2026-09-21"), "10/05/2026",
     [("Inpatient room, 2 days", 6200.00), ("Pharmacy", 742.80), ("Physical therapy evaluation", 389.00)],
     -2150.00, -250.00, 4931.80),
    ("bill_04_angled_blur.jpg", "angled + slight blur", "marshfield-clinic-health-system", "WI", "Marshfield Clinic Health System",
     "302 Birchwood Lane, Marshfield, WI 54449", "Leonard Okafor", "Account No.", "MC-55203917", ("06/30/2026", "2026-06-30"),
     "07/28/2026", [("Office visit, established patient", 245.00), ("MRI, knee", 2875.00), ("Radiology reading", 310.00)],
     -900.00, 0.00, 2530.00),
    ("bill_05_crumpled.jpg", "crumpled", "adena-health-system", "OH", "Adena Health System", "77 Ridgeline Pkwy, Chillicothe, OH 45601",
     "Teresa Lindqvist", "Account Number", "ADH-3309184", ("10/03/2026", "2026-10-03"), "10/24/2026",
     [("Outpatient surgery", 8450.00), ("Anesthesia", 1630.00), ("Recovery room", 920.00)],
     -3800.00, -500.00, 6700.00),
    ("bill_06_crumpled.jpg", "crumpled", "baptist-memorial-health-care-corporation", "MS", "Baptist Memorial Health Care",
     "4100 Pecan Hollow Dr, Columbus, MS 39705", "Jerome A. Batiste", "Patient Account #", "BMH-20871466",
     ("05/11/2026", "2026-05-11"), "06/09/2026",
     [("Emergency department visit, level 3", 1480.00), ("X-ray, chest, 2 views", 395.00), ("IV therapy", 612.40)],
     0.00, -75.00, 2412.40),
    ("bill_07_dim.jpg", "dim light", "usa-health", "AL", "USA Health", "1200 Magnolia Grove Blvd, Mobile, AL 36617",
     "Kim Ngoc Tran", "Account Number", "UH-4489315", ("04/19/2026", "2026-04-19"), "05/15/2026",
     [("Labor and delivery", 9875.00), ("Newborn nursery care", 2140.00), ("Laboratory services", 486.00)],
     -4200.00, -300.00, 8001.00),
    ("bill_08_dim_angled.jpg", "dim light + angled", "boys-town-national-research-hospital", "NE", "Boys Town National Research Hospital",
     "5500 Larkspur Ave, Omaha, NE 68131", "Alicia Moreno-Vega", "Acct #", "BT-01147722", ("09/09/2026", "2026-09-09"),
     "10/02/2026", [("Specialist consultation", 520.00), ("Sleep study", 2380.00)],
     -650.00, 0.00, 2250.00),
    ("bill_09_text.pdf", "pdf", "marshfield-clinic-health-system", "WI", "Marshfield Clinic Health System",
     "302 Birchwood Lane, Marshfield, WI 54449", "Gregory P. Haldane", "Account No.", "MC-55418820", ("03/03/2026", "2026-03-03"),
     "03/31/2026", [("Urgent care visit", 310.00), ("Rapid strep test", 48.00), ("Prescription, in-clinic", 22.75)],
     0.00, -40.00, 340.75),
    ("bill_10_crumpled_dim.jpg", "crumpled + dim light", "fort-healthcare-inc", "WI", "Fort HealthCare",
     "811 Cedar Bluff Rd, Fort Atkinson, WI 53538", "Samuel K. Oduya", "Guarantor Account", "FH 7735-0092",
     ("11/02/2026", "2026-11-02"), "11/16/2026",
     [("Emergency department visit, level 5", 4260.00), ("CT scan, head", 1890.00), ("Ambulance transport", 1150.00)],
     -1500.00, 0.00, 5800.00),
]


def money(x: float) -> str:
    return f"-${abs(x):,.2f}" if x < 0 else f"${x:,.2f}"


def render(b) -> Image.Image:
    (_, _, _, _, hosp, addr, patient, acct_label, acct, (svc, _), stmt, items, ins, pay, due) = b
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    ink, grey, line = (25, 30, 35), (95, 100, 105), (200, 204, 208)
    # header band
    d.rectangle([0, 0, W, 210], fill=(236, 241, 245))
    size = 52
    while d.textlength(hosp.upper(), font=font(size, bold=True)) > W - 90 - 90 - 640 and size > 30:
        size -= 2
    d.text((90, 60 + (52 - size) // 2), hosp.upper(), font=font(size, bold=True), fill=ink)
    d.text((90, 135), addr, font=font(34), fill=grey)
    d.text((W - 90, 70), "PATIENT STATEMENT", font=font(38, bold=True), fill=ink, anchor="ra")
    d.text((W - 90, 130), f"Statement date: {stmt}", font=font(30), fill=grey, anchor="ra")
    # patient + account block
    y = 280
    d.text((90, y), "Patient", font=font(28), fill=grey)
    d.text((90, y + 40), patient, font=font(38, bold=True), fill=ink)
    d.text((900, y), acct_label, font=font(28), fill=grey)
    d.text((900, y + 40), acct, font=font(38, bold=True, mono=True), fill=ink)
    d.text((90, y + 120), "Date of service", font=font(28), fill=grey)
    d.text((90, y + 160), svc, font=font(38, bold=True), fill=ink)
    d.text((900, y + 120), "Customer service", font=font(28), fill=grey)
    d.text((900, y + 160), "Mon-Fri 8am-5pm", font=font(34), fill=ink)
    # items table
    y = 640
    d.line([90, y, W - 90, y], fill=line, width=3)
    d.text((90, y + 20), "Description", font=font(30, bold=True), fill=ink)
    d.text((W - 90, y + 20), "Charges", font=font(30, bold=True), fill=ink, anchor="ra")
    y += 80
    total = 0.0
    for desc, amt in items:
        d.text((90, y), desc, font=font(34), fill=ink)
        d.text((W - 90, y), money(amt), font=font(34, mono=True), fill=ink, anchor="ra")
        y += 62
        total += amt
    d.line([90, y + 10, W - 90, y + 10], fill=line, width=3)
    y += 40
    for label, amt in [("Total charges", total), ("Insurance adjustments", ins), ("Patient payments", pay)]:
        d.text((900, y), label, font=font(32), fill=grey)
        d.text((W - 90, y), money(amt), font=font(32, mono=True), fill=ink, anchor="ra")
        y += 55
    assert abs(total + ins + pay - due) < 0.005, (b[0], total + ins + pay, due)
    # amount due box
    y += 30
    d.rounded_rectangle([880, y, W - 90, y + 150], radius=14, outline=ink, width=4)
    d.text((910, y + 22), "AMOUNT DUE", font=font(32, bold=True), fill=ink)
    d.text((W - 120, y + 70), money(due), font=font(60, bold=True, mono=True), fill=ink, anchor="ra")
    d.text((90, y + 30), "Please pay within 30 days of the", font=font(30), fill=grey)
    d.text((90, y + 72), "statement date.", font=font(30), fill=grey)
    # help text
    y += 230
    for t in ["Financial assistance may be available. Ask for our financial",
              "assistance policy and application, free of charge."]:
        d.text((90, y), t, font=font(30), fill=grey)
        y += 44
    # payment coupon
    y = 1760
    for x in range(90, W - 90, 30):
        d.line([x, y, x + 15, y], fill=grey, width=3)
    d.text((90, y + 30), "Detach and return with your payment", font=font(26), fill=grey)
    d.text((90, y + 90), f"{acct_label}: {acct}", font=font(32, mono=True), fill=ink)
    d.text((90, y + 140), f"Amount due: {money(due)}", font=font(32, mono=True), fill=ink)
    d.text((W - 90, y + 90), "Amount enclosed: $__________", font=font(32), fill=ink, anchor="ra")
    d.text((W // 2, H - 60), "SAMPLE BILL - FICTIONAL PATIENT - BILLBACK TEST DATA", font=font(24), fill=(150, 150, 150), anchor="ma")
    return img


def noise_field(shape, scale, rng):
    return gaussian_filter(rng.standard_normal(shape), scale)


def crumple(img: Image.Image, rng) -> Image.Image:
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    n1 = noise_field((h, w), 60, rng)
    n2 = noise_field((h, w), 60, rng)
    n1 *= 26 / (np.abs(n1).max() + 1e-6)
    n2 *= 26 / (np.abs(n2).max() + 1e-6)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.stack([map_coordinates(a[..., c], [yy + n1, xx + n2], order=1, mode="nearest") for c in range(3)], -1)
    # shading from a height field plus a few sharp creases
    hf = noise_field((h, w), 40, rng)
    for _ in range(4):
        x0, y0, x1, y1 = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0, w), rng.uniform(0, h)
        dist = np.abs((y1 - y0) * xx - (x1 - x0) * yy + x1 * y0 - y1 * x0) / np.hypot(x1 - x0, y1 - y0)
        hf += rng.uniform(.15, .35) * np.exp(-dist / 22) * rng.choice([-1, 1])
    gy, gx = np.gradient(gaussian_filter(hf, 2))
    shade = 1 + np.clip((gx + gy) * 14, -.22, .16)
    out = np.clip(out * shade[..., None], 0, 255)
    return Image.fromarray(out.astype(np.uint8))


def on_table(img: Image.Image, angle: float, rng, table=(120, 96, 72)) -> Image.Image:
    img = img.convert("RGBA").rotate(angle, expand=True, resample=Image.BICUBIC)
    bg = Image.new("RGBA", (img.width + 260, img.height + 260), table + (255,))
    grain = Image.fromarray((noise_field((bg.height, bg.width), 3, rng) * 60 + 128).clip(0, 255).astype(np.uint8)).convert("RGBA")
    bg = Image.blend(bg, grain, .12)
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow.putalpha(img.getchannel("A").point(lambda v: 90 if v else 0))
    bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)), (150, 160))
    bg.alpha_composite(img, (130, 130))
    # mild perspective: squeeze the top edge
    w, h = bg.size
    s = int(w * rng.uniform(.03, .06))
    bg = bg.transform((w, h), Image.QUAD, (s, 0, 0, h, w, h, w - s, 0), Image.BICUBIC)
    return bg.convert("RGB")


def dim(img: Image.Image, rng) -> Image.Image:
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    vignette = 1 - .45 * (((xx - w * .4) / w) ** 2 + ((yy - h * .35) / h) ** 2) * 2.2
    a = a * .55 * vignette[..., None] * np.array([1.0, .93, .78])
    a += rng.normal(0, 9, a.shape)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(.8))


def make_pdf(path: Path, b) -> None:
    (_, _, _, _, hosp, addr, patient, acct_label, acct, (svc, _), stmt, items, ins, pay, due) = b
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica-Bold", 16); c.drawString(54, 740, hosp.upper())
    c.setFont("Helvetica", 11); c.drawString(54, 722, addr)
    c.setFont("Helvetica-Bold", 13); c.drawRightString(558, 740, "PATIENT STATEMENT")
    c.setFont("Helvetica", 10); c.drawRightString(558, 724, f"Statement date: {stmt}")
    c.setFont("Helvetica", 10)
    c.drawString(54, 680, f"Patient: {patient}"); c.drawString(320, 680, f"{acct_label}: {acct}")
    c.drawString(54, 662, f"Date of service: {svc}")
    y = 620
    c.setFont("Helvetica-Bold", 10); c.drawString(54, y, "Description"); c.drawRightString(558, y, "Charges")
    c.setFont("Helvetica", 10)
    total = 0.0
    for desc, amt in items:
        y -= 18; c.drawString(54, y, desc); c.drawRightString(558, y, money(amt)); total += amt
    for label, amt in [("Total charges", total), ("Insurance adjustments", ins), ("Patient payments", pay)]:
        y -= 18; c.drawString(320, y, label); c.drawRightString(558, y, money(amt))
    y -= 34
    c.setFont("Helvetica-Bold", 14); c.drawString(320, y, "AMOUNT DUE"); c.drawRightString(558, y, money(due))
    c.setFont("Helvetica", 9)
    c.drawString(54, y - 40, "Financial assistance may be available. Ask for our financial assistance policy and application.")
    c.drawCentredString(306, 40, "SAMPLE BILL - FICTIONAL PATIENT - BILLBACK TEST DATA")
    c.save()


def main() -> None:
    rng = np.random.default_rng(22)
    random.seed(22)
    rows = []
    for b in BILLS:
        name, cond = b[0], b[1]
        path = OUT / name
        if name.endswith(".pdf"):
            make_pdf(path, b)
        else:
            img = render(b)
            if "crumpled" in cond:
                img = crumple(img, rng)
            if "angled" in cond:
                img = on_table(img, rng.uniform(6, 11) * rng.choice([-1, 1]), rng)
            elif "crumpled" in cond or "dim" in cond:
                img = on_table(img, rng.uniform(-3, 3), rng, table=(70, 74, 82))
            if "dim" in cond:
                img = dim(img, rng)
            if "blur" in cond:
                img = img.filter(ImageFilter.GaussianBlur(1.6))
            img = ImageOps.contain(img, (1600, 2000))
            img.save(path, quality=86)
        rows.append({
            "file": name, "condition": cond, "hospital_slug": b[2], "state": b[3],
            "hospital_name": b[4], "hospital_address": b[5], "amount_due": f"{b[14]:.2f}",
            "amount_due_cents": round(b[14] * 100), "service_date": b[9][1], "account_number": b[8],
        })
    with (OUT / "answer_key.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)
    print("wrote", len(rows), "bills + answer_key.csv")


if __name__ == "__main__":
    main()
