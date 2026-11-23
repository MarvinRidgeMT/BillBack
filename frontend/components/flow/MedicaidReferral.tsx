"use client";

import { medicaidReferral } from "@/lib/medicaid";
import { useT } from "@/lib/i18n";

const CMS_RETROACTIVE_SOURCE = "https://www.medicaid.gov/federal-policy-guidance/downloads/cib11182025.pdf";
const HEALTHCARE_GOV = "https://www.healthcare.gov/medicaid-chip/";
const BENEFITS_GOV = "https://www.usa.gov/benefit-finder";

export function MedicaidReferral({ state, percentOfFpl }: { state: string; percentOfFpl: number }) {
  const t = useT();
  const referral = medicaidReferral(state, percentOfFpl);
  if (!referral) return null;

  return (
    <section className="medicaid-referral" aria-labelledby="medicaid-referral-title">
      <h2 id="medicaid-referral-title">{t("medicaid.title")}</h2>
      <p>{t("medicaid.lead", { state: referral.state, pct: referral.adultFplMaxPercent })}</p>
      <p>{t("medicaid.retroactive")}</p>
      <p className="disclaimer">{t("medicaid.change_2027")}</p>
      <p className="disclaimer">{t("medicaid.not_decision")}</p>
      <div className="medicaid-links">
        <a className="text-link" href={referral.applyUrl} target="_blank" rel="noopener noreferrer">{t("medicaid.apply", { state: referral.state })}</a>
        <a className="text-link" href={HEALTHCARE_GOV} target="_blank" rel="noopener noreferrer">HealthCare.gov</a>
        <a className="text-link" href={BENEFITS_GOV} target="_blank" rel="noopener noreferrer">Benefits.gov / USA.gov</a>
        <a className="text-link" href={CMS_RETROACTIVE_SOURCE} target="_blank" rel="noopener noreferrer">{t("medicaid.federal_source")}</a>
      </div>
    </section>
  );
}
