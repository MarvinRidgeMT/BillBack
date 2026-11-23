"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { NOT_LISTED } from "@/lib/hospitals";
import { useT, type MessageKey } from "@/lib/i18n";
import { FIELD_NAMES, type ConfirmedBill, type FieldName, type ManualInitial } from "@/lib/types";
import { HospitalSearch, type HospitalPick } from "./HospitalSearch";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const EMPTY = Object.fromEntries(FIELD_NAMES.map((n) => [n, ""])) as Record<FieldName, string>;
const HINTS: Partial<Record<FieldName, MessageKey>> = {
  amount_due: "manual.amount_hint",
  service_date: "manual.date_hint",
};

interface ManualEntryProps {
  entrance: Entrance;
  reduce: boolean;
  /**
   * What we already read from the photo (when the patient left the reading screen). Every field is filled in;
   * the ones we weren't sure about are highlighted. Without it the form starts empty.
   */
  initial?: ManualInitial | null;
  onConfirm: (bill: ConfirmedBill) => void;
  /** The hospital isn't one we know: go find its policy, keeping these fields. */
  onNotListed: (fields: Record<FieldName, string>) => void;
  onBack: () => void;
}

/** Same card as the reading screen, but the patient types (or fixes) the five fields. */
export function ManualEntry({ entrance, reduce, initial, onConfirm, onNotListed, onBack }: ManualEntryProps) {
  const t = useT();
  const baseId = useId();
  const [fields, setFields] = useState<Record<FieldName, string>>(() => ({ ...EMPTY, ...initial?.fields }));
  const [hospital, setHospital] = useState<HospitalPick>(initial?.hospital ?? null);
  const [showRequired, setShowRequired] = useState(false);
  const low = new Set(initial?.lowConfidence ?? []);
  const prefilled = !!initial && FIELD_NAMES.some((n) => initial.fields[n]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = Object.fromEntries(FIELD_NAMES.map((n) => [n, fields[n].trim()])) as Record<FieldName, string>;
    if (hospital === NOT_LISTED) {
      onNotListed(trimmed);
      return;
    }
    if (!hospital) {
      setShowRequired(true);
      return;
    }
    onConfirm({ fields: trimmed, hospital });
  }

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("manual.title")}</StepHeading>
      {prefilled ? (
        <StatusBanner variant="info" title={t("manual.prefilled_title")}>
          <p>{t("manual.prefilled_body")}</p>
        </StatusBanner>
      ) : (
        <p className="sub">{t("manual.sub")}</p>
      )}

      <form onSubmit={submit} noValidate>
        {FIELD_NAMES.map((name) => {
          const id = `${baseId}-${name}`;
          const hint = HINTS[name];
          const check = low.has(name);
          return (
            <div className={check ? "form-field check" : "form-field"} key={name}>
              <label htmlFor={id}>{t(`field.${name}`)}</label>
              <input
                id={id}
                className="field-input"
                value={fields[name]}
                onChange={(e) => setFields((prev) => ({ ...prev, [name]: e.target.value }))}
                placeholder={hint ? t(hint) : undefined}
                inputMode={name === "amount_due" ? "decimal" : undefined}
                aria-describedby={check ? `${id}-check` : undefined}
                autoComplete="off"
              />
              {check && (
                <span className="check-note" id={`${id}-check`}>
                  {t("manual.check_this")}
                </span>
              )}
            </div>
          );
        })}

        <HospitalSearch
          value={hospital}
          onChange={(v) => {
            setHospital(v);
            setShowRequired(false);
          }}
          matched={false}
          showRequired={showRequired}
        />

        <div className="btn-row">
          <Button type="submit" variant={hospital === NOT_LISTED ? "coral" : "default"}>
            {hospital === NOT_LISTED ? t("reading.find_policy") : t("manual.next")}
          </Button>
          <Button type="button" variant="ghost" onClick={onBack}>
            {t("manual.back")}
          </Button>
        </div>
      </form>
    </StepCard>
  );
}
