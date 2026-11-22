"use client";

import { useI18n } from "@/lib/i18n";

/** Logo left; "How it works" and the language toggle right. */
export function Nav() {
  const { t, toggleLang } = useI18n();
  return (
    <header className="nav">
      <div className="logo">BILLBACK</div>
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
