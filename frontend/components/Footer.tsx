"use client";

import { useT } from "@/lib/i18n";

const DOLLAR_FOR_URL = "https://dollarfor.org";
const REPO_URL = "https://github.com/MarvinRidgeMT/BillBack";

/** The small print at the bottom of every screen: who built it, what we don't do, and where the data comes from. */
export function Footer() {
  const t = useT();
  const newTab = <span className="sr-only"> {t("result.new_tab")}</span>;
  return (
    <footer className="site-footer" aria-label={t("footer.label")}>
      <ul>
        <li>{t("footer.built")}</li>
        <li>{t("footer.no_store")}</li>
        <li>{t("footer.not_advice")}</li>
        <li>
          <a href={DOLLAR_FOR_URL} target="_blank" rel="noopener noreferrer">
            Dollar For
            {newTab}
          </a>
        </li>
        <li>
          <a href={REPO_URL} target="_blank" rel="noopener noreferrer">
            {t("footer.repo")}
            {newTab}
          </a>
        </li>
        <li>{t("footer.data")}</li>
      </ul>
    </footer>
  );
}
