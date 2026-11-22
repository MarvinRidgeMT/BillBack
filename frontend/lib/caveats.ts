import type { MessageKey, Translate } from "./i18n";

/**
 * The backend writes caveats in plain English (backend/eligibility.py `_caveats`). Here we turn the
 * known shapes into short, translated sentences. Anything quoted from the policy itself stays in the
 * policy's own words and goes behind a "Policy wording" disclosure. Unknown caveats are shown as sent.
 */
export interface Caveat {
  text: string;
  /** Exact policy wording, shown only when the patient opens it. */
  wording?: string;
}

const PHRASES: Record<string, MessageKey> = {
  "the free-care income limit": "plain.free_care",
  "the discount income limits": "plain.discount",
  "whether savings or property count": "plain.asset_test",
  "where you need to live": "plain.residency",
  "how long you have to apply": "plain.application_window",
  "how much you have in savings or property": "plain.missing_assets",
  "which state you live in": "plain.missing_state",
  "the policy's home-area rule (unclear in the policy)": "plain.unclear_home_area",
  "the policy's savings rule (unclear in the policy)": "plain.unclear_savings",
};

const strip = (s: string) => s.trim().replace(/\.$/, "");

function phrase(p: string, t: Translate): string {
  const key = PHRASES[p.trim().toLowerCase()];
  return key ? t(key) : p.trim();
}

function list(raw: string, sep: string, t: Translate): string {
  return strip(raw)
    .split(sep)
    .map((p) => phrase(p, t))
    .join(sep === ";" ? "; " : ", ");
}

export function plainCaveat(caveat: string, t: Translate): Caveat {
  const c = caveat.trim();
  let m = c.match(/^You may need to live in:\s*(.+)$/i);
  if (m) return { text: t("caveat.residency"), wording: strip(m[1]) };
  m = c.match(/^Savings or property may count:\s*(.+)$/i);
  if (m) return { text: t("caveat.assets"), wording: strip(m[1]) };
  m = c.match(/^The policy doesn't say anything about (.+)$/i);
  if (m) return { text: t("caveat.not_stated", { what: phrase(strip(m[1]), t) }) };
  m = c.match(/^Please double-check with the hospital:\s*(.+)$/i);
  if (m) return { text: t("caveat.review", { what: list(m[1], ",", t) }) };
  m = c.match(/^We still need to know:\s*(.+)$/i);
  if (m) return { text: t("caveat.missing", { what: list(m[1], ";", t) }) };
  return { text: c };
}
