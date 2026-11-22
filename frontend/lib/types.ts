// Shapes of the backend contract (backend/app.py, bill_reader/schema.py,
// eligibility_stub.py, policy_reader/schema.py). The front end only reads these.

export const FIELD_NAMES = [
  "hospital_name",
  "hospital_address",
  "amount_due",
  "service_date",
  "account_number",
] as const;
export type FieldName = (typeof FIELD_NAMES)[number];

/** Anything under this confidence goes to the patient to confirm. Never used silently. */
export const CONFIRM_THRESHOLD = 0.8;

export interface BillField {
  value: string | null;
  confidence: number;
  note: string;
  /** Set by backend code: cents (int) for amount_due, ISO date for service_date. */
  normalized: number | string | null;
}

export interface BillReadData {
  fields: Record<FieldName, BillField>;
  fields_to_confirm: string[];
  seconds: number;
  model: string;
}

export type EligibilityStatus =
  | "likely_free"
  | "likely_discounted"
  | "probably_not_eligible"
  | "cannot_determine";

export interface Evidence {
  quote: string;
  page: number | null;
  confidence: number;
  verified: boolean | null;
  status: "stated" | "not_stated" | "unclear";
}

export interface DiscountTier {
  fpl_min_percent: number | null;
  fpl_max_percent: number | null;
  discount_type:
    | "percent_off"
    | "pays_percent_of_charges"
    | "amount_generally_billed"
    | "sliding_scale"
    | "other";
  value: number | null;
  description: string;
}

export interface EligibilityData {
  status: EligibilityStatus;
  tier: DiscountTier | null;
  evidence: Evidence;
  caveats: string[];
  disclaimer: string;
  percent_of_fpl: number;
  hospital_name: string;
  source_url: string | null;
  engine: string;
}

export interface EligibilityRequest {
  hospital_slug: string;
  household_size: number;
  annual_income: number;
  state: string;
}

export interface Envelope<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface Hospital {
  slug: string;
  name: string;
  state: string;
}

/** What the patient confirmed on the reading or manual screen. Lives in memory only. */
export interface ConfirmedBill {
  fields: Record<FieldName, string>;
  hospital: Hospital;
}
