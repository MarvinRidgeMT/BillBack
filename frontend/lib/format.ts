import type { BillField, FieldName } from "./types";

const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
const grouped = new Intl.NumberFormat("en-US");

/** 481200 -> "$4,812.00" */
export function formatCents(cents: number): string {
  return usd.format(cents / 100);
}

/** "2026-08-14" -> "Aug 14, 2026". Parsed by hand so a time zone can't shift the day. */
export function formatIsoDate(iso: string, locale = "en-US"): string | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!m) return null;
  const date = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat(locale, {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
}

/** What to show for a bill field: the backend's normalized value when there is one, else the text as printed. */
export function displayField(name: FieldName, field: BillField, locale = "en-US"): string {
  if (name === "amount_due" && typeof field.normalized === "number" && Number.isFinite(field.normalized)) {
    return formatCents(field.normalized);
  }
  if (name === "service_date" && typeof field.normalized === "string") {
    return formatIsoDate(field.normalized, locale) ?? field.value ?? "";
  }
  return field.value ?? "";
}

/** 0.971 -> 97 */
export function confidencePercent(confidence: number): number {
  return Math.round(Math.min(Math.max(confidence, 0), 1) * 100);
}

export const MAX_INCOME = 10_000_000;

/** Keep digits only, cap at the backend's limit, and group with commas: "41000" -> "41,000". */
export function formatIncomeInput(raw: string): string {
  const digits = raw.replace(/\D/g, "").replace(/^0+(?=\d)/, "");
  if (!digits) return "";
  return grouped.format(Math.min(Number(digits), MAX_INCOME));
}

/** "41,000" -> 41000. Empty -> null (the patient hasn't answered). */
export function parseIncome(formatted: string): number | null {
  const digits = formatted.replace(/\D/g, "");
  return digits ? Number(digits) : null;
}

/** "boys town hospital" -> "Boys town hospital." Used to show backend error details in plain words. */
export function sentence(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return "";
  const capped = trimmed[0].toUpperCase() + trimmed.slice(1);
  return /[.!?…]$/.test(capped) ? capped : `${capped}.`;
}
