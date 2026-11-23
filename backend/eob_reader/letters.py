"""Insurance follow-up letters, built in memory in English or Spanish."""

from __future__ import annotations

import io
from datetime import date
from typing import Literal
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

Lang = Literal["en", "es"]
LetterKind = Literal["itemized_bill", "billing_hold"]

TEXT = {
    "en": {
        "itemized_bill": "Request for an itemized hospital bill",
        "billing_hold": "Request to hold billing while my insurer reviews the claim",
        "to": "To the hospital billing office:",
        "itemized_body": (
            "Please send me a complete itemized bill showing each service, date, billing code, charge, insurance payment, "
            "contractual adjustment, and the amount assigned to me. I am comparing the bill with my insurer's explanation "
            "of benefits. This request does not claim that any charge is wrong."
        ),
        "hold_body": (
            "I am asking you to place a temporary hold on billing and collection activity while my insurer reviews this "
            "claim. This is a request, not a statement that a hold is legally guaranteed. Please confirm in writing whether "
            "you will place the hold and tell me if you need more information."
        ),
        "details": "Bill and insurance-statement details",
        "hospital": "Hospital/provider",
        "account": "Account number",
        "service": "Service date",
        "bill_amount": "Bill amount due",
        "eob_amount": "Insurance statement patient responsibility",
        "claim_status": "Claim status",
        "closing": "Please respond in writing. I will keep a copy of this request.",
        "sign": "Patient name: ____________________    Signature: ____________________",
        "footer": "BillBack prepared this editable request. Review it before sending.",
    },
    "es": {
        "itemized_bill": "Solicitud de una factura hospitalaria detallada",
        "billing_hold": "Solicitud para detener la facturación mientras mi aseguradora revisa el reclamo",
        "to": "A la oficina de facturación del hospital:",
        "itemized_body": (
            "Por favor envíenme una factura completa y detallada que muestre cada servicio, fecha, código de facturación, "
            "cargo, pago del seguro, ajuste contractual y el monto asignado a mí. Estoy comparando la factura con la "
            "explicación de beneficios de mi aseguradora. Esta solicitud no afirma que algún cargo sea incorrecto."
        ),
        "hold_body": (
            "Les pido que detengan temporalmente la facturación y los cobros mientras mi aseguradora revisa este reclamo. "
            "Esto es una solicitud, no una afirmación de que la pausa esté garantizada por ley. Por favor confirmen por "
            "escrito si harán la pausa y díganme si necesitan más información."
        ),
        "details": "Datos de la factura y del estado del seguro",
        "hospital": "Hospital/proveedor",
        "account": "Número de cuenta",
        "service": "Fecha del servicio",
        "bill_amount": "Monto a pagar de la factura",
        "eob_amount": "Responsabilidad del paciente según el seguro",
        "claim_status": "Estado del reclamo",
        "closing": "Por favor respondan por escrito. Guardaré una copia de esta solicitud.",
        "sign": "Nombre del paciente: ____________________    Firma: ____________________",
        "footer": "BillBack preparó esta solicitud editable. Revísela antes de enviarla.",
    },
}


def build_insurance_letter(
    *,
    kind: LetterKind,
    lang: Lang,
    hospital: str,
    account_number: str,
    service_date: str,
    bill_amount: str,
    eob_patient_responsibility: str,
    claim_status: str,
    today: date | None = None,
) -> bytes:
    tx = TEXT[lang]
    today = today or date.today()
    style = ParagraphStyle("base", fontName="Helvetica", fontSize=11, leading=15, textColor=HexColor("#0D2C24"), spaceAfter=8)
    title = ParagraphStyle("title", parent=style, fontName="Helvetica-Bold", fontSize=16, leading=20)
    body_key = "itemized_body" if kind == "itemized_bill" else "hold_body"

    def p(value: str, use=style) -> Paragraph:
        return Paragraph(escape(value), use)

    story = [
        p(tx[kind], title),
        p(today.isoformat()),
        Spacer(1, 8),
        p(tx["to"]),
        p(tx[body_key]),
        Spacer(1, 8),
        p(tx["details"], title),
        p(f"{tx['hospital']}: {hospital}"),
        p(f"{tx['account']}: {account_number}"),
        p(f"{tx['service']}: {service_date}"),
        p(f"{tx['bill_amount']}: {bill_amount}"),
        p(f"{tx['eob_amount']}: {eob_patient_responsibility}"),
        p(f"{tx['claim_status']}: {claim_status}"),
        Spacer(1, 8),
        p(tx["closing"]),
        Spacer(1, 20),
        p(tx["sign"]),
    ]

    def footer(canvas, doc) -> None:  # noqa: ANN001
        canvas.saveState()
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(HexColor("#4A5F58"))
        canvas.drawCentredString(LETTER[0] / 2, 0.55 * inch, tx["footer"])
        canvas.restoreState()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.85 * inch,
        title=tx[kind],
        author="BillBack",
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
