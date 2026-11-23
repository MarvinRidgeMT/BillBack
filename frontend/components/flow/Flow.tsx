"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, MotionConfig } from "motion/react";
import { CharityMap } from "@/components/CharityMap";
import { Footer } from "@/components/Footer";
import { HowItWorks } from "@/components/HowItWorks";
import { Nav } from "@/components/Nav";
import { TranslationNotice } from "@/components/TranslationNotice";
import { Hero } from "@/components/hero/Hero";
import { Sky } from "@/components/hero/Sky";
import { AccessibilityProvider } from "@/lib/accessibility";
import { checkEligibility, readBill, readEob } from "@/lib/api";
import { I18nProvider } from "@/lib/i18n";
import { MOCK_BILL_READ, MOCK_EOB_READ } from "@/lib/mock";
import { useParallax, useReducedMotionPref } from "@/lib/motion";
import type { BillReadData, ConfirmedBill, EligibilityData, EligibilityRequest, EobDocument, EobReadData } from "@/lib/types";
import type { Benefits } from "./BenefitsQuestion";
import { ManualEntry } from "./ManualEntry";
import { InsuranceStep } from "./InsuranceStep";
import { QuestionsStep, type Answers } from "./QuestionsStep";
import { ReadingStep } from "./ReadingStep";
import { ResultStep } from "./ResultStep";
import type { Entrance } from "./StepCard";
import { UploadStep } from "./UploadStep";

type Step = "hero" | "upload" | "reading" | "insurance" | "manual" | "questions" | "result";

interface Reading {
  attempt: number;
  /** Kept in memory only, so "Try again" can resend it. Null for the sample reading. */
  file: File | null;
  eobFile: File | null;
  promise: Promise<BillReadData>;
  eobPromise: Promise<EobReadData> | null;
  sample: boolean;
  sampleInsurance: boolean;
}

interface Checking {
  attempt: number;
  request: EligibilityRequest;
  household: number;
  benefits: Benefits;
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
  const [eob, setEob] = useState<EobDocument | null>(null);
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
    (file: File | null, eobFile: File | null = null) => {
      attempts.current += 1;
      setReading({
        attempt: attempts.current,
        file,
        eobFile,
        sample: file === null,
        sampleInsurance: false,
        promise: quiet(file ? readBill(file) : Promise.resolve(MOCK_BILL_READ)),
        eobPromise: eobFile ? quiet(readEob(eobFile)) : null,
      });
      go("reading");
    },
    [go],
  );

  const startSampleInsurance = useCallback(() => {
    attempts.current += 1;
    setReading({
      attempt: attempts.current,
      file: null,
      eobFile: null,
      sample: true,
      sampleInsurance: true,
      promise: Promise.resolve(MOCK_BILL_READ),
      eobPromise: Promise.resolve(MOCK_EOB_READ),
    });
    go("reading");
  }, [go]);

  const startChecking = useCallback(
    (request: EligibilityRequest, benefits: Benefits = "skip") => {
      attempts.current += 1;
      setChecking({
        attempt: attempts.current,
        request,
        household: request.household_size,
        benefits,
        promise: quiet(checkEligibility(request)),
      });
      go("result");
    },
    [go],
  );

  const onConfirm = useCallback(
    (confirmed: ConfirmedBill) => {
      setBill(confirmed);
      go(reading?.eobPromise ? "insurance" : "questions");
    },
    [go, reading],
  );

  const confirmInsurance = useCallback((confirmed: EobDocument) => {
    setEob(confirmed);
    go("questions");
  }, [go]);

  const skipInsurance = useCallback(() => {
    setEob(null);
    go("questions");
  }, [go]);

  const retryInsurance = useCallback(() => {
    if (!reading?.eobFile) {
      skipInsurance();
      return;
    }
    attempts.current += 1;
    setReading((current) => current ? {
      ...current,
      attempt: attempts.current,
      eobPromise: quiet(readEob(current.eobFile as File)),
    } : current);
  }, [reading, skipInsurance]);

  const onAnswers = useCallback(
    ({ household, income, benefits }: Answers) => {
      if (!bill) return;
      startChecking({
        hospital_slug: bill.hospital.slug,
        household_size: household,
        annual_income: income,
        state: bill.hospital.state,
      }, benefits);
    },
    [bill, startChecking],
  );

  const startOver = useCallback(() => {
    setReading(null);
    setBill(null);
    setEob(null);
    setChecking(null);
    go("hero");
  }, [go]);

  return (
    <MotionConfig reducedMotion="user">
      <div className={step === "hero" ? "stage" : "stage in-step"}>
        <Sky parallax={parallax} />
        <Nav />
        <TranslationNotice />
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
                onSampleInsurance={startSampleInsurance}
                onManual={() => go("manual")}
              />
            )}
            {step === "insurance" && reading?.eobPromise && (
              <InsuranceStep
                key={`insurance-${reading.attempt}`}
                entrance={entrance}
                reduce={reduce}
                reading={reading.eobPromise}
                sample={reading.sampleInsurance}
                onConfirm={confirmInsurance}
                onRetry={retryInsurance}
                onSkip={skipInsurance}
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
                benefits={checking.benefits}
                eob={eob}
                onRetry={() => startChecking(checking.request, checking.benefits)}
                onStartOver={startOver}
              />
            )}
          </AnimatePresence>
        </main>
      </div>
      <HowItWorks />
      <CharityMap />
      <Footer />
    </MotionConfig>
  );
}

export function Flow() {
  return (
    <I18nProvider>
      <AccessibilityProvider>
        <FlowInner />
      </AccessibilityProvider>
    </I18nProvider>
  );
}
