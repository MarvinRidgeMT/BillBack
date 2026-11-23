"use client";

import { useI18n } from "@/lib/i18n";

export function TranslationNotice() {
  const { t, machineTranslated } = useI18n();
  if (!machineTranslated) return null;
  return (
    <aside className="translation-notice" role="note">
      <strong>{t("language.ai_notice")}</strong>
      <span>{t("language.letters_notice")}</span>
      <span>{t("language.official_notice")}</span>
    </aside>
  );
}
