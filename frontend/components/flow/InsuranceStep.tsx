"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { confidencePercent } from "@/lib/format";
import { useT, type MessageKey } from "@/lib/i18n";
import {
  CONFIRM_THRESHOLD,
  EOB_FIELD_NAMES,
  type EobDocument,
  type EobFieldName,
  type EobReadData,
} from "@/lib/types";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

type State =
  | { phase: "loading" }
  | { phase: "ready"; data: EobReadData }
  | { phase: "error"; error: ApiError };

interface InsuranceStepProps {
  entrance: Entrance;
  reduce: boolean;
  reading: Promise<EobReadData>;
  sample: boolean;
  onConfirm: (document: EobDocument) => void;
  onRetry: () => void;
  onSkip: () => void;
}

export function InsuranceStep({ entrance, reduce, reading, sample, onConfirm, onRetry, onSkip }: InsuranceStepProps) {
  const t = useT();
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    let live = true;
    reading.then(
      (data) => live && setState({ phase: "ready", data }),
      (error: unknown) =>
        live && setState({ phase: "error", error: error instanceof ApiError ? error : new ApiError("failed", null) }),
    );
    return () => {
      live = false;
    };
  }, [reading]);

  return (
    <StepCard step={3} entrance={entrance} reduce={reduce}>
      {sample && <p className="banner">{t("insurance.sample_banner")}</p>}
      <StepHeading>{state.phase === "ready" ? t("insurance.check_title") : t("insurance.reading_title")}</StepHeading>
      {state.phase === "loading" && (
        <p className="status-line" role="status">
          <span className="pulse-dot" aria-hidden="true" />
          <span>{t("insurance.reading_status")}</span>
        </p>
      )}
      {state.phase === "error" && (
        <>
          <p className="error-text" role="alert">
            {state.error.kind === "rejected" && state.error.message ? state.error.message : t("insurance.read_error")}
          </p>
          <div className="btn-row">
            <Button onClick={onRetry}>{t("error.try_again")}</Button>
            <Button variant="ghost" onClick={onSkip}>{t("insurance.skip")}</Button>
          </div>
        </>
      )}
      {state.phase === "ready" && <ConfirmInsurance data={state.data} onConfirm={onConfirm} onSkip={onSkip} />}
    </StepCard>
  );
}

function normalized(name: EobFieldName, value: string): number | string | null {
  if (name === "service_date") {
    const parsed = new Date(value);
    return Number.isNaN(parsed.valueOf()) ? null : parsed.toISOString().slice(0, 10);
  }
  if (name === "provider") return null;
  const amount = Number(value.replace(/[^0-9.-]/g, ""));
  return Number.isFinite(amount) && amount >= 0 ? Math.round(amount * 100) : null;
}

function ConfirmInsurance({ data, onConfirm, onSkip }: Pick<InsuranceStepProps, "onConfirm" | "onSkip"> & { data: EobReadData }) {
  const t = useT();
  const [document, setDocument] = useState(data.document);
  const [resolved, setResolved] = useState<ReadonlySet<string>>(new Set());
  const needs = (path: string, confidence: number) =>
    data.fields_to_confirm.includes(path) || confidence < CONFIRM_THRESHOLD;
  const unresolved = data.fields_to_confirm.filter((path) => !resolved.has(path));

  function resolve(path: string) {
    setResolved((current) => new Set([...current, path]));
  }

  function editPlan(value: string) {
    setDocument((current) => ({
      ...current,
      plan_name: { ...current.plan_name, value, confidence: 1, note: "confirmed by patient" },
    }));
    resolve("plan_name");
  }

  function editClaim(index: number, name: EobFieldName, value: string) {
    const path = `claims.${index}.${name}`;
    setDocument((current) => ({
      ...current,
      claims: current.claims.map((claim, claimIndex) =>
        claimIndex === index
          ? {
              ...claim,
              [name]: { ...claim[name], value, normalized: normalized(name, value), confidence: 1, note: "confirmed by patient" },
            }
          : claim,
      ),
    }));
    resolve(path);
  }

  return (
    <>
      <p className="sub">{t("insurance.check_sub")}</p>
      <div className={needs("plan_name", document.plan_name.confidence) && !resolved.has("plan_name") ? "field-row check" : "field-row"}>
        <label className="k" htmlFor="eob-plan">{t("insurance.plan")}</label>
        <input id="eob-plan" className="field-input v" value={document.plan_name.value} onChange={(event) => editPlan(event.target.value)} />
        <span className="chip">{t("reading.sure", { pct: confidencePercent(document.plan_name.confidence) })}</span>
        <span className="note">{t("insurance.source", { source: document.plan_name.location || t("insurance.source_missing") })}</span>
        {needs("plan_name", document.plan_name.confidence) && !resolved.has("plan_name") && (
          <span className="row-actions"><button type="button" className="mini-btn primary" onClick={() => resolve("plan_name")}>{t("reading.its_right")}</button></span>
        )}
      </div>

      {document.claims.map((claim, index) => (
        <section className="insurance-claim" key={`${claim.provider.value}-${index}`} aria-labelledby={`claim-${index}`}>
          <h2 id={`claim-${index}`}>{t("insurance.claim", { n: index + 1 })}</h2>
          {EOB_FIELD_NAMES.map((name) => {
            const field = claim[name];
            const path = `claims.${index}.${name}`;
            const check = needs(path, field.confidence) && !resolved.has(path);
            return (
              <div className={check ? "field-row check" : "field-row"} key={name}>
                <label className="k" htmlFor={`eob-${index}-${name}`}>{t(`insurance.field.${name}` as MessageKey)}</label>
                <input
                  id={`eob-${index}-${name}`}
                  className="field-input v"
                  value={field.value}
                  onChange={(event) => editClaim(index, name, event.target.value)}
                />
                <span className="chip">{t("reading.sure", { pct: confidencePercent(field.confidence) })}</span>
                <span className="note">{t("insurance.source", { source: field.location || t("insurance.source_missing") })}</span>
                {field.note && <span className="note">{field.note}</span>}
                {check && (
                  <span className="row-actions"><button type="button" className="mini-btn primary" onClick={() => resolve(path)}>{t("reading.its_right")}</button></span>
                )}
              </div>
            );
          })}
          <div className="field-row">
            <span className="k">{t("insurance.status")}</span>
            <span className="v">{t(`insurance.status.${claim.status}` as MessageKey)}</span>
            <span className="chip">{t("reading.sure", { pct: confidencePercent(claim.status_confidence) })}</span>
            <span className="note">{t("insurance.source", { source: claim.status_location || t("insurance.source_missing") })}</span>
            {needs(`claims.${index}.status`, claim.status_confidence) && !resolved.has(`claims.${index}.status`) && (
              <span className="row-actions"><button type="button" className="mini-btn primary" onClick={() => resolve(`claims.${index}.status`)}>{t("reading.its_right")}</button></span>
            )}
          </div>
        </section>
      ))}

      {unresolved.length > 0 && <p className="error-text" role="alert">{t("insurance.check_first", { n: unresolved.length })}</p>}
      <div className="btn-row">
        <Button onClick={() => onConfirm(document)} disabled={unresolved.length > 0}>{t("insurance.continue")}</Button>
        <Button variant="ghost" onClick={onSkip}>{t("insurance.skip")}</Button>
      </div>
    </>
  );
}
