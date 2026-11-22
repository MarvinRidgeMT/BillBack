"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, MotionConfig } from "motion/react";
import { HowItWorks } from "@/components/HowItWorks";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/hero/Hero";
import { Sky } from "@/components/hero/Sky";
import { checkEligibility, readBill } from "@/lib/api";
import { I18nProvider } from "@/lib/i18n";
import { MOCK_BILL_READ } from "@/lib/mock";
import { useParallax, useReducedMotionPref } from "@/lib/motion";
import type { BillReadData, ConfirmedBill, EligibilityData, EligibilityRequest } from "@/lib/types";
import { ManualEntry } from "./ManualEntry";
import { QuestionsStep, type Answers } from "./QuestionsStep";
import { ReadingStep } from "./ReadingStep";
import { ResultStep } from "./ResultStep";
import type { Entrance } from "./StepCard";
import { UploadStep } from "./UploadStep";

type Step = "hero" | "upload" | "reading" | "manual" | "questions" | "result";

interface Reading {
  attempt: number;
  /** Kept in memory only, so "Try again" can resend it. Null for the sample reading. */
  file: File | null;
  promise: Promise<BillReadData>;
  sample: boolean;
}

interface Checking {
  attempt: number;
  request: EligibilityRequest;
  household: number;
  promise: Promise<EligibilityData>;
}

/** A rejection is handled by the step that shows it. This stops it being reported as unhandled if the patient leaves first. */
function quiet<T>(promise: Promise<T>): Promise<T> {
  promise.catch(() => {});
  return promise;
}

/**
 * The whole app as one state machine: hero -> upload -> reading (or manual) -> questions -> result.
 * Everything lives in React state. Nothing is stored, so a refresh starts over.
 */
function FlowInner() {
  const reduce = useReducedMotionPref();
  const parallax = useParallax(!reduce);

  const [step, setStep] = useState<Step>("hero");
  const [entrance, setEntrance] = useState<Entrance>("hero");
  const [reading, setReading] = useState<Reading | null>(null);
  const [bill, setBill] = useState<ConfirmedBill | null>(null);
  const [checking, setChecking] = useState<Checking | null>(null);
  const attempts = useRef(0);
  const visited = useRef(false);

  const go = useCallback((next: Step) => {
    setStep((current) => {
      setEntrance(current === "hero" ? "hero" : "step");
      return next;
    });
  }, []);

  // Each new step starts at the top of the page. Back on the hero, focus returns to the CTA.
  useEffect(() => {
    if (!visited.current && step === "hero") return;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    if (!visited.current) {
      visited.current = true;
      return;
    }
    if (step !== "hero") return;
    const timer = window.setTimeout(() => document.getElementById("hero-cta")?.focus(), reduce ? 0 : 400);
    return () => window.clearTimeout(timer);
  }, [step, reduce]);

  const startReading = useCallback(
    (file: File | null) => {
      attempts.current += 1;
      setReading({
        attempt: attempts.current,
        file,
        sample: file === null,
        promise: quiet(file ? readBill(file) : Promise.resolve(MOCK_BILL_READ)),
      });
      go("reading");
    },
    [go],
  );

  const startChecking = useCallback(
    (request: EligibilityRequest) => {
      attempts.current += 1;
      setChecking({
        attempt: attempts.current,
        request,
        household: request.household_size,
        promise: quiet(checkEligibility(request)),
      });
      go("result");
    },
    [go],
  );

  const onConfirm = useCallback(
    (confirmed: ConfirmedBill) => {
      setBill(confirmed);
      go("questions");
    },
    [go],
  );

  const onAnswers = useCallback(
    ({ household, income }: Answers) => {
      if (!bill) return;
      startChecking({
        hospital_slug: bill.hospital.slug,
        household_size: household,
        annual_income: income,
        state: bill.hospital.state,
      });
    },
    [bill, startChecking],
  );

  const startOver = useCallback(() => {
    setReading(null);
    setBill(null);
    setChecking(null);
    go("hero");
  }, [go]);

  return (
    <MotionConfig reducedMotion="user">
      <div className="stage">
        <Sky parallax={parallax} />
        <Nav />
        <main>
          <AnimatePresence mode="wait">
            {step === "hero" && (
              <Hero
                key={reduce ? "hero-still" : "hero"}
                onStart={() => go("upload")}
                parallax={parallax}
                reduce={reduce}
              />
            )}
            {step === "upload" && (
              <UploadStep
                key="upload"
                entrance={entrance}
                reduce={reduce}
                onFile={startReading}
                onManual={() => go("manual")}
              />
            )}
            {step === "reading" && reading && (
              <ReadingStep
                key={`reading-${reading.attempt}`}
                entrance={entrance}
                reduce={reduce}
                reading={reading.promise}
                sample={reading.sample}
                onConfirm={onConfirm}
                onRetry={() => (reading.file ? startReading(reading.file) : go("upload"))}
                onManual={() => go("manual")}
                onSample={() => startReading(null)}
                onStartOver={startOver}
              />
            )}
            {step === "manual" && (
              <ManualEntry
                key="manual"
                entrance={entrance}
                reduce={reduce}
                onConfirm={onConfirm}
                onBack={() => go("upload")}
                onStartOver={startOver}
              />
            )}
            {step === "questions" && (
              <QuestionsStep key="questions" entrance={entrance} reduce={reduce} onSubmit={onAnswers} />
            )}
            {step === "result" && checking && bill && (
              <ResultStep
                key={`result-${checking.attempt}`}
                entrance={entrance}
                reduce={reduce}
                checking={checking.promise}
                bill={bill}
                household={checking.household}
                income={checking.request.annual_income}
                onRetry={() => startChecking(checking.request)}
                onStartOver={startOver}
              />
            )}
          </AnimatePresence>
        </main>
      </div>
      <HowItWorks />
    </MotionConfig>
  );
}

export function Flow() {
  return (
    <I18nProvider>
      <FlowInner />
    </I18nProvider>
  );
}
