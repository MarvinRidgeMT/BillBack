"use client";

import { useId, useState } from "react";
import { ChevronDown } from "lucide-react";
import { useT } from "@/lib/i18n";
import { NOT_LISTED, useHospitals, useLiveMode } from "@/lib/hospitals";

const DOLLAR_FOR_URL = "https://dollarfor.org";

interface HospitalSelectProps {
  /** A hospital slug, NOT_LISTED, or "" when the patient hasn't chosen. */
  value: string;
  onChange: (value: string) => void;
  /** True when the current value is our guess from the bill, so we say so. */
  matched: boolean;
  /** True when we tried to match the bill's hospital and found nothing close enough. */
  matchFailed?: boolean;
  /** True when the patient tried to continue without choosing. */
  showRequired: boolean;
}

/** "Which hospital is this?" The patient always has the last word, and can say it isn't listed. */
export function HospitalSelect({ value, onChange, matched, matchFailed = false, showRequired }: HospitalSelectProps) {
  const t = useT();
  const id = useId();
  const hintId = `${id}-hint`;
  const unlisted = value === NOT_LISTED;
  const hospitals = useHospitals();
  const liveMode = useLiveMode();
  const [changing, setChanging] = useState(false);
  const current = hospitals.find((h) => h.slug === value);

  if (matched && current && !changing) {
    return (
      <div className="form-field">
        <p className="match-line" aria-live="polite">
          {t("hospital.we_think")} <strong>{current.name}</strong>
          {current.state ? ` (${current.state})` : ""}
          {" — "}
          <button type="button" className="text-link inline-btn" onClick={() => setChanging(true)}>
            {t("hospital.change")}
          </button>
        </p>
      </div>
    );
  }

  return (
    <div className="form-field">
      <label htmlFor={id}>{t("hospital.label")}</label>
      <div className="select-wrap">
        <select
          id={id}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          aria-describedby={hintId}
          aria-invalid={showRequired && value === "" ? true : undefined}
          autoFocus={changing}
        >
          <option value="" disabled>
            {t("hospital.placeholder")}
          </option>
          {hospitals.map((h) => (
            <option key={h.slug} value={h.slug}>
              {h.name}
              {h.state ? ` (${h.state})` : ""}
            </option>
          ))}
          <option value={NOT_LISTED}>{t("hospital.not_listed")}</option>
        </select>
        <ChevronDown size={20} aria-hidden="true" />
      </div>

      <div id={hintId} aria-live="polite">
        {showRequired && value === "" ? (
          <p className="error-text">{t("hospital.required")}</p>
        ) : unlisted ? (
          <p className="info-text">
            {liveMode ? t("hospital.paste_link_beta") : t("hospital.add_soon")} {t("hospital.unlisted")}{" "}
            <a className="text-link" href={DOLLAR_FOR_URL} target="_blank" rel="noopener noreferrer">
              {t("hospital.dollarfor")}
              <span className="sr-only"> {t("result.new_tab")}</span>
            </a>
          </p>
        ) : value === "" && matchFailed ? (
          <p className="hint">{t("hospital.no_match")}</p>
        ) : value === "" ? (
          <p className="hint">{t("hospital.pick_hint")}</p>
        ) : null}
      </div>
    </div>
  );
}
