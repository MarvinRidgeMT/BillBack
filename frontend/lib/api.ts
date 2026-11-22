import { sentence } from "./format";
import {
  FIELD_NAMES,
  type BillReadData,
  type EligibilityData,
  type EligibilityRequest,
  type Envelope,
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
  } catch {
    // Not JSON: the proxy answered instead of the backend.
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
  const complete =
    data.fields &&
    FIELD_NAMES.every((name) => {
      const f = data.fields[name];
      return f && typeof f === "object" && typeof f.confidence === "number";
    });
  if (!complete) throw new ApiError("failed", 200);
  return {
    ...data,
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
  if (typeof data.status !== "string" || !data.evidence || typeof data.evidence !== "object") {
    throw new ApiError("failed", 200);
  }
  return {
    ...data,
    caveats: Array.isArray(data.caveats) ? data.caveats.filter((c) => typeof c === "string") : [],
    disclaimer: typeof data.disclaimer === "string" ? data.disclaimer : "",
    source_url: typeof data.source_url === "string" ? data.source_url : null,
  };
}

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "1";
