"use client";

import { useT } from "@/lib/i18n";
import { AccessibilityToolbar } from "@/components/accessibility/AccessibilityToolbar";
import { LanguageMenu } from "@/components/LanguageMenu";

/** Logo left; "How it works" and the language toggle right. */
export function Nav() {
  const t = useT();
  return (
    <header className="nav">
      <div className="logo">BILLBACK</div>
      <nav className="nav-links" aria-label="BillBack">
        <a className="nav-link how-link" href="#how">
          {t("nav.how")}
        </a>
        <AccessibilityToolbar />
        <LanguageMenu />
      </nav>
    </header>
  );
}
