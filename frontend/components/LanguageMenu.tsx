"use client";

import { Languages } from "lucide-react";
import { LANGUAGE_OPTIONS, useI18n, type Lang } from "@/lib/i18n";

export function LanguageMenu() {
  const { t, lang, setLang } = useI18n();
  return (
    <label className="language-menu">
      <Languages size={18} aria-hidden="true" />
      <span className="sr-only">{t("language.label")}</span>
      <select value={lang} onChange={(event) => setLang(event.target.value as Lang)} aria-label={t("language.label")}>
        {LANGUAGE_OPTIONS.map((option) => (
          <option key={option.code} value={option.code} lang={option.code}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
