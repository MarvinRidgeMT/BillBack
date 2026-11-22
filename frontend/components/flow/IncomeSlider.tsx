"use client";

import { useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { getThresholds, whatIfEligibility, type Thresholds } from "@/lib/extras";
import { useI18n, type MessageKey, type Translate } from "@/lib/i18n";
import { SNAPPY } from "@/lib/motion";
import type { EligibilityData, EligibilityStatus } from "@/lib/types";

const STEP = 500;
const PAGE_STEP = 5_000;
const MAX_MULTIPLE = 5; // slider goes to 5x the poverty line
const DEBOUNCE_MS = 250;

const PILL: Record<EligibilityStatus, MessageKey> = {
  likely_free: "wow.slider.free",
  likely_discounted: "wow.slider.discount",
  probably_not_eligible: "wow.slider.not_eligible",
  cannot_determine: "wow.slider.cant_tell",
};

const TONE: Record<EligibilityStatus, string> = {
  likely_free: "zone-free",
  likely_discounted: "zone-discount",
  probably_not_eligible: "zone-none",
  cannot_determine: "zone-unknown",
};

interface IncomeSliderProps {
  slug: string;
  household: number;
  state: string;
  income: number;
  initial: EligibilityData;
}

const usd = (n: number) => `$${Math.round(n).toLocaleString("en-US")}`;

function pillText(data: EligibilityData, t: Translate): string {
  const tier = data.tier;
  if (data.status === "likely_discounted" && tier?.discount_type === "percent_off" && typeof tier.value === "number") {
    return t("wow.slider.percent_off", { pct: Number(tier.value.toFixed(1)) });
  }
  return t(PILL[data.status]);
}

/** "What if my income were different?" Every status shown comes from the rules engine, never from math here. */
export function IncomeSlider({ slug, household, state, income, initial }: IncomeSliderProps) {
  const { t } = useI18n();
  const id = useId();
  const [limits, setLimits] = useState<Thresholds | null>(null);
  const [value, setValue] = useState(income);
  const [result, setResult] = useState<EligibilityData>(initial);
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    let live = true;
    getThresholds(slug, household, state).then(
      (data) => live && setLimits(data),
      () => {},
    );
    return () => {
      live = false;
    };
  }, [slug, household, state]);

  const timer = useRef<number | undefined>(undefined);
  const latest = useRef(income);

  /** Debounced: the newest value asks the engine; any earlier request is cancelled. */
  function change(next: number) {
    latest.current = next;
    setValue(next);
    window.clearTimeout(timer.current);
    controller.current?.abort();
    if (next === income) {
      setResult(initial);
      setBusy(false);
      return;
    }
    setBusy(true);
    timer.current = window.setTimeout(() => {
      const ac = new AbortController();
      controller.current = ac;
      whatIfEligibility({ hospital_slug: slug, household_size: household, annual_income: next, state }, ac.signal).then(
        (data) => {
          if (ac.signal.aborted) return;
          setResult(data);
          setBusy(false);
        },
        () => !ac.signal.aborted && setBusy(false),
      );
    }, DEBOUNCE_MS);
  }

  useEffect(
    () => () => {
      window.clearTimeout(timer.current);
      controller.current?.abort();
    },
    [],
  );

  if (!limits) return null;
  const line = limits.poverty_line;
  const max = Math.ceil((line * MAX_MULTIPLE) / STEP) * STEP;
  const clamp = (n: number) => Math.min(max, Math.max(0, n));
  const pct = Math.round((value / line) * 100);
  const maxPct = (max / line) * 100;
  const at = (p: number) => `${Math.min(100, Math.max(0, (p / maxPct) * 100))}%`;

  const zones: { from: number; to: number; tone: string; label: string }[] = [];
  let cursor = 0;
  if (limits.free_max_percent) {
    zones.push({ from: 0, to: limits.free_max_percent, tone: "zone-free", label: t("wow.slider.free") });
    cursor = limits.free_max_percent;
  }
  for (const tier of [...limits.tiers].sort((a, b) => a.max_percent - b.max_percent)) {
    if (tier.max_percent <= cursor) continue;
    zones.push({ from: cursor, to: tier.max_percent, tone: "zone-discount", label: tier.label });
    cursor = tier.max_percent;
  }
  if (limits.max_percent && limits.max_percent > cursor) {
    zones.push({ from: cursor, to: limits.max_percent, tone: "zone-discount", label: t("wow.slider.discount") });
    cursor = limits.max_percent;
  }
  if (cursor > 0 && cursor < maxPct) {
    zones.push({ from: cursor, to: maxPct, tone: "zone-none", label: t("wow.slider.not_eligible") });
  }
  const markers = zones.slice(0, -1).map((z) => z.to);
  const status = pillText(result, t);

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "PageUp" || e.key === "PageDown") {
      e.preventDefault();
      change(clamp(latest.current + (e.key === "PageUp" ? PAGE_STEP : -PAGE_STEP)));
    }
  }

  return (
    <section className="whatif" aria-labelledby={`${id}-title`}>
      <h3 className="whatif-title" id={`${id}-title`}>
        {t("wow.slider.title")} <span className="whatif-tag">{t("wow.slider.tag")}</span>
      </h3>
      <p className="whatif-sub">{t("wow.slider.sub")}</p>

      <div className="whatif-readout">
        <label htmlFor={`${id}-range`} className="whatif-amount">
          {usd(value)} <span>{t("wow.slider.per_year", { pct })}</span>
        </label>
        <div className="whatif-pill-slot" aria-live="polite" aria-busy={busy}>
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.span
              key={status}
              className={`whatif-pill ${TONE[result.status]}`}
              initial={{ opacity: 0, y: 8, scale: 0.9 }}
              animate={{ opacity: busy ? 0.6 : 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8, scale: 0.9 }}
              transition={SNAPPY}
            >
              {status}
            </motion.span>
          </AnimatePresence>
        </div>
      </div>

      <div className="whatif-track">
        <div className="whatif-zones" aria-hidden="true">
          {zones.map((z) => (
            <span
              key={`${z.from}-${z.to}`}
              className={`whatif-zone ${z.tone}`}
              style={{ left: at(z.from), width: `calc(${at(z.to)} - ${at(z.from)})` }}
              title={z.label}
            />
          ))}
        </div>
        <input
          id={`${id}-range`}
          type="range"
          min={0}
          max={max}
          step={STEP}
          value={value}
          onChange={(e) => change(Number(e.target.value))}
          onKeyDown={onKeyDown}
          aria-valuetext={t("wow.slider.valuetext", { amount: usd(value), pct, status: status.toLowerCase() })}
          aria-describedby={`${id}-scale`}
        />
        <div className="whatif-markers" id={`${id}-scale`}>
          {markers.map((m) => (
            <span key={m} className="whatif-marker" style={{ left: at(m) }}>
              <b>{Math.round(m)}%</b>
              <span>{usd((m / 100) * line)}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="whatif-foot">
        <p>{t("wow.slider.note")}</p>
        {value !== income && (
          <Button variant="ghost" className="min-h-10 px-4 py-2 text-[15px]" onClick={() => change(income)}>
            {t("wow.slider.reset")}
          </Button>
        )}
      </div>
    </section>
  );
}
