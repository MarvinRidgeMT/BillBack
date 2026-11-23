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
  /** Year of the HHS poverty guidelines the engine used. */
  fpl_year?: number | null;
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

export const EOB_FIELD_NAMES = [
  "service_date",
  "provider",
  "billed_amount",
  "allowed_amount",
  "plan_paid",
  "patient_responsibility",
  "deductible",
  "copay",
  "coinsurance",
] as const;
export type EobFieldName = (typeof EOB_FIELD_NAMES)[number];

export interface EobField {
  value: string;
  confidence: number;
  location: string;
  note: string;
  normalized: number | string | null;
}

export interface EobRemark {
  code: string;
  text: string;
  confidence: number;
  location: string;
}

export interface EobClaim {
  service_date: EobField;
  provider: EobField;
  billed_amount: EobField;
  allowed_amount: EobField;
  plan_paid: EobField;
  patient_responsibility: EobField;
  deductible: EobField;
  copay: EobField;
  coinsurance: EobField;
  status: "paid" | "denied" | "pending" | "unknown";
  status_confidence: number;
  status_location: string;
  remark_codes: EobRemark[];
}

export interface EobDocument {
  plan_name: EobField;
  claims: EobClaim[];
}

export interface EobReadData {
  document: EobDocument;
  fields_to_confirm: string[];
  seconds: number;
  model: string;
}

export interface Discrepancy {
  code:
    | "more_than_patient_responsibility"
    | "claim_denied"
    | "claim_pending"
    | "missing_insurance_adjustment"
    | "duplicate_looking_charge"
    | "no_itemization"
    | "no_matching_claim";
  severity: "check" | "important";
  bill_value: string;
  eob_value: string;
  bill_source: string;
  eob_source: string;
  claim_index: number | null;
}

export interface ReconciliationData {
  matched_claim_index: number | null;
  match_score: number;
  discrepancies: Discrepancy[];
}
