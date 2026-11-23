// Stable backend error codes (backend/errors.py) -> message keys and the way forward for each.
// Plain functions with no imports, so `node --test lib/errors.test.mjs` can run them directly.

export const ERROR_CODES = [
  "bad_file",
  "too_large",
  "invalid_input",
  "not_found",
  "live_off",
  "demo_only",
  "bad_url",
  "fetch_failed",
  "fetch_timeout",
  "not_pdf",
  "no_pdf_link",
  "pdf_encrypted",
  "pdf_empty",
  "too_short",
  "not_policy",
  "ai_unavailable",
  "ai_invalid",
  "server_error",
] as const;
export type ErrorCode = (typeof ERROR_CODES)[number];

/** "network" = we never heard back (offline, timeout, proxy can't reach the backend). */
export type ErrorKey = `err.${ErrorCode}` | "err.network";

export function isErrorCode(code: unknown): code is ErrorCode {
  return typeof code === "string" && (ERROR_CODES as readonly string[]).includes(code);
}

interface ErrorLike {
  code: string | null;
  kind: "rejected" | "unavailable" | "failed";
}

/**
 * The message key for an API error. Known codes win. Without a code: no answer -> "network",
 * a failed answer -> "server_error". A rejection with an unknown code returns null, so the
 * caller may fall back to the backend's English message.
 */
export function errorKey(err: ErrorLike): ErrorKey | null {
  if (isErrorCode(err.code)) return `err.${err.code}`;
  if (err.kind === "unavailable") return "err.network";
  if (err.kind === "failed") return "err.server_error";
  return null;
}

/** What a failed policy read lets the patient do next, most helpful first. */
export type LiveAction = "upload" | "manual" | "retry";

const LINK_PROBLEMS: readonly string[] = ["bad_url", "fetch_failed", "fetch_timeout", "not_pdf", "no_pdf_link"];
const UNREADABLE: readonly string[] = [
  "pdf_encrypted",
  "pdf_empty",
  "too_short",
  "not_policy",
  "ai_invalid",
  "bad_file",
  "too_large",
  "demo_only",
];

/**
 * Link problems -> upload the PDF instead. Unreadable PDFs and reader problems -> enter the limits yourself.
 * live_off -> upload only. A busy reader can be retried. Anything else -> try again or type the limits.
 */
export function liveActions(code: string | null): LiveAction[] {
  if (code === "live_off") return ["upload"];
  if (code !== null && LINK_PROBLEMS.includes(code)) return ["upload", "manual"];
  if (code === "ai_unavailable") return ["retry", "manual"];
  if (code === "invalid_input") return ["manual"];
  if (code !== null && UNREADABLE.includes(code)) return ["manual", "upload"];
  return ["retry", "manual"];
}

/** Bill-read failures where sending the same file again can't help: pick another file instead. */
export function isFileProblem(code: string | null): boolean {
  return code === "bad_file" || code === "too_large" || code === "demo_only";
}
