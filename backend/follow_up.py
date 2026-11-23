"""Follow-up request letters built in memory in English or Spanish."""

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
Kind = Literal["status_request", "more_documents", "eca_pause_request"]

DOCUMENTS = {
    "income": ("Proof of income", "Comprobante de ingresos"),
    "residency": ("Proof of address or residency", "Comprobante de domicilio o residencia"),
    "tax": ("Most recent tax return, if available", "Declaración de impuestos más reciente, si está disponible"),
    "bank": ("Recent bank statement, if requested by the policy", "Estado de cuenta bancario reciente, si la política lo pide"),
    "insurance": ("Insurance or coverage information", "Información del seguro o cobertura"),
    "benefits": ("Public-benefit award or eligibility letter", "Carta de aprobación o elegibilidad de beneficios públicos"),
}

TEXT = {
    "en": {
        "status_request": "Request for a status update on financial assistance",
        "more_documents": "Financial-assistance document checklist",
        "eca_pause_request": "Request to pause extraordinary collection actions",
        "to": "To the hospital financial-assistance or billing office:",
        "status_body": (
            "I submitted a financial-assistance application and am asking for a written status update. Please tell me "
            "whether the application is complete, whether a decision has been made, and the name of any document still needed."
        ),
        "documents_body": (
            "The hospital asked for more documents. I will send copies, keep the originals, write the account number on each "
            "page, and ask the hospital to confirm receipt. I will send only documents the hospital's policy actually requires."
        ),
        "pause_body": (
            "My financial-assistance application is pending. I am requesting that you pause billing and any extraordinary "
            "collection actions while you review it. Please tell me promptly if the application is incomplete. If it is complete "
            "and was submitted during the application period, IRS Section 501(r)(6) rules require qualifying nonprofit hospitals "
            "to suspend extraordinary collection actions while making an eligibility determination. This letter is a request, not "
            "a guarantee that collection activity will stop. Please confirm your response in writing."
        ),
        "details": "Account details",
        "hospital": "Hospital",
        "account": "Account number",
        "service": "Service date",
        "application": "Application submitted",
        "checklist": "Documents to send",
        "none": "No document selected yet — ask the hospital for a written list.",
        "legal": (
            "If you received court papers, a lawsuit, a bank levy, or a wage-garnishment notice, contact local legal aid or a "
            "lawyer immediately. This request is not legal advice and does not replace a court deadline."
        ),
        "sign": "Patient name: ____________________    Signature: ____________________",
        "footer": "Review before sending. IRS source: irs.gov/charities-non-profits/billing-and-collections-section-501r6",
    },
    "es": {
        "status_request": "Solicitud de actualización sobre la ayuda financiera",
        "more_documents": "Lista de documentos para la ayuda financiera",
        "eca_pause_request": "Solicitud para pausar acciones extraordinarias de cobro",
        "to": "A la oficina de ayuda financiera o facturación del hospital:",
        "status_body": (
            "Presenté una solicitud de ayuda financiera y pido una actualización por escrito. Por favor díganme si la solicitud "
            "está completa, si ya tomaron una decisión y el nombre de cualquier documento que todavía necesiten."
        ),
        "documents_body": (
            "El hospital pidió más documentos. Enviaré copias, guardaré los originales, escribiré el número de cuenta en cada "
            "página y pediré confirmación de recibido. Enviaré solo los documentos que realmente exige la política del hospital."
        ),
        "pause_body": (
            "Mi solicitud de ayuda financiera está pendiente. Les pido que pausen la facturación y cualquier acción extraordinaria "
            "de cobro mientras la revisan. Por favor avísenme pronto si está incompleta. Si está completa y se presentó durante el "
            "período de solicitud, las reglas de la Sección 501(r)(6) del IRS exigen que los hospitales sin fines de lucro sujetos a "
            "la regla suspendan las acciones extraordinarias de cobro mientras deciden la elegibilidad. Esta carta es una solicitud; "
            "no garantiza que los cobros se detendrán. Por favor confirmen su respuesta por escrito."
        ),
        "details": "Datos de la cuenta",
        "hospital": "Hospital",
        "account": "Número de cuenta",
        "service": "Fecha del servicio",
        "application": "Solicitud presentada",
        "checklist": "Documentos para enviar",
        "none": "Todavía no se eligió un documento; pide al hospital una lista por escrito.",
        "legal": (
            "Si recibiste documentos judiciales, una demanda, un embargo bancario o un aviso de embargo de sueldo, comunícate de "
            "inmediato con ayuda legal local o un abogado. Esta solicitud no es asesoría legal y no reemplaza un plazo judicial."
        ),
        "sign": "Nombre del paciente: ____________________    Firma: ____________________",
        "footer": "Revisa antes de enviar. Fuente del IRS: irs.gov/charities-non-profits/billing-and-collections-section-501r6",
    },
}


def build_follow_up_letter(
    *,
    kind: Kind,
    lang: Lang,
    hospital: str,
    account_number: str,
    service_date: str,
    application_date: str = "",
    documents: list[str] | None = None,
    today: date | None = None,
) -> bytes:
    tx = TEXT[lang]
    today = today or date.today()
    documents = [item for item in (documents or []) if item in DOCUMENTS]
    style = ParagraphStyle("base", fontName="Helvetica", fontSize=11, leading=15, textColor=HexColor("#0D2C24"), spaceAfter=8)
    title = ParagraphStyle("title", parent=style, fontName="Helvetica-Bold", fontSize=16, leading=20)

    def p(value: str, use=style) -> Paragraph:
        return Paragraph(escape(value), use)

    body_key = {"status_request": "status_body", "more_documents": "documents_body", "eca_pause_request": "pause_body"}[kind]
    story = [
        p(tx[kind], title), p(today.isoformat()), Spacer(1, 8), p(tx["to"]), p(tx[body_key]),
        Spacer(1, 8), p(tx["details"], title), p(f"{tx['hospital']}: {hospital}"),
        p(f"{tx['account']}: {account_number}"), p(f"{tx['service']}: {service_date}"),
        p(f"{tx['application']}: {application_date or '____________________'}"),
    ]
    if kind == "more_documents":
        story.extend([Spacer(1, 8), p(tx["checklist"], title)])
        if documents:
            story.extend(p(f"[ ] {DOCUMENTS[item][0 if lang == 'en' else 1]}") for item in documents)
        else:
            story.append(p(tx["none"]))
    if kind == "eca_pause_request":
        story.extend([Spacer(1, 8), p(tx["legal"])])
    story.extend([Spacer(1, 20), p(tx["sign"])])

    def footer(canvas, doc) -> None:  # noqa: ANN001
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(HexColor("#4A5F58"))
        canvas.drawCentredString(LETTER[0] / 2, 0.48 * inch, tx["footer"])
        canvas.restoreState()

    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=LETTER, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.65 * inch, bottomMargin=0.8 * inch, title=tx[kind], author="BillBack",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
