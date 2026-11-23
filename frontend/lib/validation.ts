// Form checks for the questions, "not listed" and limits forms. No imports, so node --test can run them.

export const MIN_HOUSEHOLD = 1;
export const MAX_HOUSEHOLD = 20; // the backend accepts 1-20
export const MAX_INCOME = 10_000_000;
export const MIN_LIMIT_PERCENT = 100;
export const MAX_LIMIT_PERCENT = 600;
export const MAX_POLICY_BYTES = 25 * 1024 * 1024;

export type Checked<E extends string> = { ok: true; value: number } | { ok: false; error: E };

export type HouseholdError = "blank" | "zero" | "too_many";

/** "3" -> 3. Blank, 0 and over 20 each get their own message. Anything that isn't digits counts as blank. */
export function checkHousehold(raw: string): Checked<HouseholdError> {
  const text = raw.trim();
  if (!/^\d+$/.test(text)) return { ok: false, error: "blank" };
  const n = Number(text);
  if (n < MIN_HOUSEHOLD) return { ok: false, error: "zero" };
  if (n > MAX_HOUSEHOLD) return { ok: false, error: "too_many" };
  return { ok: true, value: n };
}

export type IncomeError = "blank" | "negative" | "too_high";

/** "41,000" -> 41000. A leading minus is kept by the input so we can say why it doesn't work. */
export function checkIncome(raw: string): Checked<IncomeError> {
  const text = raw.trim();
  if (/^-/.test(text)) return { ok: false, error: "negative" };
  const digits = text.replace(/[,\s$]/g, "");
  if (!digits || !/^\d+$/.test(digits)) return { ok: false, error: "blank" };
  const n = Number(digits);
  if (n > MAX_INCOME) return { ok: false, error: "too_high" };
  return { ok: true, value: n };
}

export type LimitError = "blank" | "out_of_range" | "below_free";

/** A percent of the poverty line, 100-600. Optional limits may be blank (value null). */
export function checkLimit(
  raw: string,
  opts: { optional?: boolean; atLeast?: number } = {},
): { ok: true; value: number | null } | { ok: false; error: LimitError } {
  const text = raw.trim().replace(/%$/, "").trim();
  if (!text) return opts.optional ? { ok: true, value: null } : { ok: false, error: "blank" };
  if (!/^\d+(\.\d+)?$/.test(text)) return { ok: false, error: "out_of_range" };
  const n = Number(text);
  if (n < MIN_LIMIT_PERCENT || n > MAX_LIMIT_PERCENT) return { ok: false, error: "out_of_range" };
  if (opts.atLeast !== undefined && n < opts.atLeast) return { ok: false, error: "below_free" };
  return { ok: true, value: n };
}

/** Two letters, any case -> "WI". Anything else -> null. */
export function checkState(raw: string): string | null {
  const text = raw.trim().toUpperCase();
  return /^[A-Z]{2}$/.test(text) ? text : null;
}

/** The state in an address like "100 Main St, Mobile, AL 36604" -> "AL". Null when there isn't a clear one. */
export function stateFromAddress(address: string | null | undefined): string | null {
  if (!address) return null;
  const m = /\b([A-Z]{2})\s+\d{5}(?:-\d{4})?\b/.exec(address) ?? /,\s*([A-Z]{2})\s*$/.exec(address.trim());
  return m ? m[1] : null;
}

export type UrlError = "blank" | "not_web";

/** Only http(s) links. "hospital.org/fap" gets https:// added. */
export function checkPolicyUrl(raw: string): { ok: true; value: string } | { ok: false; error: UrlError } {
  const text = raw.trim();
  if (!text) return { ok: false, error: "blank" };
  const withScheme = /^[a-z][a-z0-9+.-]*:/i.test(text) ? text : `https://${text}`;
  try {
    const url = new URL(withScheme);
    if ((url.protocol !== "https:" && url.protocol !== "http:") || !url.hostname.includes(".")) {
      return { ok: false, error: "not_web" };
    }
    return { ok: true, value: url.href };
  } catch {
    return { ok: false, error: "not_web" };
  }
}

/** A policy upload must be a PDF of at most 25 MB. */
export function checkPolicyFile(file: { name: string; type: string; size: number }): "ok" | "not_pdf" | "too_large" {
  const pdf = file.type === "application/pdf" || /\.pdf$/i.test(file.name);
  if (!pdf || file.size === 0) return "not_pdf";
  if (file.size > MAX_POLICY_BYTES) return "too_large";
  return "ok";
}
