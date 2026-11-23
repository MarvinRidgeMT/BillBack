export interface MedicaidReferral {
  state: string;
  adultFplMaxPercent: number;
  applyUrl: string;
  thresholdSourceUrl: string;
  checkedOn: string;
}

// Deliberately narrow: states are added only after a current official source is opened.
const VERIFIED_REFERRALS: Record<string, MedicaidReferral> = {
  OH: {
    state: "Ohio",
    adultFplMaxPercent: 138,
    applyUrl: "https://medicaid.ohio.gov/families-and-individuals/coverage/01-how-to-apply",
    thresholdSourceUrl: "https://medicaid.ohio.gov/families-and-individuals/citizen-programs-and-initiatives/medicaid-group-viii",
    checkedOn: "2026-11-23",
  },
};

export function medicaidReferral(state: string, percentOfFpl: number): MedicaidReferral | null {
  const referral = VERIFIED_REFERRALS[state.toUpperCase()];
  return referral && Number.isFinite(percentOfFpl) && percentOfFpl <= referral.adultFplMaxPercent ? referral : null;
}
