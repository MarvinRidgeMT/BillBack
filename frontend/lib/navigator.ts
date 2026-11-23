import type { PacketRequest } from "./api";

export type NavigatorStatus = "started" | "result" | "packet_downloaded";

export interface NavigatorCase {
  id: string;
  label: string;
  status: NavigatorStatus;
  packet: PacketRequest | null;
  hospital: string;
  result: string;
}

export function escapeHtml(value: string | number): string {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function summaryHtml(item: NavigatorCase, lang: "en" | "es"): string {
  if (!item.packet) return "";
  const p = item.packet;
  const es = lang === "es";
  const title = es ? "Resumen de ayuda con la factura" : "Hospital bill help summary";
  const rows = [
    [es ? "Caso" : "Case", item.label],
    [es ? "Hospital" : "Hospital", item.hospital],
    [es ? "Resultado" : "Result", item.result],
    [es ? "Tamaño del hogar" : "Household size", p.household_size],
    [es ? "Ingreso anual" : "Yearly income", `$${p.annual_income.toLocaleString("en-US")}`],
    [es ? "Porcentaje de la guía federal" : "Federal poverty guideline percentage", `${Math.round(p.eligibility.percent_of_fpl)}%`],
    [es ? "Cuenta" : "Account", p.bill.account_number || (es ? "No aparece" : "Not shown")],
    [es ? "Fecha del servicio" : "Service date", p.bill.service_date || (es ? "No aparece" : "Not shown")],
  ];
  const next = es
    ? "Próximo paso: descarga y revisa el paquete, confirma todos los datos y envíalo tú mismo al hospital. Este resultado es una guía, no una garantía."
    : "Next step: download and review the packet, confirm every detail, and send it to the hospital yourself. This result is guidance, not a guarantee.";
  return `<!doctype html><html lang="${lang}"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title><style>@page{size:letter;margin:.65in}body{font:16px/1.45 system-ui,sans-serif;color:#123b2f;max-width:7.2in;margin:auto}h1{font-size:26px;border-bottom:4px solid #ff6b4a;padding-bottom:10px}dl{display:grid;grid-template-columns:2fr 3fr;gap:10px;margin:24px 0}dt{font-weight:700}dd{margin:0}.note{padding:14px;background:#eaf8f0;border-radius:10px}footer{margin-top:26px;font-size:13px}</style></head><body><h1>${escapeHtml(title)}</h1><dl>${rows.map(([key,value])=>`<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}</dl><p class="note">${escapeHtml(next)}</p><footer>BillBack · ${escapeHtml(es ? "Nada se guardó" : "Nothing was saved")}</footer></body></html>`;
}
