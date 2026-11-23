"use client";

import { useEffect, useId, useState } from "react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { ApiError, DEMO_MODE } from "@/lib/api";
import { asApiError } from "@/lib/errorText";
import { confidencePercent, displayField } from "@/lib/format";
import { fieldsToCheck } from "@/lib/grounded";
import { matchHospital, NOT_LISTED } from "@/lib/hospitals";
import { useI18n, type Lang, type MessageKey, type Translate } from "@/lib/i18n";
import { SOFT } from "@/lib/motion";
import {
  FIELD_NAMES,
  type BillReadData,
  type ConfirmedBill,
  type FieldName,
  type ManualInitial,
} from "@/lib/types";
import { HospitalSearch, type HospitalPick } from "./HospitalSearch";
import { BlurryBanner, ReadErrorBanner, UnreadableBanner } from "./ReadingBanners";
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
  /** The hospital isn't one we know: go find its policy, keeping the confirmed bill fields. */
  onNotListed: (fields: Record<FieldName, string>) => void;
  onRetry: () => void;
  /** Back to the upload card, for a new photo or another file. */
  onRetake: () => void;
  /** To the manual form, prefilled with whatever was read. */
  onManual: (initial?: ManualInitial) => void;
  onSample: () => void;
}

const localeOf = (lang: Lang) => (lang === "es" ? "es-US" : "en-US");

/** Everything the reader found, as text the patient can edit, and which fields need their eyes. */
export function manualInitialFrom(data: BillReadData, lang: Lang): ManualInitial {
  const fields = Object.fromEntries(
    FIELD_NAMES.map((n) => [n, displayField(n, data.fields[n], localeOf(lang))]),
  ) as Record<FieldName, string>;
  const lowConfidence = fieldsToCheck(FIELD_NAMES, data.fields, [...data.fields_to_confirm, ...data.weak_fields]);
  return { fields, lowConfidence };
}

export function ReadingStep(props: ReadingStepProps) {
  const { entrance, reduce, reading, sample, onRetry, onRetake, onManual, onSample } = props;
  const { t, lang } = useI18n();
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

  // An unreadable photo keeps the "Reading" heading, so focus goes to the banner that explains it.
  const checking = state.phase === "ready" && !state.data.unreadable;

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      {sample && (
        <StatusBanner variant="info" title={t("reading.sample_title")}>
          <p>{t("reading.sample_banner")}</p>
        </StatusBanner>
      )}
      <StepHeading key={checking ? "check" : "reading"}>
        {checking ? t("reading.check_title") : t("reading.title")}
      </StepHeading>

      {state.phase === "loading" && (
        <p className="status-line" role="status">
          <span className="pulse-dot" aria-hidden="true" />
          <span>{t("reading.status")}</span>
        </p>
      )}

      {state.phase === "error" && (
        <ReadErrorBanner
          error={state.error}
          onRetry={onRetry}
          onRetake={onRetake}
          onManual={() => onManual()}
          onSample={DEMO_MODE && state.error.kind === "unavailable" ? onSample : undefined}
        />
      )}

      {state.phase === "ready" && state.data.unreadable && (
        <UnreadableBanner
          reasons={state.data.quality.reasons}
          onRetake={onRetake}
          onManual={() => onManual(manualInitialFrom(state.data, lang))}
        />
      )}

      {checking && <Confirm {...props} data={state.data} />}
    </StepCard>
  );
}

/** Reader notes come from backend code in English. Known ones are shown in the patient's language. */
const KNOWN_NOTES: Record<string, MessageKey> = {
  "account number should be 4-30 letters, digits or dashes": "note.account_format",
};
function noteText(note: string, t: Translate): string {
  const key = KNOWN_NOTES[note.trim().toLowerCase()];
  return key ? t(key) : note;
}

/** The five fields, revealed one by one, with anything under 80% sure handed to the patient to fix. */
function Confirm({
  data,
  reduce,
  onConfirm,
  onNotListed,
}: ReadingStepProps & { data: BillReadData }) {
  const { t, lang } = useI18n();
  const baseId = useId();
  const locale = localeOf(lang);

  const toCheck = fieldsToCheck(FIELD_NAMES, data.fields, [...data.fields_to_confirm, ...data.weak_fields]);
  const needsCheck = (name: FieldName) => toCheck.includes(name);

  const [edits, setEdits] = useState<Partial<Record<FieldName, string>>>({});
  const [revealed, setRevealed] = useState(reduce);
  const [guess, setGuess] = useState<HospitalPick>(null);
  const [matchDone, setMatchDone] = useState(false);
  const [hospital, setHospital] = useState<HospitalPick>(null);
  // True once the patient has picked a hospital themselves. Their pick is never overwritten.
  const [chosenByPatient, setChosenByPatient] = useState(false);
  const [showRequired, setShowRequired] = useState(false);
  const [editing, setEditing] = useState<ReadonlySet<FieldName>>(new Set());
  const [confirmed, setConfirmed] = useState<ReadonlySet<FieldName>>(new Set());
  const unresolved = toCheck.filter((n) => !confirmed.has(n) && edits[n] === undefined);

  const startEditing = (name: FieldName) => setEditing((prev) => new Set([...prev, name]));
  const markConfirmed = (name: FieldName) => setConfirmed((prev) => new Set([...prev, name]));

  // Ask the backend which cached policy this bill belongs to. Only a preselection: the patient can change it.
  useEffect(() => {
    let live = true;
    matchHospital(data.fields.hospital_name.value, data.fields.hospital_address.value).then((m) => {
      if (!live) return;
      setGuess(m);
      setMatchDone(true);
      setHospital((current) => (current === null ? m : current));
    });
    return () => {
      live = false;
    };
  }, [data]);

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
      matchHospital(value, valueOf("hospital_address")).then((next) => {
        setGuess(next);
        if (!chosenByPatient) setHospital(next);
      });
    }
  }

  const valueOf = (name: FieldName) => edits[name] ?? displayField(name, data.fields[name], locale);

  function confirm() {
    const fields = Object.fromEntries(FIELD_NAMES.map((n) => [n, valueOf(n).trim()])) as Record<FieldName, string>;
    if (hospital === NOT_LISTED) {
      onNotListed(fields);
      return;
    }
    if (!hospital) {
      setShowRequired(true);
      return;
    }
    onConfirm({ fields, hospital });
  }

  const seconds = data.seconds.toFixed(1);
  const needs =
    toCheck.length === 0
      ? ""
      : toCheck.length === 1
        ? t("reading.needs_one")
        : t("reading.needs_many", { n: toCheck.length });

  const quality = data.quality;
  return (
    <>
      {quality.checked && !quality.ok && <BlurryBanner reasons={quality.reasons} />}
      <p className="status-line" role="status">
        {revealed ? (
          <span>
            {t("reading.done", { seconds })} {needs}
          </span>
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
          const check = needsCheck(name);
          const resolved = !check || confirmed.has(name) || edits[name] !== undefined;
          const open = check || editing.has(name);
          const id = `${baseId}-${name}`;
          const shown = valueOf(name);
          const note = check && field.note ? noteText(field.note, t) : "";
          return (
            <motion.div
              key={name}
              className={check && !resolved ? "field-row check" : check ? "field-row checked" : "field-row"}
              initial={reduce ? false : { opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...SOFT, delay: (i + 1) * REVEAL_GAP_S }}
            >
              {open ? (
                <>
                  <label className="k" htmlFor={id}>
                    {t(`field.${name}`)}
                    {check && !resolved && <> · <strong>{t("reading.check_suffix")}</strong></>}
                  </label>
                  <input
                    id={id}
                    className="field-input v"
                    value={shown}
                    onChange={(e) => edit(name, e.target.value)}
                    aria-describedby={note ? `${id}-note` : undefined}
                    autoComplete="off"
                    autoFocus={!check && editing.has(name)}
                  />
                </>
              ) : (
                <>
                  <span className="k">{t(`field.${name}`)}</span>
                  <span className="v">{shown || t("reading.not_found")}</span>
                </>
              )}
              <span className="chip">{t("reading.sure", { pct: confidencePercent(field.confidence) })}</span>
              {note && (
                <span className="note" id={`${id}-note`}>
                  {note}
                </span>
              )}
              <span className="row-actions">
                {check && !resolved && (
                  <button type="button" className="mini-btn primary" onClick={() => markConfirmed(name)}>
                    {t("reading.its_right")}
                  </button>
                )}
                {check && resolved && <span className="checked-label">✓ {t("reading.checked")}</span>}
                {!check && !editing.has(name) && (
                  <button
                    type="button"
                    className="mini-btn"
                    onClick={() => startEditing(name)}
                    aria-label={`${t("reading.edit")}: ${t(`field.${name}`)}`}
                  >
                    {t("reading.edit")}
                  </button>
                )}
              </span>
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
        <HospitalSearch
          value={hospital}
          onChange={(v) => {
            setHospital(v);
            setChosenByPatient(true);
            setShowRequired(false);
          }}
          matched={
            !chosenByPatient &&
            hospital !== null &&
            hospital !== NOT_LISTED &&
            guess !== null &&
            guess !== NOT_LISTED &&
            hospital.slug === guess.slug
          }
          matchFailed={matchDone && !guess}
          showRequired={showRequired}
        />
        {unresolved.length > 0 && <p className="hint mt-4 mb-0">{t("reading.check_first")}</p>}
        <div className="btn-row">
          <Button variant="coral" onClick={confirm} disabled={unresolved.length > 0}>
            {hospital === NOT_LISTED ? t("reading.find_policy") : t("reading.ok")}
          </Button>
        </div>
      </motion.div>
    </>
  );
}
