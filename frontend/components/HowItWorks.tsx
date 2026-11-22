"use client";

import { useT } from "@/lib/i18n";

/** The short three-step explainer below the fold. */
export function HowItWorks() {
  const t = useT();
  return (
    <section className="how" id="how" aria-labelledby="how-title">
      <h2 id="how-title">{t("how.title")}</h2>
      <ol>
        <li>
          <h3>{t("how.1_title")}</h3>
          <p>{t("how.1_body")}</p>
        </li>
        <li>
          <h3>{t("how.2_title")}</h3>
          <p>{t("how.2_body")}</p>
        </li>
        <li>
          <h3>{t("how.3_title")}</h3>
          <p>{t("how.3_body")}</p>
        </li>
      </ol>
    </section>
  );
}
