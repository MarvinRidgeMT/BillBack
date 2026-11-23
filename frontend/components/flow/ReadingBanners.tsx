"use client";

import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import type { ApiError } from "@/lib/api";
import { apiErrorText } from "@/lib/errorText";
import { isFileProblem } from "@/lib/errors";
import { useI18n, type Lang, type MessageKey, type Translate } from "@/lib/i18n";

const REASONS: Record<string, MessageKey> = {
  blurry: "reason.blurry",
  too_small: "reason.too_small",
  dark: "reason.dark",
};

/** ["blurry", "dark"] -> "blurry and too dark" / "borrosa y muy oscura". Unknown reasons are left out. */
export function reasonsText(reasons: readonly string[], t: Translate, lang: Lang): string {
  const words = reasons.filter((r) => r in REASONS).map((r) => t(REASONS[r]));
  if (words.length === 0) return "";
  return new Intl.ListFormat(lang === "es" ? "es" : "en", { type: "conjunction" }).format(words);
}

interface ReadErrorBannerProps {
  error: ApiError;
  onRetry: () => void;
  onRetake: () => void;
  onManual: () => void;
  /** Demo mode only, when the reader isn't there: offer the labeled sample. */
  onSample?: () => void;
}

/** The bill read failed (busy AI, bad file, offline...). Always a way forward, never a stack trace. */
export function ReadErrorBanner({ error, onRetry, onRetake, onManual, onSample }: ReadErrorBannerProps) {
  const { t } = useI18n();
  const fileProblem = isFileProblem(error.code);
  return (
    <StatusBanner
      variant="error"
      title={t("reading.error_title")}
      focusOnMount
      actions={
        <>
          {fileProblem ? (
            <Button onClick={onRetake}>{t("reading.choose_other")}</Button>
          ) : (
            <Button onClick={onRetry}>{t("error.try_again")}</Button>
          )}
          <Button variant="ghost" onClick={onManual}>
            {t("reading.enter_by_hand")}
          </Button>
          {onSample && (
            <Button variant="ghost" onClick={onSample}>
              {t("reading.see_sample")}
            </Button>
          )}
        </>
      }
    >
      <p>{apiErrorText(error, t)}</p>
    </StatusBanner>
  );
}

interface UnreadableBannerProps {
  reasons: readonly string[];
  onRetake: () => void;
  onManual: () => void;
}

/** The photo was too poor to trust. Retake it, or type the details with what we did read filled in. */
export function UnreadableBanner({ reasons, onRetake, onManual }: UnreadableBannerProps) {
  const { t, lang } = useI18n();
  const why = reasonsText(reasons, t, lang);
  return (
    <StatusBanner
      variant="error"
      title={t("reading.unreadable_title")}
      focusOnMount
      actions={
        <>
          <Button onClick={onRetake}>{t("reading.retake")}</Button>
          <Button variant="ghost" onClick={onManual}>
            {t("reading.enter_by_hand")}
          </Button>
        </>
      }
    >
      <p>{why ? t("reading.unreadable_body", { reasons: why }) : t("reading.unreadable_body_plain")}</p>
    </StatusBanner>
  );
}

/** Readable, but the photo check flagged it: every detail needs a careful look. */
export function BlurryBanner({ reasons }: { reasons: readonly string[] }) {
  const { t, lang } = useI18n();
  const why = reasonsText(reasons, t, lang);
  return (
    <StatusBanner
      variant="warning"
      title={why ? t("reading.blurry_title", { reasons: why }) : t("reading.blurry_title_plain")}
    >
      <p>{t("reading.blurry_body")}</p>
    </StatusBanner>
  );
}
