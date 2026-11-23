"use client";

import { useEffect, useId, useRef, useState } from "react";
import { FileUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import type { ManualPolicyRequest } from "@/lib/api";
import { useT, type MessageKey } from "@/lib/i18n";
import {
  checkLimit,
  checkPolicyFile,
  checkPolicyUrl,
  checkState,
  type LimitError,
} from "@/lib/validation";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const DOLLAR_FOR_URL = "https://dollarfor.org";
const PDF_ACCEPT = ".pdf,application/pdf";

/** How the patient gave us the policy. Kept in memory by Flow so "Try again" can resend it. */
export type PolicyInput =
  | { kind: "url"; url: string }
  | { kind: "file"; file: File }
  | { kind: "manual"; body: ManualPolicyRequest };

/** What was typed on this screen, so coming back after a failure shows it again. */
export interface NotListedDraft {
  url: string;
  hospital: string;
  state: string;
  free: string;
  discount: string;
}

/** Which part to land on when coming back: the upload (link failed) or the limits form (PDF unreadable). */
export type NotListedFocus = "upload" | "manual" | null;

export function emptyDraft(hospital: string, state: string | null): NotListedDraft {
  return { url: "", hospital, state: state ?? "", free: "", discount: "" };
}

const LIMIT_ERRORS: Record<LimitError, MessageKey> = {
  blank: "notlisted.err_limit_blank",
  out_of_range: "notlisted.err_limit_range",
  below_free: "notlisted.err_below_free",
};

interface NotListedProps {
  entrance: Entrance;
  reduce: boolean;
  /** GET /api/config live_mode. Off: upload only, no link box. */
  liveMode: boolean;
  draft: NotListedDraft;
  focus?: NotListedFocus;
  onRead: (input: PolicyInput, draft: NotListedDraft) => void;
  onBack: () => void;
  /** Start with every limits-form error showing (the /states page). */
  revealErrors?: boolean;
}

/** "My hospital isn't listed": give us the policy (link or PDF), how to find it, free help, or type the limits. */
export function NotListed({ entrance, reduce, liveMode, draft, focus = null, onRead, onBack, revealErrors = false }: NotListedProps) {
  const t = useT();
  const id = useId();
  const [url, setUrl] = useState(draft.url);
  const [urlError, setUrlError] = useState<MessageKey | null>(null);
  const [fileError, setFileError] = useState<MessageKey | null>(null);
  const [hospital, setHospital] = useState(draft.hospital);
  const [state, setState] = useState(draft.state);
  const [free, setFree] = useState(draft.free);
  const [discount, setDiscount] = useState(draft.discount);
  const [tried, setTried] = useState(revealErrors);
  const fileInput = useRef<HTMLInputElement>(null);
  const uploadButton = useRef<HTMLButtonElement>(null);
  const manualHeading = useRef<HTMLHeadingElement>(null);

  const current = (): NotListedDraft => ({ url, hospital, state, free, discount });
  const name = hospital.trim();

  // Coming back from a failed read: land on the way forward that was offered. Runs after the heading's own focus.
  useEffect(() => {
    if (focus === "upload") uploadButton.current?.focus();
    if (focus === "manual") manualHeading.current?.focus();
  }, [focus]);

  function readLink(e: React.FormEvent) {
    e.preventDefault();
    const checked = checkPolicyUrl(url);
    if (!checked.ok) {
      setUrlError(checked.error === "blank" ? "notlisted.url_blank" : "notlisted.url_bad");
      document.getElementById(`${id}-url`)?.focus();
      return;
    }
    setUrlError(null);
    onRead({ kind: "url", url: checked.value }, current());
  }

  function takeFile(file: File | undefined) {
    if (!file) return;
    const verdict = checkPolicyFile(file);
    if (verdict !== "ok") {
      setFileError(verdict === "too_large" ? "notlisted.pdf_too_large" : "notlisted.pdf_bad");
      return;
    }
    setFileError(null);
    const pdf = file.type === "application/pdf" ? file : new File([file], file.name, { type: "application/pdf" });
    onRead({ kind: "file", file: pdf }, current());
  }

  const stateCode = checkState(state);
  const freeCheck = checkLimit(free);
  const discountCheck = checkLimit(discount, {
    optional: true,
    atLeast: freeCheck.ok && freeCheck.value !== null ? freeCheck.value : undefined,
  });
  const nameError = tried && name.length < 2 ? "notlisted.err_name" : null;
  const stateError = tried && !stateCode ? "live.state_error" : null;
  const freeError = tried && !freeCheck.ok ? LIMIT_ERRORS[freeCheck.error] : null;
  const discountError = tried && !discountCheck.ok ? LIMIT_ERRORS[discountCheck.error] : null;

  function submitLimits(e: React.FormEvent) {
    e.preventDefault();
    setTried(true);
    if (name.length < 2 || !stateCode || !freeCheck.ok || freeCheck.value === null || !discountCheck.ok) {
      const first = name.length < 2 ? "name" : !stateCode ? "state" : !freeCheck.ok ? "free" : "discount";
      document.getElementById(`${id}-${first}`)?.focus();
      return;
    }
    onRead(
      {
        kind: "manual",
        body: {
          hospital_name: name,
          state: stateCode,
          free_max_percent: freeCheck.value,
          discount_max_percent: discountCheck.value,
        },
      },
      current(),
    );
  }

  const fieldError = (key: string, msg: MessageKey | null) =>
    msg && (
      <StatusBanner variant="error" size="compact" id={`${id}-${key}-error`}>
        {t(msg)}
      </StatusBanner>
    );
  const described = (key: string, msg: MessageKey | null, hint?: string) =>
    [msg ? `${id}-${key}-error` : null, hint ?? null].filter(Boolean).join(" ") || undefined;

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("notlisted.title")}</StepHeading>
      <StatusBanner
        variant="info"
        title={name ? t("notlisted.banner_title", { hospital: name }) : t("notlisted.banner_title_plain")}
      >
        <p>{t("notlisted.banner_body")}</p>
      </StatusBanner>

      <ol className="paths">
        <li>
          <h3>{t("notlisted.step1_title")}</h3>
          {liveMode ? (
            <form onSubmit={readLink} noValidate>
              <div className="form-field mt-0">
                <label htmlFor={`${id}-url`}>{t("notlisted.url_label")}</label>
                <input
                  id={`${id}-url`}
                  className="field-input"
                  type="url"
                  inputMode="url"
                  autoComplete="off"
                  spellCheck={false}
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  aria-invalid={urlError ? true : undefined}
                  aria-describedby={described("url", urlError, `${id}-url-hint`)}
                />
                <p className="hint" id={`${id}-url-hint`}>
                  {t("notlisted.url_hint")}
                </p>
                {fieldError("url", urlError)}
              </div>
              <Button type="submit" variant="coral">
                {t("notlisted.read_link")}
              </Button>
            </form>
          ) : (
            <p className="mt-0 mb-2">{t("notlisted.upload_only")}</p>
          )}

          {liveMode && <p className="mt-4 mb-2 font-medium">{t("notlisted.or")}</p>}
          <Button
            ref={uploadButton}
            variant={liveMode ? "ghost" : "coral"}
            onClick={() => fileInput.current?.click()}
            aria-describedby={`${id}-upload-hint`}
          >
            <FileUp aria-hidden="true" />
            {t("notlisted.upload")}
          </Button>
          <p className="hint" id={`${id}-upload-hint`}>
            {t("notlisted.upload_hint")}
          </p>
          <input
            ref={fileInput}
            type="file"
            accept={PDF_ACCEPT}
            hidden
            tabIndex={-1}
            onChange={(e) => {
              takeFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />
          {fileError && (
            <StatusBanner variant="error" size="compact">
              {t(fileError)}
            </StatusBanner>
          )}
        </li>

        <li>
          <h3>{t("notlisted.step2_title")}</h3>
          <ul className="find-list">
            <li>{t("notlisted.find_search", { hospital: name || t("notlisted.your_hospital") })}</li>
            <li>{t("notlisted.find_billing")}</li>
            <li>{t("notlisted.find_call")}</li>
          </ul>
        </li>

        <li>
          <h3>{t("notlisted.step3_title")}</h3>
          <p className="m-0">
            {t("notlisted.dollarfor_body")}{" "}
            <a className="text-link" href={DOLLAR_FOR_URL} target="_blank" rel="noopener noreferrer">
              {t("notlisted.dollarfor_link")}
              <span className="sr-only"> {t("result.new_tab")}</span>
            </a>
          </p>
        </li>
      </ol>

      <section className="manual-limits" aria-labelledby={`${id}-manual-title`}>
        <h3 id={`${id}-manual-title`} ref={manualHeading} tabIndex={-1}>
          {t("notlisted.manual_title")}
        </h3>
        <p className="hint mt-0">{t("notlisted.manual_sub")}</p>
        <form onSubmit={submitLimits} noValidate>
          <div className="form-field">
            <label htmlFor={`${id}-name`}>{t("notlisted.manual_hospital")}</label>
            <input
              id={`${id}-name`}
              className="field-input"
              autoComplete="off"
              maxLength={200}
              value={hospital}
              onChange={(e) => setHospital(e.target.value)}
              aria-invalid={nameError ? true : undefined}
              aria-describedby={described("name", nameError)}
            />
            {fieldError("name", nameError)}
          </div>
          <div className="form-field">
            <label htmlFor={`${id}-state`}>{t("notlisted.manual_state")}</label>
            <input
              id={`${id}-state`}
              className="field-input state-input"
              autoComplete="off"
              maxLength={2}
              value={state}
              onChange={(e) => setState(e.target.value.toUpperCase().replace(/[^A-Z]/g, ""))}
              aria-invalid={stateError ? true : undefined}
              aria-describedby={described("state", stateError, `${id}-state-hint`)}
            />
            <p className="hint" id={`${id}-state-hint`}>
              {t("live.state_hint")}
            </p>
            {fieldError("state", stateError)}
          </div>
          <div className="form-field">
            <label htmlFor={`${id}-free`}>{t("notlisted.manual_free")}</label>
            <input
              id={`${id}-free`}
              className="field-input percent-input"
              inputMode="decimal"
              autoComplete="off"
              maxLength={6}
              value={free}
              onChange={(e) => setFree(e.target.value)}
              aria-invalid={freeError ? true : undefined}
              aria-describedby={described("free", freeError, `${id}-free-hint`)}
            />
            <p className="hint" id={`${id}-free-hint`}>
              {t("notlisted.manual_free_hint")}
            </p>
            {fieldError("free", freeError)}
          </div>
          <div className="form-field">
            <label htmlFor={`${id}-discount`}>{t("notlisted.manual_discount")}</label>
            <input
              id={`${id}-discount`}
              className="field-input percent-input"
              inputMode="decimal"
              autoComplete="off"
              maxLength={6}
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
              aria-invalid={discountError ? true : undefined}
              aria-describedby={described("discount", discountError, `${id}-discount-hint`)}
            />
            <p className="hint" id={`${id}-discount-hint`}>
              {t("notlisted.manual_discount_hint")}
            </p>
            {fieldError("discount", discountError)}
          </div>
          <div className="btn-row">
            <Button type="submit">{t("notlisted.manual_submit")}</Button>
            <Button type="button" variant="ghost" onClick={onBack}>
              {t("notlisted.back")}
            </Button>
          </div>
        </form>
      </section>
    </StepCard>
  );
}
