"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { compareEob, downloadInsuranceLetter } from "@/lib/api";
import { useI18n, type MessageKey } from "@/lib/i18n";
import type { ConfirmedBill, EobDocument, ReconciliationData } from "@/lib/types";

interface InsuranceReviewProps {
  bill: ConfirmedBill;
  eob: EobDocument;
}

type State = { phase: "loading" } | { phase: "ready"; data: ReconciliationData } | { phase: "error" };

export function InsuranceReview({ bill, eob }: InsuranceReviewProps) {
  const { t, lang } = useI18n();
  const [state, setState] = useState<State>({ phase: "loading" });
  const [letter, setLetter] = useState<"idle" | "working" | "failed">("idle");

  useEffect(() => {
    let live = true;
    compareEob(bill, eob).then(
      (data) => live && setState({ phase: "ready", data }),
      () => live && setState({ phase: "error" }),
    );
    return () => {
      live = false;
    };
  }, [bill, eob]);

  const claim = state.phase === "ready"
    ? eob.claims[state.data.matched_claim_index ?? 0] ?? eob.claims[0]
    : eob.claims[0];

  async function getLetter(kind: "itemized_bill" | "billing_hold") {
    setLetter("working");
    try {
      await downloadInsuranceLetter({
        kind,
        lang,
        hospital: bill.fields.hospital_name,
        account_number: bill.fields.account_number,
        service_date: bill.fields.service_date,
        bill_amount: bill.fields.amount_due,
        eob_patient_responsibility: claim?.patient_responsibility.value ?? "",
        claim_status: claim?.status ?? "unknown",
      });
      setLetter("idle");
    } catch {
      setLetter("failed");
    }
  }

  return (
    <section className="insurance-review" aria-labelledby="insurance-review-title">
      <p className="feature-tag">{t("insurance.review_tag")}</p>
      <h2 id="insurance-review-title">{t("insurance.review_title")}</h2>
      <p>{t("insurance.review_sub")}</p>
      {state.phase === "loading" && <p className="status-line" role="status">{t("insurance.comparing")}</p>}
      {state.phase === "error" && <p className="error-text" role="alert">{t("insurance.compare_error")}</p>}
      {state.phase === "ready" && (
        <>
          {state.data.discrepancies.length === 0 ? (
            <p className="banner">{t("insurance.no_flags")}</p>
          ) : (
            <div className="insurance-flags">
              {state.data.discrepancies.map((item, index) => (
                <article className={`insurance-flag ${item.severity}`} key={`${item.code}-${index}`}>
                  <h3>{t(`insurance.flag.${item.code}` as MessageKey)}</h3>
                  <div className="insurance-sides">
                    <div><strong>{t("insurance.bill_says")}</strong><span>{item.bill_value}</span><small>{item.bill_source}</small></div>
                    <div><strong>{t("insurance.eob_says")}</strong><span>{item.eob_value}</span><small>{item.eob_source}</small></div>
                  </div>
                </article>
              ))}
            </div>
          )}
          <div className="call-script">
            <h3>{t("insurance.call_title")}</h3>
            <p>{t("insurance.call_script", { amount: bill.fields.amount_due, responsibility: claim?.patient_responsibility.value ?? t("insurance.unknown") })}</p>
          </div>
        </>
      )}
      <p className="disclaimer">{t("insurance.hold_note")}</p>
      <div className="btn-row">
        <Button variant="ghost" onClick={() => getLetter("itemized_bill")} disabled={letter === "working"}>{t("insurance.itemized_letter")}</Button>
        <Button variant="ghost" onClick={() => getLetter("billing_hold")} disabled={letter === "working"}>{t("insurance.hold_letter")}</Button>
      </div>
      <div aria-live="polite">{letter === "failed" && <p className="error-text">{t("insurance.letter_error")}</p>}</div>
    </section>
  );
}
