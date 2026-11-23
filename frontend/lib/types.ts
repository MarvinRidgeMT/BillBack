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

/** Photo check done by backend code before the AI read. PDFs are not checked (checked: false, ok: true). */
export interface ImageQuality {
  ok: boolean;
  checked: boolean;
  /** "blurry" | "too_small" | "dark" */
  reasons: string[];
}

export interface BillReadData {
  fields: Record<FieldName, BillField>;
  fields_to_confirm: string[];
  seconds: number;
  model: string;
  quality: ImageQuality;
  /** True when the photo was too poor to trust: the patient retakes it or types the details. */
  unreadable: boolean;
  /** Fields the backend thinks are weak even when the AI said it was sure. */
  weak_fields: string[];
  timings?: { bill_read_s?: number };
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
  timings?: { rules_s?: number };
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
  /** Stable error code on failures (backend/errors.py). */
  code?: string;
}

/** One policy field as the reader found it, with the sentence it came from. */
export interface GroundedField {
  /** Shape depends on the field: see describeGrounded in lib/grounded.ts. */
  value: unknown;
  source_quote: string;
  page: number | null;
  confidence: number;
  status: "stated" | "not_stated" | "unclear";
  verified: boolean | null;
  needs_checking: boolean;
  /** quote_not_found | policy_unclear | low_confidence | not_stated | failed_sanity_check */
  problems: string[];
}

export type Grounded = Record<
  "free_care" | "discount" | "asset_test" | "residency" | "application_window",
  GroundedField
>;

/** POST /api/policy/read and /api/policy/manual. Live and manual policies are kept in backend memory only. */
export interface PolicyReadData {
  /** "live-xxxxxxxx" for a policy read now, or a curated slug when we had already read it. */
  slug: string;
  source: "curated" | "live" | "manual";
  hospital_name: string;
  state: string | null;
  grounded: Grounded;
  needs_checking: string[];
  seconds: number;
  beta: boolean;
  timings?: { policy_read_s?: number };
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

/** What the manual form starts with when the patient leaves a bill read: everything read, and what to check. */
export interface ManualInitial {
  fields: Record<FieldName, string>;
  /** Fields under 80% sure or flagged by the backend: highlighted on the form. */
  lowConfidence: FieldName[];
  hospital?: Hospital | null;
}
