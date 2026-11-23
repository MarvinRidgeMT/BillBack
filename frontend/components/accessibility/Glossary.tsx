"use client";

import { useId } from "react";
import { useT, type MessageKey } from "@/lib/i18n";

const TERMS = ["deductible", "coinsurance", "fpl", "presumptive", "agb", "collections"] as const;

export function Glossary() {
  const t = useT();
  const id = useId();
  return (
    <section className="glossary" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`}>{t("glossary.title")}</h3>
      <p>{t("glossary.sub")}</p>
      <div className="glossary-terms">
        {TERMS.map((term) => (
          <details key={term}>
            <summary>{t(`glossary.${term}.term` as MessageKey)}</summary>
            <p>{t(`glossary.${term}.definition` as MessageKey)}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
