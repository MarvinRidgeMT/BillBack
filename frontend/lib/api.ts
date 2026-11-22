import { sentence } from "./format";
import {
  FIELD_NAMES,
  type BillField,
  type BillReadData,
  type EligibilityData,
  type EligibilityRequest,
  type EligibilityStatus,
  type Envelope,
  type Evidence,
} from "./types";

/**
 * rejected:    the backend understood the request and said no (4xx). `message` is safe to show.
 * unavailable: the service isn't there (503, network failure, timeout, or the proxy can't reach it).
 * failed:      the backend tried and failed (502 and other errors).
 */
export type ApiErrorKind = "rejected" | "unavailable" | "failed";

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    readonly status: number | null,
    message = "",
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const READ_TIMEOUT_MS = 60_000;
const ELIGIBILITY_TIMEOUT_MS = 20_000;

async function request<T>(path: string, init: RequestInit, timeoutMs: number): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { ...init, signal: AbortSignal.timeout(timeoutMs) });
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

  if (res.status === 503 || body === null) throw new ApiError("unavailable", res.status);
  if (res.status >= 400 && res.status < 500) throw new ApiError("rejected", res.status, detailOf(body));
  throw new ApiError("failed", res.status);
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
  return {
    ...data,
    fields,
    fields_to_confirm: Array.isArray(data.fields_to_confirm) ? data.fields_to_confirm : [],
    seconds: typeof data.seconds === "number" ? data.seconds : 0,
  };
}

/** POST /api/eligibility. Plain code on the backend makes the call; the front end only shows it. */
export async function checkEligibility(body: EligibilityRequest): Promise<EligibilityData> {
  const data = await request<EligibilityData>(
    "/api/eligibility",
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) },
    ELIGIBILITY_TIMEOUT_MS,
  );
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

const STATUSES: readonly EligibilityStatus[] = [
  "likely_free",
  "likely_discounted",
  "probably_not_eligible",
  "cannot_determine",
];

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "1";
