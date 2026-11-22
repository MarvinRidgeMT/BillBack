// The backend's caveats are written for the team, not the patient
// (backend/eligibility_stub.py: "Some policy details need confirming: application_window").
// This turns each one into a plain sentence in the patient's language. The original
// text is still shown, word for word, behind the "Policy wording" disclosure.

import type { MessageKey, Translate } from "./i18n";

const FIELD_WORDS: Record<string, MessageKey> = {
  application_window: "caveat.field.application_window",
  asset_test: "caveat.field.asset_test",
  residency: "caveat.field.residency",
  free_care: "caveat.field.income_limits",
  discount: "caveat.field.income_limits",
};

export interface PlainCaveat {
  /** What the patient reads. */
  text: string;
  /** The backend's own words, kept for the disclosure. */
  original: string;
  /** False when we had no plain version and show the original as it came. */
  rewritten: boolean;
}

export function plainCaveat(original: string, t: Translate): PlainCaveat {
  const raw = original.trim();
  if (/^assets may be considered\b/i.test(raw)) {
    return { text: t("caveat.assets"), original, rewritten: true };
  }
  if (/^residency required\b/i.test(raw)) {
    return { text: t("caveat.residency"), original, rewritten: true };
  }
  const confirm = /^some policy details need confirming:?\s*(.*)$/i.exec(raw);
  if (confirm) {
    const words = confirm[1]
      .split(",")
      .map((name) => name.trim())
      .filter(Boolean)
      // A field we don't know yet is shown with its underscores as spaces.
      .map((name) => (FIELD_WORDS[name] ? t(FIELD_WORDS[name]) : name.replace(/_/g, " ")));
    const list = [...new Set(words)].join(", ");
    return {
      text: list ? t("caveat.confirm", { list }) : t("caveat.confirm_plain"),
      original,
      rewritten: true,
    };
  }
  return { text: original, original, rewritten: false };
}
