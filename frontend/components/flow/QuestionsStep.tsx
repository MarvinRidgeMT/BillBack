"use client";

import { useId, useState } from "react";
import { Minus, Plus } from "lucide-react";
import { motion, useAnimationControls } from "motion/react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { formatIncomeInput } from "@/lib/format";
import { useT, type MessageKey } from "@/lib/i18n";
import { SNAPPY } from "@/lib/motion";
import {
  checkHousehold,
  checkIncome,
  MAX_HOUSEHOLD,
  MIN_HOUSEHOLD,
  type HouseholdError,
  type IncomeError,
} from "@/lib/validation";
import { BenefitsQuestion, type Benefits } from "./BenefitsQuestion";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

export interface Answers {
  household: number;
  /** Whole dollars per year. */
  income: number;
  /** Optional SNAP/Medicaid/WIC answer. Shown on the result only; it never changes the eligibility call. */
  benefits: Benefits;
}

/** The form exactly as typed, so going back shows the same answers. In memory only. */
export interface AnswersDraft {
  household: string;
  income: string;
  benefits: Benefits;
}

export const EMPTY_DRAFT: AnswersDraft = { household: "1", income: "", benefits: "skip" };

const HOUSEHOLD_ERRORS: Record<HouseholdError, MessageKey> = {
  blank: "questions.household_blank",
  zero: "questions.household_zero",
  too_many: "questions.household_too_many",
};
const INCOME_ERRORS: Record<IncomeError, MessageKey> = {
  blank: "questions.income_error",
  negative: "questions.income_negative",
  too_high: "questions.income_too_high",
};

interface QuestionsStepProps {
  entrance: Entrance;
  reduce: boolean;
  initial?: AnswersDraft;
  /** Show the field errors straight away (the /states page). */
  revealErrors?: boolean;
  onSubmit: (answers: Answers, draft: AnswersDraft) => void;
  onBack?: (draft: AnswersDraft) => void;
}

/** "41000" or "-41000" -> "41,000" / "-41,000": the minus is kept so we can say why it won't work. */
function formatIncomeTyping(raw: string): string {
  const negative = /^\s*-/.test(raw);
  return (negative ? "-" : "") + formatIncomeInput(raw);
}

/** The two things hospitals decide on: household size and yearly income. */
export function QuestionsStep({ entrance, reduce, initial = EMPTY_DRAFT, revealErrors = false, onSubmit, onBack }: QuestionsStepProps) {
  const t = useT();
  const id = useId();
  const [household, setHousehold] = useState(initial.household);
  const [income, setIncome] = useState(initial.income);
  const [benefits, setBenefits] = useState<Benefits>(initial.benefits);
  const [tried, setTried] = useState(revealErrors);
  const pop = useAnimationControls();

  const householdCheck = checkHousehold(household);
  const incomeCheck = checkIncome(income);
  const householdError = tried && !householdCheck.ok ? HOUSEHOLD_ERRORS[householdCheck.error] : null;
  const incomeError = tried && !incomeCheck.ok ? INCOME_ERRORS[incomeCheck.error] : null;
  const count = householdCheck.ok ? householdCheck.value : null;
  const draft = (): AnswersDraft => ({ household, income, benefits });

  // The buttons use aria-disabled, not disabled, so focus stays put at the limits.
  function step(by: number) {
    const current = /^\d+$/.test(household.trim()) ? Number(household.trim()) : 0;
    const next = Math.min(MAX_HOUSEHOLD, Math.max(MIN_HOUSEHOLD, current + by));
    if (next === current) return;
    setHousehold(String(next));
    if (!reduce) void pop.start({ scale: [1.25, 1], transition: SNAPPY });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!householdCheck.ok || !incomeCheck.ok) {
      setTried(true);
      document.getElementById(!householdCheck.ok ? `${id}-household-input` : `${id}-income`)?.focus();
      return;
    }
    onSubmit({ household: householdCheck.value, income: incomeCheck.value, benefits }, draft());
  }

  return (
    <StepCard step={3} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("questions.title")}</StepHeading>
      <p className="sub">{t("questions.sub")}</p>

      <form onSubmit={submit} noValidate>
        <div className="q">
          <label className="q-label" id={`${id}-household`} htmlFor={`${id}-household-input`}>
            {t("questions.household")}
          </label>
          <div className="stepper" role="group" aria-labelledby={`${id}-household`} data-invalid={!!householdError}>
            <button
              type="button"
              aria-label={t("questions.fewer")}
              onClick={() => step(-1)}
              aria-disabled={count !== null && count <= MIN_HOUSEHOLD}
            >
              <Minus size={20} aria-hidden="true" />
            </button>
            <motion.input
              animate={pop}
              id={`${id}-household-input`}
              className="stepper-input"
              inputMode="numeric"
              autoComplete="off"
              maxLength={3}
              value={household}
              onChange={(e) => setHousehold(e.target.value.replace(/[^\d]/g, ""))}
              aria-required="true"
              aria-invalid={householdError ? true : undefined}
              aria-describedby={householdError ? `${id}-household-error` : undefined}
            />
            <button
              type="button"
              aria-label={t("questions.more")}
              onClick={() => step(1)}
              aria-disabled={count !== null && count >= MAX_HOUSEHOLD}
            >
              <Plus size={20} aria-hidden="true" />
            </button>
          </div>
          {householdError && (
            <StatusBanner variant="error" size="compact" id={`${id}-household-error`}>
              {t(householdError)}
            </StatusBanner>
          )}
        </div>

        <div className="q">
          <label className="q-label" htmlFor={`${id}-income`}>
            {t("questions.income")}
          </label>
          <div className="money" data-invalid={!!incomeError}>
            <span aria-hidden="true">$</span>
            <input
              id={`${id}-income`}
              inputMode="numeric"
              autoComplete="off"
              value={income}
              onChange={(e) => setIncome(formatIncomeTyping(e.target.value))}
              aria-required="true"
              aria-invalid={incomeError ? true : undefined}
              aria-describedby={incomeError ? `${id}-income-error` : undefined}
            />
          </div>
          {incomeError && (
            <StatusBanner variant="error" size="compact" id={`${id}-income-error`}>
              {t(incomeError)}
            </StatusBanner>
          )}
        </div>

        <BenefitsQuestion value={benefits} onChange={setBenefits} />

        <div className="btn-row">
          <Button type="submit" variant="coral">
            {t("questions.submit")}
          </Button>
          {onBack && (
            <Button type="button" variant="ghost" onClick={() => onBack(draft())}>
              {t("questions.back")}
            </Button>
          )}
        </div>
      </form>
    </StepCard>
  );
}
