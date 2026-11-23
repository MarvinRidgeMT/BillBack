"use client";

import { useState } from "react";
import { strToU8, zipSync } from "fflate";
import { Download, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { buildPacketBlob } from "@/lib/api";
import { buildIcs, computeDeadline, reminderDate } from "@/lib/deadline";
import { getFacts } from "@/lib/extras";
import { useI18n, type MessageKey } from "@/lib/i18n";
import { summaryHtml, type NavigatorCase } from "@/lib/navigator";

interface Props {
  cases: NavigatorCase[];
  onDownloaded: (ids: string[]) => void;
}

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}

export function NavigatorPanel({ cases, onDownloaded }: Props) {
  const { t, lang } = useI18n();
  const [state, setState] = useState<"idle" | "working" | "failed">("idle");
  const packetCases = cases.filter((item) => item.packet);

  function print(item: NavigatorCase) {
    const page = window.open("", "_blank");
    if (!page) return;
    page.opener = null;
    page.document.write(summaryHtml(item, lang === "es" ? "es" : "en"));
    page.document.close();
    page.focus();
    page.print();
  }

  async function downloadAll() {
    setState("working");
    try {
      const files: Record<string, Uint8Array> = {};
      for (const [index, item] of packetCases.entries()) {
        const packet = item.packet;
        if (!packet) continue;
        const folder = `case-${index + 1}`;
        const pdf = await buildPacketBlob(packet);
        files[`${folder}/application.pdf`] = new Uint8Array(await pdf.arrayBuffer());
        files[`${folder}/take-home-summary.html`] = strToU8(summaryHtml(item, lang === "es" ? "es" : "en"));
        const facts = await getFacts(packet.hospital_slug).catch(() => null);
        if (facts) {
          const deadline = computeDeadline(packet.bill.service_date, facts.application_window.days, facts.application_window.counted_from);
          if (deadline.date) {
            files[`${folder}/reminder.ics`] = strToU8(buildIcs({
              hospital: item.hospital,
              slug: packet.hospital_slug,
              deadline: deadline.date,
              reminder: reminderDate(deadline.date),
              description: t("navigator.ics_note"),
            }));
          }
        }
      }
      save(new Blob([zipSync(files) as BlobPart], { type: "application/zip" }), "BillBack-navigator-cases.zip");
      onDownloaded(packetCases.map((item) => item.id));
      setState("idle");
    } catch {
      setState("failed");
    }
  }

  return (
    <section className="navigator-panel" aria-labelledby="navigator-cases-title">
      <h2 id="navigator-cases-title">{t("navigator.cases_title")}</h2>
      <p>{t("navigator.memory_note")}</p>
      <ul>
        {cases.map((item) => (
          <li key={item.id}>
            <span><strong>{item.label}</strong>{item.hospital ? ` · ${item.hospital}` : ""}</span>
            <span className="navigator-status">{t(`navigator.status.${item.status}` as MessageKey)}</span>
            {item.packet && (
              <button type="button" className="text-link link-button" onClick={() => print(item)}>
                <Printer size={16} aria-hidden="true" /> {t("navigator.print")}
              </button>
            )}
          </li>
        ))}
      </ul>
      <Button variant="ghost" onClick={downloadAll} disabled={state === "working" || packetCases.length === 0}>
        <Download aria-hidden="true" /> {state === "working" ? t("navigator.working") : t("navigator.download_all")}
      </Button>
      <div aria-live="polite">{state === "failed" && <p className="error-text">{t("navigator.failed")}</p>}</div>
    </section>
  );
}
