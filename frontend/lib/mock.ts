// SAMPLE DATA ONLY. Nothing here is real: not the hospital, not the bill, not the policy.
// Used only when NEXT_PUBLIC_DEMO_MODE=1 and the backend can't answer, and always
// shown under a "Sample" banner. Never present any of this as a real result.

import type { BillReadData, EligibilityData, EligibilityStatus, EobField, EobReadData } from "./types";

const SAMPLE_HOSPITAL = "Sample Hospital";

export const MOCK_BILL_READ: BillReadData = {
  fields: {
    hospital_name: { value: "Sample General Hospital (fictional)", confidence: 0.97, note: "", normalized: null },
    hospital_address: { value: "100 Example Street, Sampletown, AL 00000", confidence: 0.95, note: "", normalized: null },
    amount_due: { value: "$4,812.00", confidence: 0.99, note: "", normalized: 481200 },
    service_date: { value: "08/14/2026", confidence: 0.93, note: "", normalized: "2026-08-14" },
    account_number: {
      value: "FAKE-88-20417",
      confidence: 0.71,
      note: "One digit is smudged in the photo.",
      normalized: null,
    },
  },
  fields_to_confirm: ["account_number"],
  seconds: 2.6,
  model: "sample",
};

const eobField = (value: string, normalized: number | string | null, location: string): EobField => ({
  value,
  normalized,
  location,
  confidence: 0.96,
  note: "",
});

export const MOCK_EOB_READ: EobReadData = {
  document: {
    plan_name: eobField("Sample Health Plan (fictional)", null, "page 1, Plan"),
    claims: [
      {
        service_date: eobField("08/14/2026", "2026-08-14", "page 1, Service date"),
        provider: eobField("Sample General Hospital (fictional)", null, "page 1, Provider"),
        billed_amount: eobField("$4,812.00", 481200, "page 1, Provider billed"),
        allowed_amount: eobField("$3,050.00", 305000, "page 1, Plan allowed"),
        plan_paid: eobField("$2,430.00", 243000, "page 1, Plan paid"),
        patient_responsibility: eobField("$620.00", 62000, "page 1, Your responsibility"),
        deductible: eobField("$200.00", 20000, "page 1, Deductible"),
        copay: eobField("$20.00", 2000, "page 1, Copay"),
        coinsurance: eobField("$400.00", 40000, "page 1, Coinsurance"),
        status: "paid",
        status_confidence: 0.98,
        status_location: "page 1, Claim status",
        remark_codes: [],
      },
    ],
  },
  fields_to_confirm: [],
  seconds: 1.8,
  model: "fictional sample",
};

const base = {
  caveats: [] as string[],
  disclaimer: "Likely eligible — not a guarantee",
  hospital_name: SAMPLE_HOSPITAL,
  source_url: null,
  engine: "sample",
};

export const MOCK_ELIGIBILITY: Record<EligibilityStatus, EligibilityData> = {
  likely_free: {
    ...base,
    status: "likely_free",
    tier: null,
    percent_of_fpl: 150,
    evidence: {
      quote:
        "Patients with household income at or below 200% of the Federal Poverty Guidelines are eligible for a 100% discount.",
      page: 3,
      confidence: 0.95,
      verified: true,
      status: "stated",
    },
  },
  likely_discounted: {
    ...base,
    status: "likely_discounted",
    tier: {
      fpl_min_percent: 201,
      fpl_max_percent: 300,
      discount_type: "percent_off",
      value: 75,
      description: "75% off for household income from 201% to 300% of the poverty line.",
    },
    percent_of_fpl: 250,
    evidence: {
      quote:
        "Patients with household income between 201% and 400% of the Federal Poverty Guidelines are eligible for a partial discount.",
      page: 3,
      confidence: 0.92,
      verified: true,
      status: "stated",
    },
  },
  probably_not_eligible: {
    ...base,
    status: "probably_not_eligible",
    tier: null,
    percent_of_fpl: 520,
    evidence: {
      quote: "Discounts are available to patients with household income up to 400% of the Federal Poverty Guidelines.",
      page: 3,
      confidence: 0.92,
      verified: true,
      status: "stated",
    },
  },
  cannot_determine: {
    ...base,
    status: "cannot_determine",
    tier: null,
    percent_of_fpl: 180,
    evidence: { quote: "", page: null, confidence: 0.9, verified: null, status: "not_stated" },
  },
};

/** The one sample result shown when the eligibility service isn't connected. */
export const MOCK_ELIGIBILITY_DEFAULT = MOCK_ELIGIBILITY.likely_free;
