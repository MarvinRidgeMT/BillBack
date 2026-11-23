"use client";

import { useEffect, useId, useState } from "react";
import { CircleCheck, TriangleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import type { ApiError } from "@/lib/api";
import { apiErrorText, asApiError } from "@/lib/errorText";
import { liveActions, type LiveAction } from "@/lib/errors";
import { describeGrounded, GROUNDED_FIELDS, problemKeys, type GroundedName } from "@/lib/grounded";
import { useT, type MessageKey } from "@/lib/i18n";
import type { GroundedField, Hospital, PolicyReadData } from "@/lib/types";
import { checkState } from "@/lib/validation";
import type { PolicyInput } from "./NotListed";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const FIELD_LABELS: Record<GroundedName, MessageKey> = {
  free_care: "live.field.free_care",
  discount: "live.field.discount",
  asset_test: "live.field.asset_test",
  residency: "live.field.residency",
  application_window: "live.field.application_window",
};
/** Typed limits only have these two; the rest would just say "not stated". */
const MANUAL_FIELDS: readonly GroundedName[] = ["free_care", "discount"];

type State = { phase: "loading" } | { phase: "ready"; data: PolicyReadData } | { phase: "error"; error: ApiError };

interface LivePolicyStepProps {
  entrance: Entrance;
  reduce: boolean;
  /** The read already in flight, started by Flow. */
  reading: Promise<PolicyReadData>;
  kind: PolicyInput["kind"];
  /** Name and state from the bill, used when the policy doesn't say. */
  fallbackName: string;
  fallbackState: string | null;
  onContinue: (hospital: Hospital) => void;
  onAction: (action: LiveAction) => void;
  onBack: () => void;
}

export function LivePolicyStep(props: LivePolicyStepProps) {
  const { entrance, reduce, reading, kind, onAction } = props;
  const t = useT();
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    let live = true;
    reading.then(
      (data) => live && setState({ phase: "ready", data }),
      (err: unknown) => live && setState({ phase: "error", error: asApiError(err) }),
    );
    return () => {
      live = false;
    };
  }, [reading]);

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      {state.phase !== "ready" && <StepHeading key="reading">{t("live.reading_title")}</StepHeading>}
      {state.phase === "loading" && (
        <p className="status-line" role="status">
          <span className="pulse-dot" aria-hidden="true" />
          <span>{t("live.reading_status")}</span>
        </p>
      )}
      {state.phase === "error" && <LiveErrorBanner error={state.error} kind={kind} onAction={onAction} />}
      {state.phase === "ready" && <Found {...props} data={state.data} />}
    </StepCard>
  );
}

const ACTION_LABELS: Record<LiveAction, MessageKey> = {
  upload: "live.action.upload",
  manual: "live.action.manual",
  retry: "live.action.retry",
};

interface LiveErrorBannerProps {
  error: ApiError;
  kind: PolicyInput["kind"];
  onAction: (action: LiveAction) => void;
}

/** A failed policy read, translated by code, with the paths forward that fit that code. */
export function LiveErrorBanner({ error, kind, onAction }: LiveErrorBannerProps) {
  const t = useT();
  // Typed limits that were rejected go back to the limits form; there is nothing to upload or retry.
  const actions = kind === "manual" && error.code === "invalid_input" ? (["manual"] as LiveAction[]) : liveActions(error.code);
  const label = (a: LiveAction): string =>
    a === "upload" && kind === "file" ? t("notlisted.upload") : t(ACTION_LABELS[a]);
  return (
    <StatusBanner
      variant="error"
      title={t("live.error_title")}
      focusOnMount
      actions={actions.map((a, i) => (
        <Button key={a} variant={i === 0 ? "default" : "ghost"} onClick={() => onAction(a)}>
          {label(a)}
        </Button>
      ))}
    >
      <p>{apiErrorText(error, t)}</p>
    </StatusBanner>
  );
}

function Found({ data, fallbackName, fallbackState, onContinue, onBack }: LivePolicyStepProps & { data: PolicyReadData }) {
  const t = useT();
  const id = useId();
  const manual = data.source === "manual";
  const shown = manual ? MANUAL_FIELDS : GROUNDED_FIELDS;
  const toCheck = shown.filter((n) => data.grounded[n].needs_checking);
  const knownState = data.state ?? checkState(fallbackState ?? "");
  const [stateInput, setStateInput] = useState("");
  const [stateTried, setStateTried] = useState(false);
  const typedState = checkState(stateInput);
  const stateError = !knownState && stateTried && !typedState;

  function next() {
    const state = knownState ?? typedState;
    if (!state) {
      setStateTried(true);
      document.getElementById(`${id}-state`)?.focus();
      return;
    }
    onContinue({ slug: data.slug, name: data.hospital_name || fallbackName, state });
  }

  const note =
    data.source === "live"
      ? { title: t("live.read_now_title"), body: t("live.read_now_body") }
      : { title: undefined, body: t(manual ? "live.manual_note" : "live.curated_note") };

  return (
    <>
      <StepHeading key="found">{manual ? t("live.manual_title") : t("live.found_title")}</StepHeading>
      <p className="sub">
        <strong>{data.hospital_name || fallbackName}</strong>
        {data.source === "live" && data.seconds > 0 && <> · {t("live.seconds", { seconds: data.seconds.toFixed(1) })}</>}
      </p>
      <StatusBanner variant="info" title={note.title}>
        <p>{note.body}</p>
      </StatusBanner>
      {toCheck.length > 0 && (
        <StatusBanner
          variant="warning"
          title={toCheck.length === 1 ? t("live.check_title_one") : t("live.check_title_many", { n: toCheck.length })}
        >
          <p>{t("live.check_body")}</p>
        </StatusBanner>
      )}

      <div className="grounded">
        {shown.map((name) => (
          <GroundedRow key={name} name={name} field={data.grounded[name]} manual={manual} />
        ))}
      </div>

      {!knownState && (
        <div className="form-field">
          <label htmlFor={`${id}-state`}>{t("live.state_label")}</label>
          <input
            id={`${id}-state`}
            className="field-input state-input"
            autoComplete="off"
            maxLength={2}
            value={stateInput}
            onChange={(e) => setStateInput(e.target.value.toUpperCase().replace(/[^A-Z]/g, ""))}
            aria-invalid={stateError || undefined}
            aria-describedby={stateError ? `${id}-state-error ${id}-state-hint` : `${id}-state-hint`}
          />
          <p className="hint" id={`${id}-state-hint`}>
            {t("live.state_hint")}
          </p>
          {stateError && (
            <StatusBanner variant="error" size="compact" id={`${id}-state-error`}>
              {t("live.state_error")}
            </StatusBanner>
          )}
        </div>
      )}

      <div className="btn-row">
        <Button variant="coral" onClick={next}>
          {t("live.continue")}
        </Button>
        <Button variant="ghost" onClick={onBack}>
          {t("notlisted.back")}
        </Button>
      </div>
    </>
  );
}

/** One policy fact: in plain words, the sentence it came from (with its page), and whether to check it. */
function GroundedRow({ name, field, manual }: { name: GroundedName; field: GroundedField; manual: boolean }) {
  const t = useT();
  const id = useId();
  const described = describeGrounded(name, field.value, field.status);
  const quote = field.source_quote.trim();
  const reasons = problemKeys(field.problems);
  const check = field.needs_checking;
  return (
    <div className="grounded-row" data-check={check || undefined} aria-labelledby={`${id}-label`} role="group">
      <div className="g-head">
        <span className="g-label" id={`${id}-label`}>
          {t(FIELD_LABELS[name])}
        </span>
        {check ? (
          <span className="badge">
            <TriangleAlert size={14} aria-hidden="true" />
            {t("live.needs_checking")}
          </span>
        ) : (
          !manual &&
          quote && (
            <span className="badge" data-tone="ok">
              <CircleCheck size={14} aria-hidden="true" />
              {t("live.found_in_policy")}
            </span>
          )
        )}
      </div>
      <p className="g-value">{t(described.key, described.vars)}</p>
      {manual ? (
        <p className="g-source">{t("live.you_entered")}</p>
      ) : quote ? (
        <figure className="g-quote">
          <figcaption>
            {typeof field.page === "number" ? t("live.quote_page", { page: field.page }) : t("live.quote_no_page")}
          </figcaption>
          <blockquote lang="en">{`“${quote}”`}</blockquote>
        </figure>
      ) : (
        <p className="g-source">{t("live.no_quote")}</p>
      )}
      {check && reasons.length > 0 && (
        <ul className="g-problems">
          {reasons.map((k) => (
            <li key={k}>{t(k)}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
