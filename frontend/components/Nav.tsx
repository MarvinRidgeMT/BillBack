"use client";

import { useI18n } from "@/lib/i18n";

/** Logo left; "How it works" and the language toggle right. */
export function Nav({ onHome }: { onHome?: () => void }) {
  const { t, toggleLang } = useI18n();
  return (
    <header className="nav">
      <a
        className="logo"
        href="/"
        aria-label="BillBack home"
        style={{ color: "inherit", textDecoration: "none" }}
        onClick={(e) => {
          if (!onHome) return;
          e.preventDefault();
          onHome();
        }}
      >
        BILLBACK
      </a>
      <nav className="nav-links" aria-label="BillBack">
        <a className="nav-link how-link" href="#how">
          {t("nav.how")}
        </a>
        <button type="button" className="nav-link" lang={t("nav.lang_code")} onClick={toggleLang}>
          {t("nav.lang_toggle")}
        </button>
      </nav>
    </header>
  );
}
