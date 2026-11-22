"use client";

import { useId } from "react";
import { useT } from "@/lib/i18n";

export type Benefits = "yes" | "no" | "skip";

const OPTIONS: Benefits[] = ["yes", "no", "skip"];

/** Optional: does anyone get SNAP, Medicaid or WIC? It never changes the eligibility call. */
export function BenefitsQuestion({ value, onChange }: { value: Benefits; onChange: (v: Benefits) => void }) {
  const t = useT();
  const id = useId();
  return (
    <fieldset className="q benefits-q">
      <legend className="q-label">
        {t("wow.benefits.question")} <span className="whatif-tag">{t("wow.benefits.optional")}</span>
      </legend>
      <div className="choice-row">
        {OPTIONS.map((opt) => (
          <label key={opt} className="choice" htmlFor={`${id}-${opt}`}>
            <input
              id={`${id}-${opt}`}
              type="radio"
              name={`${id}-benefits`}
              value={opt}
              checked={value === opt}
              onChange={() => onChange(opt)}
            />
            <span>{t(`wow.benefits.${opt}`)}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
