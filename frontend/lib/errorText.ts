import { ApiError } from "./api";
import { errorKey } from "./errors";
import type { Translate } from "./i18n";

/** Anything thrown -> an ApiError, so every screen handles failures the same way. */
export function asApiError(err: unknown): ApiError {
  return err instanceof ApiError ? err : new ApiError("failed", null);
}

/** The patient-facing message: translated by code; the backend's English text only when there's no known code. */
export function apiErrorText(err: ApiError, t: Translate): string {
  const key = errorKey(err);
  if (key) return t(key);
  return err.message || t("err.server_error");
}
