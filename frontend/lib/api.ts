import { sentence } from "./format";
import { recordBillRead, recordTiming } from "./timings";
import {
  FIELD_NAMES,
  type BillField,
  type BillReadData,
  type ConfirmedBill,
  type EligibilityData,
  type EligibilityRequest,
  type EligibilityStatus,
  type Envelope,
  type Evidence,
  type Grounded,
  type GroundedField,
  type Hospital,
  type ImageQuality,
  type PolicyReadData,
} from "./types";
import { GROUNDED_FIELDS } from "./grounded";

/**
 * rejected:    the backend understood the request and said no (4xx). `message` is safe to show.
 * unavailable: the service isn't there (503, network failure, timeout, or the proxy can't reach it).
 * failed:      the backend tried and failed (502 and other errors).
 */
export type ApiErrorKind = "rejected" | "unavailable" | "failed";

export class ApiError extends Error {
  /**
   * `code` is the backend's stable error code (backend/errors.py), translated with "err.<code>".
   * `message` is the backend's English text: only a fallback when there is no known code.
   */
  constructor(
    readonly kind: ApiErrorKind,
    readonly status: number | null,
    message = "",
    readonly code: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const READ_TIMEOUT_MS = 60_000;
const ELIGIBILITY_TIMEOUT_MS = 20_000;
/** Reading a whole policy can take 10-60 s, plus the backend's own retries. */
const POLICY_TIMEOUT_MS = 120_000;
const SEARCH_TIMEOUT_MS = 8_000;

async function request<T>(path: string, init: RequestInit, timeoutMs: number): Promise<T> {
  let res: Response;
  try {
    const timeout = AbortSignal.timeout(timeoutMs);
    res = await fetch(path, { ...init, signal: init.signal ? AbortSignal.any([init.signal, timeout]) : timeout });
  } catch {
    throw new ApiError("unavailable", null);
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch (err) {
    // A timeout while the body was still arriving is "not there", not a bad answer.
    const name = err instanceof Error ? err.name : "";
    if (name === "TimeoutError" || name === "AbortError") throw new ApiError("unavailable", res.status);
    // Otherwise it isn't JSON: the proxy answered instead of the backend.
  }

  if (res.ok) {
    const envelope = body as Envelope<T> | null;
    if (envelope && envelope.success === true && envelope.data != null) return envelope.data;
    throw new ApiError("failed", res.status);
  }

  const code = codeOf(body);
  if (res.status === 503 || body === null) throw new ApiError("unavailable", res.status, detailOf(body), code);
  if (res.status >= 400 && res.status < 500) throw new ApiError("rejected", res.status, detailOf(body), code);
  throw new ApiError("failed", res.status, "", code);
}

function codeOf(body: unknown): string | null {
  if (body && typeof body === "object") {
    const { code } = body as { code?: unknown };
    if (typeof code === "string" && code) return code;
  }
  return null;
}

/** FastAPI errors look like {"detail": "..."}; validation errors carry a list we don't show. */
function detailOf(body: unknown): string {
  if (body && typeof body === "object") {
    const { detail, error } = body as { detail?: unknown; error?: unknown };
    if (typeof detail === "string") return sentence(detail);
    if (typeof error === "string") return sentence(error);
  }
  return "";
}

/** POST /api/bill/read. The file goes straight to the backend, which reads it in memory. */
export async function readBill(file: File): Promise<BillReadData> {
  const form = new FormData();
  form.append("file", file, file.name);
  const data = await request<BillReadData>("/api/bill/read", { method: "POST", body: form }, READ_TIMEOUT_MS);
  const raw = data.fields as Record<string, Partial<BillField> | null | undefined> | null | undefined;
  const complete =
    raw &&
    typeof raw === "object" &&
    FIELD_NAMES.every((name) => {
      const f = raw[name];
      return f && typeof f === "object" && typeof f.confidence === "number" && Number.isFinite(f.confidence);
    });
  if (!complete) throw new ApiError("failed", 200);
  // Keep only what the UI uses, in the types it expects.
  const fields = Object.fromEntries(
    FIELD_NAMES.map((name) => {
      const f = raw[name] as Partial<BillField>;
      const field: BillField = {
        value: typeof f.value === "string" && f.value.trim() ? f.value : null,
        confidence: f.confidence as number,
        note: typeof f.note === "string" ? f.note : "",
        normalized: typeof f.normalized === "number" || typeof f.normalized === "string" ? f.normalized : null,
      };
      return [name, field];
    }),
  ) as BillReadData["fields"];
  const seconds = typeof data.seconds === "number" ? data.seconds : 0;
  recordTiming("bill_read_s", data.timings?.bill_read_s ?? seconds);
  recordBillRead(FIELD_NAMES.map((n) => fields[n].confidence));
  return {
    ...data,
    fields,
    fields_to_confirm: strings(data.fields_to_confirm),
    seconds,
    quality: qualityOf(data.quality),
    unreadable: data.unreadable === true,
    weak_fields: strings(data.weak_fields),
  };
}

function strings(v: unknown): string[] {
  return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : [];
}

/** Missing quality means "not checked" (PDFs, older backends): never a warning by itself. */
function qualityOf(raw: unknown): ImageQuality {
  const q = (raw && typeof raw === "object" ? raw : {}) as Partial<ImageQuality>;
  return {
    ok: q.ok !== false,
    checked: q.checked === true,
    reasons: strings(q.reasons),
  };
}

/** POST /api/eligibility. Plain code on the backend makes the call; the front end only shows it. */
export async function checkEligibility(body: EligibilityRequest): Promise<EligibilityData> {
  const data = await request<EligibilityData>(
    "/api/eligibility",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) },
    ELIGIBILITY_TIMEOUT_MS,
  );
  recordTiming("rules_s", data.timings?.rules_s);
  const ev = data.evidence as Partial<Evidence> | null | undefined;
  if (
    !STATUSES.includes(data.status) ||
    !ev ||
    typeof ev !== "object" ||
    typeof data.percent_of_fpl !== "number" ||
    !Number.isFinite(data.percent_of_fpl)
  ) {
    throw new ApiError("failed", 200);
  }
  // Anything missing is read as "unsure", so the patient is told to double-check, never the reverse.
  const evidence: Evidence = {
    quote: typeof ev.quote === "string" ? ev.quote : "",
    page: typeof ev.page === "number" ? ev.page : null,
    confidence: typeof ev.confidence === "number" ? ev.confidence : 0,
    verified: typeof ev.verified === "boolean" ? ev.verified : null,
    status: ev.status === "not_stated" || ev.status === "unclear" ? ev.status : ev.status === "stated" ? "stated" : "unclear",
  };
  return {
    ...data,
    evidence,
    tier: data.tier && typeof data.tier === "object" ? data.tier : null,
    hospital_name: typeof data.hospital_name === "string" ? data.hospital_name : "",
    caveats: Array.isArray(data.caveats) ? data.caveats.filter((c) => typeof c === "string") : [],
    disclaimer: typeof data.disclaimer === "string" ? data.disclaimer : "",
    source_url: typeof data.source_url === "string" ? data.source_url : null,
  };
}

/** Policies read during this visit (live link, uploaded PDF or typed limits) live only in backend memory. */
export function isSessionPolicy(slug: string): boolean {
  return slug.startsWith("live-");
}

const STATUSES: readonly EligibilityStatus[] = [
  "likely_free",
  "likely_discounted",
  "probably_not_eligible",
  "cannot_determine",
];

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "1";

export interface PacketRequest {
  bill: ConfirmedBill["fields"];
  hospital_slug: string;
  household_size: number;
  annual_income: number;
  eligibility: { status: string; percent_of_fpl: number; quote: string; page: number | null; fpl_year: number | null };
  lang: "en" | "es";
  /** "appeal" = the "If they say no" request to reconsider. Default: the application. */
  kind?: "application" | "appeal";
  /** Optional SNAP/Medicaid/WIC answer: adds the benefit letter to the checklist. */
  benefits?: boolean;
}

/** POST /api/packet. The PDF is built in memory on the backend and handed straight to the browser. */
export async function downloadPacket(body: PacketRequest): Promise<void> {
  let res: Response;
  try {
    res = await fetch("/api/packet", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(ELIGIBILITY_TIMEOUT_MS),
    });
  } catch {
    throw new ApiError("unavailable", null);
  }
  if (!res.ok || !res.headers.get("content-type")?.includes("application/pdf")) {
    let code: string | null = null;
    try {
      code = codeOf(await res.json());
    } catch {
      // Not JSON: the proxy answered instead of the backend.
    }
    const kind: ApiErrorKind = res.status === 503 ? "unavailable" : res.status >= 400 && res.status < 500 ? "rejected" : "failed";
    throw new ApiError(kind, res.status, "", code);
  }
  recordTiming("packet_s", res.headers.get("X-Packet-Seconds"));
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `BillBack-${body.kind === "appeal" ? "appeal" : "application"}-${body.hospital_slug}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

/** POST /api/policy/read with a pasted link (only when GET /api/config says live_mode). */
export function readPolicyUrl(url: string): Promise<PolicyReadData> {
  return policyRequest("/api/policy/read", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
}

/** POST /api/policy/read with an uploaded policy PDF. Read in memory on the backend, never saved. */
export function readPolicyFile(file: File): Promise<PolicyReadData> {
  const form = new FormData();
  form.append("file", file, file.name);
  return policyRequest("/api/policy/read", { method: "POST", body: form });
}

export interface ManualPolicyRequest {
  hospital_name: string;
  state: string;
  free_max_percent: number;
  discount_max_percent?: number | null;
}

/** POST /api/policy/manual: the patient typed the limits from the policy themselves. */
export function manualPolicy(body: ManualPolicyRequest): Promise<PolicyReadData> {
  return policyRequest("/api/policy/manual", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function policyRequest(path: string, init: RequestInit): Promise<PolicyReadData> {
  const data = await request<PolicyReadData>(path, init, POLICY_TIMEOUT_MS);
  if (!data || typeof data.slug !== "string" || !data.slug) throw new ApiError("failed", 200);
  recordTiming("policy_read_s", data.timings?.policy_read_s ?? data.seconds);
  const raw = (data.grounded && typeof data.grounded === "object" ? data.grounded : {}) as Record<string, unknown>;
  const grounded = Object.fromEntries(
    GROUNDED_FIELDS.map((name) => [name, groundedField(raw[name])]),
  ) as Grounded;
  return {
    slug: data.slug,
    source: data.source === "curated" || data.source === "manual" ? data.source : "live",
    hospital_name: typeof data.hospital_name === "string" ? data.hospital_name : "",
    state: typeof data.state === "string" && /^[A-Za-z]{2}$/.test(data.state) ? data.state.toUpperCase() : null,
    grounded,
    needs_checking: strings(data.needs_checking),
    seconds: typeof data.seconds === "number" ? data.seconds : 0,
    beta: data.beta === true,
  };
}

/** Anything missing reads as "needs checking", never the reverse. */
function groundedField(raw: unknown): GroundedField {
  const f = (raw && typeof raw === "object" ? raw : {}) as Partial<GroundedField>;
  return {
    value: f.value ?? null,
    source_quote: typeof f.source_quote === "string" ? f.source_quote : "",
    page: typeof f.page === "number" ? f.page : null,
    confidence: typeof f.confidence === "number" ? f.confidence : 0,
    status: f.status === "stated" || f.status === "not_stated" ? f.status : "unclear",
    verified: typeof f.verified === "boolean" ? f.verified : null,
    needs_checking: f.needs_checking !== false,
    problems: strings(f.problems),
  };
}

export interface HospitalHit extends Hospital {
  city: string | null;
}

/** GET /api/hospitals/search?q=. [] means no match. Throws ApiError when the search itself fails. */
export async function searchHospitals(q: string, signal?: AbortSignal): Promise<HospitalHit[]> {
  const rows = await request<unknown>(`/api/hospitals/search?q=${encodeURIComponent(q)}`, { signal }, SEARCH_TIMEOUT_MS);
  if (!Array.isArray(rows)) throw new ApiError("failed", 200);
  return rows
    .filter((h): h is Record<string, unknown> => !!h && typeof h === "object")
    .filter((h) => typeof h.slug === "string" && typeof h.name === "string")
    .map((h) => ({
      slug: h.slug as string,
      name: h.name as string,
      state: typeof h.state === "string" ? h.state : "",
      city: typeof h.city === "string" ? h.city : null,
    }));
}
