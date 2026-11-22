"use client";

import { useEffect, useState } from "react";
import { CalendarPlus, Scale } from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildIcs, computeDeadline, reminderDate, type Deadline } from "@/lib/deadline";
import { getFacts, type PolicyFacts } from "@/lib/extras";
import { useI18n, type Lang, type Translate } from "@/lib/i18n";
import type { ConfirmedBill, EligibilityData } from "@/lib/types";
import type { Benefits } from "./BenefitsQuestion";

const PRESUMPTIVE_RE = /presumptive|automatic|SNAP|food stamp|Medicaid|WIC|public (assistance|benefit)/i;

function useFacts(slug: string): PolicyFacts | null {
  const [facts, setFacts] = useState<PolicyFacts | null>(null);
  useEffect(() => {
    let live = true;
    getFacts(slug).then(
      (data) => live && setFacts(data),
      () => {},
    );
    return () => {
      live = false;
    };
  }, [slug]);
  return facts;
}

function fmtDate(d: Date, lang: Lang): string {
  return new Intl.DateTimeFormat(lang === "es" ? "es-US" : "en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(d);
}

interface ResultExtrasProps {
  data: EligibilityData;
  bill: ConfirmedBill;
  benefits: Benefits;
  sample: boolean;
}

/** Deadline + calendar, benefits note and state law. Information only: none of it changes the result above. */
export function ResultExtras({ data, bill, benefits, sample }: ResultExtrasProps) {
  const facts = useFacts(bill.hospital.slug);
  if (!facts || sample) return null;
  const applies = data.status !== "probably_not_eligible";
  return (
    <>
      {applies && <DeadlineCard facts={facts} bill={bill} data={data} />}
      {applies && benefits === "yes" && <BenefitsNote facts={facts} />}
      {facts.state_law && <StateLawBox facts={facts} />}
    </>
  );
}

function deadlineLine(d: Deadline, t: Translate, lang: Lang): string {
  if (d.kind === "none") return t("wow.deadline.none");
  if (d.kind === "no_date") return t("wow.deadline.no_date", { days: d.days ?? 0 });
  const vars = {
    date: fmtDate(d.date as Date, lang),
    days: d.days ?? 0,
    visit: fmtDate(d.service as Date, lang),
  };
  return d.kind === "from_service" ? t("wow.deadline.from_service", vars) : t("wow.deadline.at_least", vars);
}

function DeadlineCard({ facts, bill, data }: { facts: PolicyFacts; bill: ConfirmedBill; data: EligibilityData }) {
  const { t, lang } = useI18n();
  const w = facts.application_window;
  const d = computeDeadline(bill.fields.service_date, w.days, w.counted_from);
  const hospital = data.hospital_name || bill.hospital.name;

  function download() {
    if (!d.date) return;
    const lines = [
      bill.fields.account_number ? `${t("wow.ics.account")}: ${bill.fields.account_number}` : "",
      facts.source_url ? `${t("wow.ics.policy")}: ${facts.source_url}` : "",
      t("result.fine"),
    ].filter(Boolean);
    const ics = buildIcs({
      hospital,
      slug: bill.hospital.slug,
      deadline: d.date,
      reminder: reminderDate(d.date),
      description: lines.join("\n"),
    });
    const url = URL.createObjectURL(new Blob([ics], { type: "text/calendar;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `BillBack-reminder-${bill.hospital.slug}.ics`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
  }

  const left = d.daysLeft;
  return (
    <section className="extra-box deadline-box" aria-label={t("wow.deadline.title")}>
      <p className="extra-title">
        {t("wow.deadline.title")}
        {left !== null && (
          <span className={`days-chip${left < 30 ? " urgent" : ""}`}>
            {left >= 0 ? t("wow.deadline.days_left", { n: left }) : t("wow.deadline.passed")}
          </span>
        )}
      </p>
      <p className="mb-0">{deadlineLine(d, t, lang)}</p>
      {d.date && left !== null && left >= 0 && (
        <div className="btn-row mt-3!">
          <Button variant="ghost" onClick={download}>
            <CalendarPlus aria-hidden="true" />
            {t("wow.deadline.calendar")}
          </Button>
        </div>
      )}
    </section>
  );
}

function BenefitsNote({ facts }: { facts: PolicyFacts }) {
  const { t } = useI18n();
  const text = facts.presumptive_eligibility?.trim() ?? "";
  const automatic = text !== "" && PRESUMPTIVE_RE.test(text);
  return (
    <section className={`extra-box ${automatic ? "benefits-yes" : ""}`} aria-label={t("wow.benefits.title")}>
      {automatic ? (
        <>
          <p className="extra-title">{t("wow.benefits.auto_title")}</p>
          <p className="quote-lang">{t("result.policy_text_label")}</p>
          <p lang="en">“{text}”</p>
          <p className="mb-0">{t("wow.benefits.auto_tell")}</p>
        </>
      ) : (
        <p className="mb-0">{t("wow.benefits.no_auto")}</p>
      )}
    </section>
  );
}

function StateLawBox({ facts }: { facts: PolicyFacts }) {
  const { t, lang } = useI18n();
  const law = facts.state_law;
  if (!law) return null;
  return (
    <section className="extra-box law-box" aria-label={t("wow.law.title")}>
      <p className="extra-title">
        <Scale aria-hidden="true" size={18} /> {t("wow.law.where", { state: lang === "es" ? law.name_es : law.name_en })}
      </p>
      <p>
        {t("wow.law.lead")} {lang === "es" ? law.summary_es : law.summary_en}.{" "}
        <a className="text-link" href={law.url} target="_blank" rel="noopener noreferrer">
          {t("wow.law.read", { citation: law.citation })}
          <span className="sr-only"> {t("result.new_tab")}</span>
        </a>
      </p>
      <p className="disclaimer mb-0">{t("wow.law.note")}</p>
    </section>
  );
}
