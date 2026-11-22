"use client";

import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { Stamp } from "@/components/hero/Stamp";
import { Button } from "@/components/ui/button";
import { ApiError, DEMO_MODE, downloadPacket } from "@/lib/api";
import { useI18n, useT, type MessageKey, type Translate } from "@/lib/i18n";
import { EASE_OUT, SNAPPY_SETTLE_MS } from "@/lib/motion";
import { plainCaveat } from "@/lib/caveats";
import { MOCK_ELIGIBILITY_DEFAULT } from "@/lib/mock";
import {
  CONFIRM_THRESHOLD,
  type ConfirmedBill,
  type EligibilityData,
  type EligibilityStatus,
} from "@/lib/types";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const DOLLAR_FOR_URL = "https://dollarfor.org";
const STAMP_DELAY_MS = 200;
const STRIKE_DELAY_MS = 250;
const STRIKE_MS = 550;
const SWEEP_DELAY_S = 0.5;

const TITLES: Record<EligibilityStatus, MessageKey> = {
  likely_free: "result.title.likely_free",
  likely_discounted: "result.title.likely_discounted",
  probably_not_eligible: "result.title.probably_not_eligible",
  cannot_determine: "result.title.cannot_determine",
};

type State =
  | { phase: "loading" }
  | { phase: "ready"; data: EligibilityData; sample: boolean }
  | { phase: "unavailable"; message: string };

interface ResultStepProps {
  entrance: Entrance;
  reduce: boolean;
  /** The eligibility check already in flight, started by Flow. */
  checking: Promise<EligibilityData>;
  bill: ConfirmedBill;
  household: number;
  income: number;
  onRetry: () => void;
  onStartOver: () => void;
}

export function ResultStep({ entrance, reduce, checking, bill, household, income, onRetry, onStartOver }: ResultStepProps) {
  const t = useT();
  const [state, setState] = useState<State>({ phase: "loading" });

  useEffect(() => {
    let live = true;
    checking.then(
      (data) => live && setState({ phase: "ready", data, sample: false }),
      (err: unknown) => {
        if (!live) return;
        const error = err instanceof ApiError ? err : new ApiError("failed", null);
        // Only when the service isn't there, and only in demo mode, show the labeled sample.
        if (DEMO_MODE && error.kind === "unavailable") {
          setState({ phase: "ready", data: MOCK_ELIGIBILITY_DEFAULT, sample: true });
        } else {
          setState({ phase: "unavailable", message: error.kind === "rejected" ? error.message : "" });
        }
      },
    );
    return () => {
      live = false;
    };
  }, [checking]);

  return (
    <StepCard step={4} entrance={entrance} reduce={reduce}>
      {state.phase === "loading" && (
        <>
          <StepHeading key="loading">{t("result.checking_title")}</StepHeading>
          <p className="status-line" role="status">
            <span className="pulse-dot" aria-hidden="true" />
            <span>{t("result.checking")}</span>
          </p>
        </>
      )}

      {state.phase === "unavailable" && (
        <>
          <StepHeading key="unavailable">{t("result.unavailable_title")}</StepHeading>
          <p className="sub" role="alert">
            {state.message || t("result.unavailable")}
          </p>
          <div className="btn-row">
            <Button onClick={onRetry}>{t("error.try_again")}</Button>
            <Button variant="ghost" onClick={onStartOver}>
              {t("result.start_over")}
            </Button>
          </div>
        </>
      )}

      {state.phase === "ready" && (
        <Verdict
          data={state.data}
          sample={state.sample}
          bill={bill}
          household={household}
          income={income}
          reduce={reduce}
          onStartOver={onStartOver}
        />
      )}
    </StepCard>
  );
}

function stampText(data: EligibilityData, t: Translate): { top: string; bottom: string } | null {
  if (data.status === "likely_free") {
    return { top: t("result.stamp.free_top"), bottom: t("result.stamp.free_bottom") };
  }
  if (data.status === "likely_discounted") {
    const tier = data.tier;
    const percent =
      tier && tier.discount_type === "percent_off" && typeof tier.value === "number"
        ? `${Number(tier.value.toFixed(1))}%`
        : "−%";
    return { top: percent, bottom: t("result.stamp.off_bottom") };
  }
  return null;
}

function safeUrl(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}

const TONE: Record<EligibilityStatus, string> = {
  likely_free: "tone-free",
  likely_discounted: "tone-discount",
  probably_not_eligible: "tone-neutral",
  cannot_determine: "tone-neutral",
};

interface VerdictProps {
  data: EligibilityData;
  sample: boolean;
  bill: ConfirmedBill;
  household: number;
  income: number;
  reduce: boolean;
  onStartOver: () => void;
}

type PacketState = "idle" | "working" | "failed";

function Verdict({ data, sample, bill, household, income, reduce, onStartOver }: VerdictProps) {
  const { t, lang } = useI18n();
  const stamp = stampText(data, t);
  const [stamped, setStamped] = useState(reduce);
  const [packet, setPacket] = useState<PacketState>("idle");

  const free = data.status === "likely_free";
  // For "likely free" the amount is struck through first, then the stamp lands: about 1s, once.
  const stampDelayMs = free ? STRIKE_DELAY_MS + STRIKE_MS : STAMP_DELAY_MS;
  const hasStamp = stamp !== null;
  useEffect(() => {
    if (reduce || !hasStamp) return;
    const timer = window.setTimeout(() => setStamped(true), stampDelayMs);
    return () => window.clearTimeout(timer);
  }, [reduce, hasStamp, stampDelayMs]);

  const { evidence } = data;
  const quote = evidence.quote?.trim() ?? "";
  const doubleCheck =
    evidence.verified === false || evidence.status !== "stated" || evidence.confidence < CONFIRM_THRESHOLD;
  const policyUrl = safeUrl(data.source_url);
  const hospitalName = data.hospital_name || bill.hospital.name;
  const lead =
    typeof evidence.page === "number"
      ? t("result.quote_lead_page", { hospital: hospitalName, page: evidence.page })
      : t("result.quote_lead", { hospital: hospitalName });

  // The coral highlight sweeps after the stamp has landed, or shortly after the card when there's no stamp.
  const sweepDelay = (stamp ? (stampDelayMs + SNAPPY_SETTLE_MS) / 1000 : 0) + SWEEP_DELAY_S;
  const caveats = data.caveats.map((c) => plainCaveat(c, t));
  const amount = sample ? "" : bill.fields.amount_due;
  const canApply = data.status !== "probably_not_eligible";

  async function getPacket() {
    setPacket("working");
    try {
      await downloadPacket({
        bill: bill.fields,
        hospital_slug: bill.hospital.slug,
        household_size: household,
        annual_income: income,
        eligibility: {
          status: data.status,
          percent_of_fpl: data.percent_of_fpl,
          quote,
          page: evidence.page,
          fpl_year: data.fpl_year ?? null,
        },
        lang,
      });
      setPacket("idle");
    } catch {
      setPacket("failed");
    }
  }

  const helpLine = (
    <p className="help-line">
      {t("result.help")} · {t("result.free_help")}{" "}
      <a className="text-link" href={DOLLAR_FOR_URL} target="_blank" rel="noopener noreferrer">
        Dollar For
        <span className="sr-only"> {t("result.new_tab")}</span>
      </a>
    </p>
  );

  return (
    <>
      {sample && <p className="banner">{t("result.sample_banner")}</p>}

      <div className={`verdict ${TONE[data.status]}`}>
        <div className="mini-bill" aria-hidden="true">
          <span className="mini-name">{(sample ? data.hospital_name : bill.hospital.name).toUpperCase()}</span>
          <span className="mini-due">{t("result.mini_due")}</span>
          {amount && (
            <span className="mini-amount">
              {amount}
              {free && (
                <motion.span
                  className="strike"
                  initial={reduce ? false : { scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: STRIKE_MS / 1000, ease: EASE_OUT, delay: STRIKE_DELAY_MS / 1000 }}
                />
              )}
            </span>
          )}
          {stamp && <Stamp top={stamp.top} bottom={stamp.bottom} show={stamped} reduce={reduce} from={2.6} />}
        </div>
        <div>
          <StepHeading key={data.status}>{t(TITLES[data.status])}</StepHeading>
          <p className="sub mb-0!">
            {sample
              ? t("result.sample_note")
              : t(household === 1 ? "result.fpl_one" : "result.fpl_other", {
                  pct: Math.round(data.percent_of_fpl),
                  n: household,
                })}
          </p>
          <p className="disclaimer">{t("result.fine")}</p>
        </div>
      </div>

      {data.status === "likely_discounted" && data.tier?.description && (
        <p className="mt-3 mb-0" lang="en">
          {data.tier.description}
        </p>
      )}

      <div className="quote-box">
        <p className="lead">{lead}</p>
        {lang === "es" && quote && <p className="quote-lang">{t("result.policy_text_label")}</p>}
        {quote ? (
          <p lang="en">
            {"“"}
            <motion.span
              className="hl"
              initial={reduce ? false : { backgroundSize: "0% 100%" }}
              animate={{ backgroundSize: "100% 100%" }}
              transition={{ duration: 1.1, ease: EASE_OUT, delay: sweepDelay }}
            >
              {quote}
            </motion.span>
            {"”"}
          </p>
        ) : (
          <p>{t("result.no_quote")}</p>
        )}
        {(policyUrl || (quote && doubleCheck)) && (
          <p className="more">
            {quote && doubleCheck && <>{t("result.double_check")} </>}
            {policyUrl && (
              <a className="text-link policy-link" href={policyUrl} target="_blank" rel="noopener noreferrer">
                {t("result.read_policy")}
                <span className="sr-only"> {t("result.new_tab")}</span>
              </a>
            )}
          </p>
        )}
      </div>

      {canApply && !sample && (
        <>
          <p className="caveats-title">{t("result.next_title")}</p>
          <ol className="what-next">
            <li>{t("result.next_1")}</li>
            <li>{t("result.next_2")}</li>
            <li>{t("result.next_3")}</li>
          </ol>
        </>
      )}

      {data.status === "probably_not_eligible" && (
        <ul className="next-steps">
          <li>{t("result.next.payment_plan")}</li>
          <li>{t("result.next.check_errors")}</li>
          <li>
            <a className="text-link" href={DOLLAR_FOR_URL} target="_blank" rel="noopener noreferrer">
              {t("result.next.dollarfor")}
              <span className="sr-only"> {t("result.new_tab")}</span>
            </a>
          </li>
        </ul>
      )}
      {data.status === "cannot_determine" && (
        <ul className="next-steps">
          <li>{t("result.next.call")}</li>
        </ul>
      )}

      {caveats.length > 0 && (
        <>
          <p className="caveats-title">{t("result.caveats_title")}</p>
          <ul className="caveats">
            {caveats.map((c) => (
              <li key={c.text}>
                {c.text}
                {c.wording && (
                  <details className="wording">
                    <summary>{t("result.policy_wording")}</summary>
                    <span lang="en">{c.wording}</span>
                  </details>
                )}
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="btn-row">
        {canApply && !sample && (
          <Button variant="coral" onClick={getPacket} disabled={packet === "working"}>
            {packet === "working" ? t("result.app_working") : t("result.get_app")}
          </Button>
        )}
        <Button variant="ghost" onClick={onStartOver}>
          {t("result.start_over")}
        </Button>
      </div>
      <div aria-live="polite">{packet === "failed" && <p className="error-text">{t("result.app_failed")}</p>}</div>

      {helpLine}
    </>
  );
}
