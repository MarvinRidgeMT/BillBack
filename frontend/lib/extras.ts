// Result-screen extras. Read-only public policy facts (no AI). Nothing about the patient is sent in a URL.
import type { EligibilityData, EligibilityRequest, Envelope } from "./types";

export interface Box {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface PolicyPage {
  image: string;
  width: number;
  height: number;
  boxes: Box[];
  page: number;
  found: boolean;
}

export interface Thresholds {
  poverty_line: number;
  free_max_percent: number | null;
  discount_max_percent: number | null;
  tiers: { min_percent: number | null; max_percent: number; label: string; discount_percent: number | null }[];
  max_percent: number | null;
}

export interface StateLaw {
  state: string;
  name_en: string;
  name_es: string;
  summary_en: string;
  summary_es: string;
  citation: string;
  url: string;
  checked_on: string;
}

export type CountedFrom = "date_of_service" | "discharge" | "first_post_discharge_billing_statement" | "other";

export interface PolicyFacts {
  hospital_name: string;
  hospital_state: string | null;
  state_law: StateLaw | null;
  application_window: { days: number | null; counted_from: CountedFrom | null; quote: string; page: number | null };
  presumptive_eligibility: string | null;
  has_page_images: boolean;
  /** The packet also includes the hospital's own application form. */
  own_form?: boolean;
  source_url: string | null;
}

const TIMEOUT_MS = 20_000;

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  const res = await fetch(path, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
  const body = (await res.json()) as Envelope<T>;
  if (!res.ok || !body.success || body.data == null) throw new Error(`request failed (${res.status})`);
  return body.data;
}

const pageCache = new Map<string, Promise<PolicyPage>>();

/** Public policy page + quote boxes. Cached per page/quote so the prefetch makes the button instant. */
export function getPolicyPage(slug: string, page: number, quote: string): Promise<PolicyPage> {
  const qs = new URLSearchParams({ slug, page: String(page), quote });
  const key = qs.toString();
  let hit = pageCache.get(key);
  if (!hit) {
    hit = getJson<PolicyPage>(`/api/policy/page?${key}`);
    hit.catch(() => pageCache.delete(key));
    pageCache.set(key, hit);
  }
  return hit;
}

export function getFacts(slug: string): Promise<PolicyFacts> {
  return getJson<PolicyFacts>(`/api/policy/facts?${new URLSearchParams({ slug })}`);
}

/** Household size and state only pick the poverty line row; income is never sent in a URL. */
export function getThresholds(slug: string, householdSize: number, state: string): Promise<Thresholds> {
  const qs = new URLSearchParams({ slug, household_size: String(householdSize), state });
  return getJson<Thresholds>(`/api/policy/thresholds?${qs}`);
}

/** The same rules engine as the real result (POST /api/eligibility), cancellable for the what-if slider. */
export async function whatIfEligibility(body: EligibilityRequest, signal: AbortSignal): Promise<EligibilityData> {
  const res = await fetch("/api/eligibility", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.any([signal, AbortSignal.timeout(TIMEOUT_MS)]),
  });
  const envelope = (await res.json()) as Envelope<EligibilityData>;
  if (!res.ok || !envelope.success || !envelope.data) throw new Error(`eligibility failed (${res.status})`);
  return envelope.data;
}
