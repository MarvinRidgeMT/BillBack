// Plain-words view of a policy the reader just read (POST /api/policy/read "grounded"), and which bill
// fields need the patient's eyes. No imports, so node --test can run these.

export const GROUNDED_FIELDS = ["free_care", "discount", "asset_test", "residency", "application_window"] as const;
export type GroundedName = (typeof GROUNDED_FIELDS)[number];

export const PROBLEM_CODES = [
  "quote_not_found",
  "policy_unclear",
  "low_confidence",
  "not_stated",
  "failed_sanity_check",
] as const;
export type ProblemCode = (typeof PROBLEM_CODES)[number];
export type ProblemKey = `problem.${ProblemCode}` | "problem.other";

/** Backend problem code -> message key. Unknown codes still say "check this", never nothing. */
export function problemKey(code: string): ProblemKey {
  return (PROBLEM_CODES as readonly string[]).includes(code) ? (`problem.${code}` as ProblemKey) : "problem.other";
}

/** The distinct reasons to check a field, in the backend's order, unknown ones folded into one. */
export function problemKeys(codes: readonly string[]): ProblemKey[] {
  return [...new Set(codes.map(problemKey))];
}

export type ValueKey =
  | "live.value.not_stated"
  | "live.value.free_up_to"
  | "live.value.discount_up_to"
  | "live.value.discount_tiers"
  | "live.value.assets_count"
  | "live.value.assets_dont_count"
  | "live.value.residency_area"
  | "live.value.residency_required"
  | "live.value.residency_none"
  | "live.value.window_days"
  | "live.value.window_from_service"
  | "live.value.window_from_discharge"
  | "live.value.window_from_first_bill"
  | "live.value.window_no_number";

export interface Described {
  key: ValueKey;
  vars?: Record<string, string | number>;
}

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => !!v && typeof v === "object" && !Array.isArray(v);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const pct = (n: number) => Number(n.toFixed(1));

const COUNTED_FROM: Record<string, ValueKey> = {
  date_of_service: "live.value.window_from_service",
  discharge: "live.value.window_from_discharge",
  first_post_discharge_billing_statement: "live.value.window_from_first_bill",
};

/** One grounded value as a sentence key + its numbers. Shapes follow backend/policy_reader/grounding.py. */
export function describeGrounded(name: GroundedName, value: unknown, status?: string): Described {
  const notStated: Described = { key: "live.value.not_stated" };
  switch (name) {
    case "free_care": {
      const n = num(value);
      return n === null ? notStated : { key: "live.value.free_up_to", vars: { pct: pct(n) } };
    }
    case "discount": {
      if (!isObj(value)) return notStated;
      const max = num(value.fpl_max_percent);
      if (max !== null) return { key: "live.value.discount_up_to", vars: { pct: pct(max) } };
      const tiers = Array.isArray(value.tiers) ? value.tiers.length : 0;
      return tiers > 0 ? { key: "live.value.discount_tiers", vars: { n: tiers } } : notStated;
    }
    case "asset_test": {
      if (!isObj(value) || typeof value.applies !== "boolean") return notStated;
      return { key: value.applies ? "live.value.assets_count" : "live.value.assets_dont_count" };
    }
    case "residency": {
      if (!isObj(value) || typeof value.required !== "boolean") return notStated;
      if (!value.required) return { key: "live.value.residency_none" };
      const area = typeof value.area === "string" ? value.area.trim() : "";
      return area ? { key: "live.value.residency_area", vars: { area } } : { key: "live.value.residency_required" };
    }
    case "application_window": {
      if (!isObj(value)) return notStated;
      const days = num(value.days);
      // The policy addresses the deadline but gives no number (e.g. "no application deadline"): point to its words.
      if (days === null) return status === "stated" ? { key: "live.value.window_no_number" } : notStated;
      const from = typeof value.counted_from === "string" ? COUNTED_FROM[value.counted_from] : undefined;
      return { key: from ?? "live.value.window_days", vars: { days } };
    }
  }
}

/** Bill fields under this confidence go to the patient to confirm. Same as CONFIRM_THRESHOLD in types.ts. */
export const LOW_CONFIDENCE = 0.8;

/**
 * Which bill fields the patient must check: under 80% sure, or flagged by the backend
 * (fields_to_confirm, weak_fields). Keeps the order of `names`.
 */
export function fieldsToCheck<N extends string>(
  names: readonly N[],
  fields: Record<N, { confidence: number }>,
  flagged: readonly string[] = [],
): N[] {
  return names.filter((n) => flagged.includes(n) || !(fields[n]?.confidence >= LOW_CONFIDENCE));
}
