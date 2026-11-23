"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import { useT } from "@/lib/i18n";
import {
  averages,
  getServerTimings,
  getTimings,
  subscribeTimings,
  TIMING_KEYS,
  type TimingSnapshot,
} from "@/lib/timings";

interface DevPanelProps {
  /** Show without ?dev=1 (the /states page). */
  force?: boolean;
  /** Show these numbers instead of the live session (screenshots on /states). */
  snapshot?: TimingSnapshot;
  /** In the page flow instead of pinned to the corner. */
  inline?: boolean;
}

/**
 * Dev only: per-step seconds for this tab and how many bill fields came back under 80% sure.
 * Shown with ?dev=1 in the URL. Reads the in-memory store in lib/timings.ts; nothing is stored or sent.
 */
export function DevPanel({ force = false, snapshot, inline = false }: DevPanelProps) {
  const t = useT();
  const live = useSyncExternalStore(subscribeTimings, getTimings, getServerTimings);
  const [enabled, setEnabled] = useState(false);

  // Read the query string after hydration, so the server render and the first client render match.
  useEffect(() => {
    if (force) return;
    const on = new URLSearchParams(window.location.search).get("dev") === "1";
    if (on) queueMicrotask(() => setEnabled(true));
  }, [force]);

  if (!force && !enabled) return null;
  const data = snapshot ?? live;
  const avg = averages(data.entries);
  const last = (key: (typeof TIMING_KEYS)[number]) => [...data.entries].reverse().find((e) => e.key === key)?.seconds;

  return (
    <aside className={inline ? "dev-panel static" : "dev-panel"} aria-label={t("dev.title")}>
      <p className="dev-title">{t("dev.title")}</p>
      {data.entries.length === 0 ? (
        <p className="m-0">{t("dev.empty")}</p>
      ) : (
        <dl>
          {TIMING_KEYS.map((key) => {
            const a = avg[key];
            if (!a) return null;
            return (
              <div key={key}>
                <dt>{t(`dev.timing.${key}`)}</dt>
                <dd>
                  {t("dev.avg", { avg: a.avg.toFixed(2), last: (last(key) ?? 0).toFixed(2), n: a.n })}
                </dd>
              </div>
            );
          })}
        </dl>
      )}
      <p className="m-0">{t("dev.bills", { n: data.bills })}</p>
      <p className="m-0">{t("dev.low", { low: data.lowConfidence, total: data.fields })}</p>
      <p className="dev-note">{t("dev.note")}</p>
    </aside>
  );
}
