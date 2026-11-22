"use client";

import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { hospitalBySlug, NOT_LISTED } from "@/lib/hospitals";
import { useT, type MessageKey } from "@/lib/i18n";
import { FIELD_NAMES, type ConfirmedBill, type FieldName } from "@/lib/types";
import { HospitalSelect } from "./HospitalSelect";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const EMPTY = Object.fromEntries(FIELD_NAMES.map((n) => [n, ""])) as Record<FieldName, string>;
const HINTS: Partial<Record<FieldName, MessageKey>> = {
  amount_due: "manual.amount_hint",
  service_date: "manual.date_hint",
};

interface ManualEntryProps {
  entrance: Entrance;
  reduce: boolean;
  onConfirm: (bill: ConfirmedBill) => void;
  onBack: () => void;
  onStartOver: () => void;
}

/** Same card as the reading screen, but the patient types the five fields. Nothing is prefilled or pre-chosen. */
export function ManualEntry({ entrance, reduce, onConfirm, onBack, onStartOver }: ManualEntryProps) {
  const t = useT();
  const baseId = useId();
  const [fields, setFields] = useState(EMPTY);
  const [hospital, setHospital] = useState("");
  const [showRequired, setShowRequired] = useState(false);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const chosen = hospitalBySlug(hospital);
    if (!chosen) {
      setShowRequired(true);
      return;
    }
    const trimmed = Object.fromEntries(FIELD_NAMES.map((n) => [n, fields[n].trim()])) as Record<FieldName, string>;
    onConfirm({ fields: trimmed, hospital: chosen });
  }

  return (
    <StepCard step={2} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("manual.title")}</StepHeading>
      <p className="sub">{t("manual.sub")}</p>

      <form onSubmit={submit} noValidate>
        {FIELD_NAMES.map((name) => {
          const id = `${baseId}-${name}`;
          const hint = HINTS[name];
          return (
            <div className="form-field" key={name}>
              <label htmlFor={id}>{t(`field.${name}`)}</label>
              <input
                id={id}
                className="field-input"
                value={fields[name]}
                onChange={(e) => setFields((prev) => ({ ...prev, [name]: e.target.value }))}
                placeholder={hint ? t(hint) : undefined}
                inputMode={name === "amount_due" ? "decimal" : undefined}
                autoComplete="off"
              />
            </div>
          );
        })}

        <HospitalSelect
          value={hospital}
          onChange={(v) => {
            setHospital(v);
            setShowRequired(false);
          }}
          matched={false}
          showRequired={showRequired}
        />

        <div className="btn-row">
          {hospital === NOT_LISTED ? (
            <Button type="button" variant="ghost" onClick={onStartOver}>
              {t("result.start_over")}
            </Button>
          ) : (
            <Button type="submit">{t("manual.next")}</Button>
          )}
          <Button type="button" variant="ghost" onClick={onBack}>
            {t("manual.back")}
          </Button>
        </div>
      </form>
    </StepCard>
  );
}
