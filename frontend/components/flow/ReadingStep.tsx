"use client";

import { useEffect, useId, useState } from "react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { ApiError, DEMO_MODE } from "@/lib/api";
import { confidencePercent, displayField } from "@/lib/format";
import { hospitalBySlug, matchHospital, NOT_LISTED } from "@/lib/hospitals";
import { useI18n, type Translate } from "@/lib/i18n";
import { SOFT } from "@/lib/motion";
import {
  CONFIRM_THRESHOLD,
  FIELD_NAMES,
  type BillReadData,
  type ConfirmedBill,
  type FieldName,
} from "@/lib/types";
import { HospitalSelect } from "./HospitalSelect";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const REVEAL_GAP_S = 0.42;
const AFTER_REVEAL_MS = 450;

type State =
  | { phase: "loading" }
  | { phase: "ready"; data: BillReadData }
  | { phase: "error"; error: ApiError };

interface ReadingStepProps {
  entrance: Entrance;
  reduce: boolean;
  /** The bill read already in flight. Started by Flow, so it runs once per attempt. */
  reading: Promise<BillReadData>;
  /** True when this is the labeled sample, not the patient's bill. */
  sample: boolean;
  onConfirm: (bill: ConfirmedBill) => void;
  onRetry: () => void;
  onManual: () => void;
  onSample: () => void;
  onStartOver: () => void;
}

export function ReadingStep(props: ReadingStepProps) {
  const { entrance, reduce, reading, sample, onRetry, onManual, onSample } = props;
  const { t } = useI18n();
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    let live = true;
    reading.then(
      (data) => live && setState({ phase: "ready", data }),
      (err: unknown) =>
        live && setState({ phase: "error", error: err instanceof ApiError ? err : new ApiError("failed", null) }),
    );
    return () => {
      live = false;
    };
  }, [reading]);

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      {sample && <p className="banner">{t("reading.sample_banner")}</p>}
      <StepHeading>{t(state.phase === "ready" ? "reading.found_title" : "reading.title")}</StepHeading>
      {/* Always here, so a screen reader hears the change from "reading" to what was found. */}
      <p className="sr-only" role="status">
        {state.phase === "loading" && t("reading.status")}
        {state.phase === "ready" && foundSummary(state.data, t)}
      </p>

      {state.phase === "loading" && (
        <p className="status-line" aria-hidden="true">
          <span className="pulse-dot" aria-hidden="true" />
          <span>{t("reading.status")}</span>
        </p>
      )}

      {state.phase === "error" && (
        <>
          <p className="error-text" role="alert">
            {state.error.kind === "rejected" && state.error.message
              ? state.error.message
              : t("error.read_generic")}
          </p>
          <div className="btn-row">
            <Button onClick={onRetry}>{t("error.try_again")}</Button>
            <Button variant="ghost" onClick={onManual}>
              {t("upload.manual")}
            </Button>
            {DEMO_MODE && state.error.kind !== "rejected" && (
              <Button variant="ghost" onClick={onSample}>
                {t("reading.see_sample")}
              </Button>
            )}
          </div>
        </>
      )}

      {state.phase === "ready" && <Confirm {...props} data={state.data} />}
    </StepCard>
  );
}

function needsCheck(data: BillReadData, name: FieldName): boolean {
  return data.fields_to_confirm.includes(name) || data.fields[name].confidence < CONFIRM_THRESHOLD;
}

/** "Done in 2.6 seconds. One detail needs your eyes." */
function foundSummary(data: BillReadData, t: Translate): string {
  const count = FIELD_NAMES.filter((name) => needsCheck(data, name)).length;
  const done = t("reading.done", { seconds: data.seconds.toFixed(1) });
  if (count === 0) return done;
  return `${done} ${count === 1 ? t("reading.needs_one") : t("reading.needs_many", { n: count })}`;
}

/** The five fields, revealed one by one, with anything under 80% sure handed to the patient to fix. */
function Confirm({
  data,
  reduce,
  onConfirm,
  onStartOver,
}: ReadingStepProps & { data: BillReadData }) {
  const { t, lang } = useI18n();
  const baseId = useId();
  const locale = lang === "es" ? "es-US" : "en-US";


  const [edits, setEdits] = useState<Partial<Record<FieldName, string>>>({});
  // Rows the patient opened with "Edit". Rows under 80% sure are open from the start.
  const [opened, setOpened] = useState<Partial<Record<FieldName, boolean>>>({});
  const [revealed, setRevealed] = useState(reduce);
  const [guess, setGuess] = useState(() => matchHospital(data.fields.hospital_name.value));
  const [hospital, setHospital] = useState(guess?.slug ?? "");
  // True once the patient has picked a hospital themselves. Their pick is never overwritten.
  const [chosenByPatient, setChosenByPatient] = useState(false);
  const [showRequired, setShowRequired] = useState(false);

  useEffect(() => {
    if (reduce) return;
    const ms = FIELD_NAMES.length * REVEAL_GAP_S * 1000 + AFTER_REVEAL_MS;
    const timer = window.setTimeout(() => setRevealed(true), ms);
    return () => window.clearTimeout(timer);
  }, [reduce]);

  function edit(name: FieldName, value: string) {
    setEdits((prev) => ({ ...prev, [name]: value }));
    // A corrected hospital name can point at a different policy, so our guess follows it.
    if (name === "hospital_name") {
      const next = matchHospital(value);
      setGuess(next);
      if (!chosenByPatient) setHospital(next?.slug ?? "");
    }
  }

  const valueOf = (name: FieldName) => edits[name] ?? displayField(name, data.fields[name], locale);

  function confirm() {
    const chosen = hospitalBySlug(hospital);
    if (!chosen) {
      setShowRequired(true);
      return;
    }
    const fields = Object.fromEntries(FIELD_NAMES.map((n) => [n, valueOf(n).trim()])) as Record<FieldName, string>;
    onConfirm({ fields, hospital: chosen });
  }

  return (
    <>
      <p className="status-line" aria-hidden="true">
        {revealed ? (
          <span>{foundSummary(data, t)}</span>
        ) : (
          <>
            <span className="pulse-dot" aria-hidden="true" />
            <span>{t("reading.status")}</span>
          </>
        )}
      </p>

      <div>
        {FIELD_NAMES.map((name, i) => {
          const field = data.fields[name];
          const check = needsCheck(data, name);
          const id = `${baseId}-${name}`;
          const shown = valueOf(name);
          return (
            <motion.div
              key={name}
              className={check ? "field-row check" : "field-row"}
              initial={reduce ? false : { opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...SOFT, delay: (i + 1) * REVEAL_GAP_S }}
            >
              {check || opened[name] ? (
                <>
                  <label className="k" htmlFor={id}>
                    {t(`field.${name}`)}
                    {check && <> · {t("reading.check_suffix")}</>}
                  </label>
                  <input
                    id={id}
                    className="field-input v"
                    value={shown}
                    onChange={(e) => edit(name, e.target.value)}
                    aria-describedby={check && field.note ? `${id}-note` : undefined}
                    autoComplete="off"
                    // Opened by the patient pressing Edit, so the cursor follows them there.
                    autoFocus={!check}
                  />
                </>
              ) : (
                <>
                  <span className="k">{t(`field.${name}`)}</span>
                  <span className="v">{shown || t("reading.not_found")}</span>
                </>
              )}
              <span className="chip">{t("reading.sure", { pct: confidencePercent(field.confidence) })}</span>
              {!check && !opened[name] && (
                <button
                  type="button"
                  className="edit-btn"
                  aria-label={t("reading.edit_field", { field: t(`field.${name}`) })}
                  onClick={() => setOpened((prev) => ({ ...prev, [name]: true }))}
                >
                  {t("reading.edit")}
                </button>
              )}
              {check && field.note && (
                <span className="note" id={`${id}-note`} lang={lang === "es" ? "en" : undefined}>
                  {field.note}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>

      <motion.div
        initial={reduce ? false : { opacity: 0 }}
        animate={{ opacity: revealed ? 1 : 0 }}
        transition={{ duration: 0.5 }}
        inert={!revealed}
      >
        <HospitalSelect
          value={hospital}
          onChange={(v) => {
            setHospital(v);
            setChosenByPatient(true);
            setShowRequired(false);
          }}
          matched={!chosenByPatient && hospital !== "" && hospital === guess?.slug}
          showRequired={showRequired}
        />
        <div className="btn-row">
          {hospital === NOT_LISTED ? (
            <Button variant="ghost" onClick={onStartOver}>
              {t("result.start_over")}
            </Button>
          ) : (
            <Button variant="coral" onClick={confirm}>
              {t("reading.ok")}
            </Button>
          )}
        </div>
      </motion.div>
    </>
  );
}
