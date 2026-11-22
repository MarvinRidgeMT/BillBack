"""Application packet PDF: a request letter + a checklist, built in memory with ReportLab.

Never written to disk. Patient name, address, phone and signature are left blank on purpose:
BillBack never asks for or stores who the patient is.
"""

from __future__ import annotations

import io
import re
from datetime import date
from typing import Any, Literal, Optional
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

Lang = Literal["en", "es"]

_PHONE_RE = re.compile(r"(?:1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_MONTHS_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
              "septiembre", "octubre", "noviembre", "diciembre"]

TEXT: dict[str, dict[str, str]] = {
    "en": {
        "title": "Request for Financial Assistance",
        "to": "To: Financial Assistance Office",
        "re": "Re: Request for free or discounted care under your Financial Assistance Policy",
        "date": "Date",
        "patient_name": "Patient name",
        "patient_address": "Patient address",
        "patient_phone": "Phone",
        "account": "Account number",
        "service_date": "Date of service",
        "amount": "Amount due",
        "household": "People in household",
        "income": "Yearly household income (before taxes)",
        "fpl": "Percent of the federal poverty line ({year} HHS guidelines)",
        "greeting": "To the Financial Assistance Office:",
        "body1": ("I am writing to apply for free or discounted care for the bill listed above under {hospital}'s "
                  "Financial Assistance Policy. My household has {n} {people} and a yearly income of {income}, "
                  "which is about {pct}% of the federal poverty line."),
        "people_one": "person",
        "people_many": "people",
        "body_quote": "Your policy says{page}:",
        "page": " (page {page})",
        "source": "Source: {url}",
        "body2": ("Please review my application for financial assistance. While it is being reviewed, please "
                  "pause all collection activity on this account, including any referral to a collection agency "
                  "or credit bureau."),
        "body3": "I have attached the documents listed on the next page. Please send me your decision in writing.",
        "closing": "Sincerely,",
        "signature": "Signature",
        "check_title": "Checklist: before you send this",
        "attach": "Attach these documents:",
        "doc_id": "A photo ID (driver's license, state ID or passport)",
        "doc_income": "Proof of income: recent pay stubs, your last tax return, or benefit letters (Social Security, unemployment, SNAP)",
        "doc_bill": "A copy of this bill",
        "doc_form": "The hospital's own financial assistance application form, if it has one (ask the billing office)",
        "dollarfor": "Free help with your application: Dollar For, https://dollarfor.org",
        "fill_in": "Fill in your name, address and phone, and sign the letter",
        "copy": "Make a copy of everything for yourself",
        "follow": "Follow up in 30 days if you hear nothing",
        "send": "Send it to the hospital's financial assistance or billing office (the address on your bill)",
        "how": "How to apply, from the hospital's policy:",
        "phone": "Billing / financial assistance phone: {phone}",
        "footer": "Likely eligible, not a guarantee. The hospital makes the final decision. Made with BillBack.",
        "blank": "",
    },
    "es": {
        "title": "Solicitud de asistencia financiera",
        "to": "Para: Oficina de Asistencia Financiera",
        "re": "Asunto: Solicitud de atención gratuita o con descuento según su Política de Asistencia Financiera",
        "date": "Fecha",
        "patient_name": "Nombre del paciente",
        "patient_address": "Dirección del paciente",
        "patient_phone": "Teléfono",
        "account": "Número de cuenta",
        "service_date": "Fecha del servicio",
        "amount": "Monto a pagar",
        "household": "Personas en el hogar",
        "income": "Ingreso anual del hogar (antes de impuestos)",
        "fpl": "Porcentaje del nivel federal de pobreza (guías del HHS {year})",
        "greeting": "A la Oficina de Asistencia Financiera:",
        "body1": ("Les escribo para solicitar atención gratuita o con descuento para la factura indicada arriba, "
                  "según la Política de Asistencia Financiera de {hospital}. En mi hogar somos {n} {people} y el "
                  "ingreso anual es de {income}, que equivale a cerca del {pct}% del nivel federal de pobreza."),
        "people_one": "persona",
        "people_many": "personas",
        "body_quote": "Su política dice{page} (texto original en inglés):",
        "page": " (página {page})",
        "source": "Fuente: {url}",
        "body2": ("Les pido que revisen mi solicitud de asistencia financiera. Mientras la revisan, por favor "
                  "detengan toda gestión de cobro en esta cuenta, incluido cualquier envío a una agencia de cobranza "
                  "o a una agencia de crédito."),
        "body3": "Adjunto los documentos de la página siguiente. Por favor envíenme su decisión por escrito.",
        "closing": "Atentamente,",
        "signature": "Firma",
        "check_title": "Lista: antes de enviarla",
        "attach": "Adjunte estos documentos:",
        "doc_id": "Una identificación con foto (licencia de conducir, identificación estatal o pasaporte)",
        "doc_income": "Comprobante de ingresos: talones de pago recientes, su última declaración de impuestos o cartas de beneficios (Seguro Social, desempleo, SNAP)",
        "doc_bill": "Una copia de esta factura",
        "doc_form": "El formulario de solicitud de asistencia financiera del propio hospital, si tiene uno (pídalo en la oficina de facturación)",
        "dollarfor": "Ayuda gratis con su solicitud: Dollar For, https://dollarfor.org",
        "fill_in": "Escriba su nombre, dirección y teléfono, y firme la carta",
        "copy": "Guarde una copia de todo para usted",
        "follow": "Si no recibe respuesta en 30 días, vuelva a llamar",
        "send": "Envíela a la oficina de asistencia financiera o de facturación del hospital (la dirección de su factura)",
        "how": "Cómo solicitarla, según la política del hospital (en inglés):",
        "phone": "Teléfono de facturación / asistencia financiera: {phone}",
        "footer": "Probablemente califica, pero no es una garantía. El hospital toma la decisión final. Hecho con BillBack.",
        "blank": "",
    },
}

INK = HexColor("#0D2C24")
MUTED = HexColor("#4A5F58")
LINE = HexColor("#9FB8AE")


def _styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle("base", fontName="Helvetica", fontSize=10, leading=13.2, textColor=INK, spaceAfter=5)
    return {
        "base": base,
        "title": ParagraphStyle("title", parent=base, fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=6),
        "small": ParagraphStyle("small", parent=base, fontSize=9, leading=12, textColor=MUTED),
        "quote": ParagraphStyle("quote", parent=base, fontName="Helvetica-Oblique", leftIndent=14, rightIndent=10,
                                borderPadding=(6, 8, 6, 8), backColor=HexColor("#EEF7F2"), spaceBefore=4, spaceAfter=10),
        "check": ParagraphStyle("check", parent=base, leftIndent=18, firstLineIndent=-18, spaceAfter=6),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def _money(value: float, lang: Lang) -> str:
    whole = f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"
    return f"${whole}" if lang == "en" else f"US${whole}"


def _today(lang: Lang, today: date) -> str:
    if lang == "es":
        return f"{today.day} de {_MONTHS_ES[today.month - 1]} de {today.year}"
    return today.strftime("%B %-d, %Y")


def find_phone(how_to_apply: Optional[str]) -> Optional[str]:
    if not how_to_apply:
        return None
    found = _PHONE_RE.search(how_to_apply)
    return found.group(0).strip() if found else None


def _detail_table(rows: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    data = [[_p(k, styles["small"]), _p(v, styles["base"])] for k, v in rows]
    table = Table(data, colWidths=[2.3 * inch, 4.2 * inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return table


def build_packet(
    *,
    bill: dict[str, str],
    hospital_name: str,
    household_size: int,
    annual_income: float,
    percent_of_fpl: float,
    fpl_year: int,
    quote: str,
    page: Optional[int],
    source_url: Optional[str],
    how_to_apply: Optional[str],
    lang: Lang = "en",
    today: Optional[date] = None,
) -> bytes:
    """Return the packet as PDF bytes. Nothing touches the filesystem."""
    tx = TEXT[lang]
    st = _styles()
    today = today or date.today()
    blank = "_" * 34

    story: list[Any] = [
        _p(tx["title"], st["title"]),
        _p(tx["to"], st["base"]),
        _p(hospital_name, st["base"]),
    ]
    if bill.get("hospital_address"):
        story.append(_p(bill["hospital_address"], st["base"]))
    story += [
        Spacer(1, 4),
        _p(tx["re"], st["h2"]),
        _detail_table(
            [
                (tx["date"], _today(lang, today)),
                (tx["patient_name"], blank),
                (tx["patient_address"], blank),
                (tx["patient_phone"], blank),
                (tx["account"], bill.get("account_number") or blank),
                (tx["service_date"], bill.get("service_date") or blank),
                (tx["amount"], bill.get("amount_due") or blank),
                (tx["household"], str(household_size)),
                (tx["income"], _money(annual_income, lang)),
                (tx["fpl"].format(year=fpl_year), f"{round(percent_of_fpl)}%"),
            ],
            st,
        ),
        Spacer(1, 10),
        _p(tx["greeting"], st["base"]),
        _p(
            tx["body1"].format(
                hospital=hospital_name,
                n=household_size,
                people=tx["people_one"] if household_size == 1 else tx["people_many"],
                income=_money(annual_income, lang),
                pct=round(percent_of_fpl),
            ),
            st["base"],
        ),
    ]
    if quote:
        story += [
            _p(tx["body_quote"].format(page=tx["page"].format(page=page) if page else ""), st["base"]),
            _p(f"“{quote}”", st["quote"]),
        ]
        if source_url:
            story.append(_p(tx["source"].format(url=source_url), st["small"]))
    story += [
        _p(tx["body2"], st["base"]),
        _p(tx["body3"], st["base"]),
        Spacer(1, 6),
        _p(tx["closing"], st["base"]),
        Spacer(1, 14),
        _p(f"{blank}    {tx['signature']}", st["base"]),
        PageBreak(),
        _p(tx["check_title"], st["title"]),
        _p(tx["attach"], st["h2"]),
    ]
    box = "[  ]"  # Helvetica has no ballot-box glyph
    for key in ("doc_id", "doc_income", "doc_bill", "doc_form"):
        story.append(_p(f"{box}  {tx[key]}", st["check"]))
    story.append(Spacer(1, 6))
    for key in ("fill_in", "copy", "send", "follow"):
        story.append(_p(f"{box}  {tx[key]}", st["check"]))
    phone = find_phone(how_to_apply)
    if phone or how_to_apply:
        story += [Spacer(1, 8), _p(tx["how"], st["h2"])]
        if phone:
            story.append(_p(tx["phone"].format(phone=phone), st["base"]))
        if how_to_apply:
            story.append(_p(how_to_apply, st["small"]))
    story += [Spacer(1, 10), _p(tx["dollarfor"], st["base"])]

    def footer(canvas, doc) -> None:  # noqa: ANN001 - ReportLab callback signature
        canvas.saveState()
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(LETTER[0] / 2, 0.55 * inch, tx["footer"])
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
        topMargin=0.6 * inch, bottomMargin=0.85 * inch,
        title=tx["title"], author="BillBack",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
