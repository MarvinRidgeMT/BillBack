"use client";

import { useEffect, useState } from "react";
import { getScheduleHCrosscheck } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { ScheduleHCrosscheck } from "@/lib/types";

function taxPeriod(value: string): string {
  return /^\d{6}$/.test(value) ? `${value.slice(0, 4)}-${value.slice(4)}` : value;
}

export function ScheduleHBadge({ hospitalSlug }: { hospitalSlug: string }) {
  const t = useT();
  const [record, setRecord] = useState<ScheduleHCrosscheck | null>(null);

  useEffect(() => {
    let active = true;
    getScheduleHCrosscheck(hospitalSlug).then(
      (value) => active && setRecord(value),
      () => active && setRecord(null),
    );
    return () => {
      active = false;
    };
  }, [hospitalSlug]);

  if (!record) return null;

  const freeConflict =
    record.free_care_fpl_percent != null &&
    record.policy_free_care_fpl_percent != null &&
    record.free_care_fpl_percent !== record.policy_free_care_fpl_percent;
  const reported = freeConflict ? record.free_care_fpl_percent : record.discounted_care_fpl_percent;
  const current = freeConflict ? record.policy_free_care_fpl_percent : record.policy_discounted_care_fpl_percent;
  const link = record.rendered_schedule_h_url || record.filing_url;

  return (
    <aside className={`schedule-h ${record.status === "agree" ? "schedule-h-agree" : "schedule-h-conflict"}`} aria-label={t("schedule_h.title")}>
      <p className="schedule-h-label">{record.status === "agree" ? "✓" : "!"} {t("schedule_h.title")}</p>
      <p>
        {record.status === "agree"
          ? t("schedule_h.agree", { pct: record.free_care_fpl_percent ?? record.discounted_care_fpl_percent ?? "—" })
          : t("schedule_h.conflict", {
              kind: t(freeConflict ? "schedule_h.free" : "schedule_h.discounted"),
              reported: reported ?? "—",
              current: current ?? "—",
            })}
      </p>
      <p className="schedule-h-meta">
        {t("schedule_h.period", { period: taxPeriod(record.tax_period) })} {t("schedule_h.older")}{" "}
        <a className="text-link" href={link} target="_blank" rel="noopener noreferrer">
          {t("schedule_h.source")}<span className="sr-only"> {t("result.new_tab")}</span>
        </a>
      </p>
      <p className="schedule-h-meta">{t("schedule_h.no_effect")}</p>
    </aside>
  );
}
