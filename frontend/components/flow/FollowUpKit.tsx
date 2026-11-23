"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { downloadFollowUpLetter, type FollowUpLetterRequest } from "@/lib/api";
import { useI18n, type MessageKey } from "@/lib/i18n";
import type { ConfirmedBill } from "@/lib/types";

type Step = "applied" | "documents" | "decision" | "appeal";
type DocumentKind = FollowUpLetterRequest["documents"][number];
type DownloadKind = FollowUpLetterRequest["kind"] | "appeal";

const STEPS: Step[] = ["applied", "documents", "decision", "appeal"];
const DOCUMENTS: DocumentKind[] = ["income", "residency", "tax", "bank", "insurance", "benefits"];

export function FollowUpKit({ bill, onAppeal }: { bill: ConfirmedBill; onAppeal: () => Promise<void> }) {
  const { t, lang } = useI18n();
  const [step, setStep] = useState<Step>("applied");
  const [applicationDate, setApplicationDate] = useState("");
  const [documents, setDocuments] = useState<Set<DocumentKind>>(new Set());
  const [working, setWorking] = useState<DownloadKind | null>(null);
  const [failed, setFailed] = useState(false);

  function toggle(document: DocumentKind) {
    setDocuments((current) => {
      const next = new Set(current);
      if (next.has(document)) next.delete(document);
      else next.add(document);
      return next;
    });
  }

  async function download(kind: FollowUpLetterRequest["kind"]) {
    setWorking(kind);
    setFailed(false);
    try {
      await downloadFollowUpLetter({
        kind,
        lang: lang === "es" ? "es" : "en",
        hospital: bill.hospital.name || bill.fields.hospital_name,
        account_number: bill.fields.account_number,
        service_date: bill.fields.service_date,
        application_date: applicationDate,
        documents: [...documents],
      });
    } catch {
      setFailed(true);
    } finally {
      setWorking(null);
    }
  }

  async function appeal() {
    setWorking("appeal");
    setFailed(false);
    try {
      await onAppeal();
    } catch {
      setFailed(true);
    } finally {
      setWorking(null);
    }
  }

  return (
    <section className="follow-up-kit" aria-labelledby="follow-up-title">
      <h2 id="follow-up-title">{t("follow_up.title")}</h2>
      <p>{t("follow_up.sub")}</p>
      <ol className="follow-up-steps">
        {STEPS.map((item, index) => (
          <li key={item}>
            <button type="button" aria-pressed={step === item} onClick={() => setStep(item)}>
              <span aria-hidden="true">{index + 1}</span>
              {t(`follow_up.step.${item}` as MessageKey)}
            </button>
          </li>
        ))}
      </ol>

      <label className="follow-up-date">
        <span>{t("follow_up.application_date")}</span>
        <input type="date" value={applicationDate} onChange={(event) => setApplicationDate(event.target.value)} />
      </label>

      {step === "applied" && (
        <div className="follow-up-action">
          <h3>{t("follow_up.status_title")}</h3>
          <p>{t("follow_up.status_sub")}</p>
          <Button variant="ghost" onClick={() => download("status_request")} disabled={working !== null}>
            {working === "status_request" ? t("follow_up.working") : t("follow_up.status_button")}
          </Button>
        </div>
      )}

      {step === "documents" && (
        <div className="follow-up-action">
          <h3>{t("follow_up.documents_title")}</h3>
          <p>{t("follow_up.documents_sub")}</p>
          <fieldset className="document-checklist">
            <legend>{t("follow_up.documents_legend")}</legend>
            {DOCUMENTS.map((item) => (
              <label key={item}>
                <input type="checkbox" checked={documents.has(item)} onChange={() => toggle(item)} />
                <span>{t(`follow_up.document.${item}` as MessageKey)}</span>
              </label>
            ))}
          </fieldset>
          <Button variant="ghost" onClick={() => download("more_documents")} disabled={working !== null}>
            {working === "more_documents" ? t("follow_up.working") : t("follow_up.documents_button")}
          </Button>
        </div>
      )}

      {step === "decision" && (
        <div className="follow-up-action">
          <h3>{t("follow_up.decision_title")}</h3>
          <p>{t("follow_up.decision_sub")}</p>
          <Button variant="ghost" onClick={appeal} disabled={working !== null}>
            {working === "appeal" ? t("follow_up.working") : t("follow_up.appeal_button")}
          </Button>
        </div>
      )}

      {step === "appeal" && <p className="follow-up-action">{t("follow_up.appeal_note")}</p>}

      <div className="collections-help">
        <h3>{t("follow_up.collections_title")}</h3>
        <p>{t("follow_up.collections_sub")}</p>
        <p className="disclaimer">{t("follow_up.collections_legal")}</p>
        <Button variant="ghost" onClick={() => download("eca_pause_request")} disabled={working !== null}>
          {working === "eca_pause_request" ? t("follow_up.working") : t("follow_up.collections_button")}
        </Button>
      </div>
      <div aria-live="polite">{failed && <p className="error-text">{t("follow_up.failed")}</p>}</div>
    </section>
  );
}
