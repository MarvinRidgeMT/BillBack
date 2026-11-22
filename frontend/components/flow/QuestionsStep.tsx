"use client";

import { useId, useState } from "react";
import { Minus, Plus } from "lucide-react";
import { motion, useAnimationControls } from "motion/react";
import { Button } from "@/components/ui/button";
import { formatIncomeInput, parseIncome } from "@/lib/format";
import { useT } from "@/lib/i18n";
import { SNAPPY } from "@/lib/motion";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const MIN_HOUSEHOLD = 1;
const MAX_HOUSEHOLD = 12;

export interface Answers {
  household: number;
  /** Whole dollars per year. */
  income: number;
}

interface QuestionsStepProps {
  entrance: Entrance;
  reduce: boolean;
  onSubmit: (answers: Answers) => void;
}

/** The two things hospitals decide on: household size and yearly income. */
export function QuestionsStep({ entrance, reduce, onSubmit }: QuestionsStepProps) {
  const t = useT();
  const id = useId();
  const [household, setHousehold] = useState(MIN_HOUSEHOLD);
  const [income, setIncome] = useState("");
  const [showError, setShowError] = useState(false);
  const pop = useAnimationControls();

  function step(by: number) {
    const next = Math.min(MAX_HOUSEHOLD, Math.max(MIN_HOUSEHOLD, household + by));
    if (next === household) return;
    setHousehold(next);
    if (!reduce) void pop.start({ scale: [1.4, 1], transition: SNAPPY });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const dollars = parseIncome(income);
    if (dollars === null) {
      setShowError(true);
      document.getElementById(`${id}-income`)?.focus();
      return;
    }
    onSubmit({ household, income: dollars });
  }

  const invalid = showError && parseIncome(income) === null;

  return (
    <StepCard step={3} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("questions.title")}</StepHeading>
      <p className="sub">{t("questions.sub")}</p>

      <form onSubmit={submit} noValidate>
        <div className="q">
          <span className="q-label" id={`${id}-household`}>
            {t("questions.household")}
          </span>
          <div className="stepper" role="group" aria-labelledby={`${id}-household`}>
            <button
              type="button"
              aria-label={t("questions.fewer")}
              onClick={() => step(-1)}
              disabled={household <= MIN_HOUSEHOLD}
            >
              <Minus size={20} aria-hidden="true" />
            </button>
            <motion.output animate={pop} aria-live="polite">
              {household}
            </motion.output>
            <button
              type="button"
              aria-label={t("questions.more")}
              onClick={() => step(1)}
              disabled={household >= MAX_HOUSEHOLD}
            >
              <Plus size={20} aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="q">
          <label className="q-label" htmlFor={`${id}-income`}>
            {t("questions.income")}
          </label>
          <div className="money" data-invalid={invalid}>
            <span aria-hidden="true">$</span>
            <input
              id={`${id}-income`}
              inputMode="numeric"
              autoComplete="off"
              value={income}
              onChange={(e) => setIncome(formatIncomeInput(e.target.value))}
              aria-required="true"
              aria-invalid={invalid || undefined}
              aria-describedby={invalid ? `${id}-income-error` : undefined}
            />
          </div>
          {invalid && (
            <p className="error-text" id={`${id}-income-error`} role="alert">
              {t("questions.income_error")}
            </p>
          )}
        </div>

        <div className="btn-row">
          <Button type="submit" variant="coral">
            {t("questions.submit")}
          </Button>
        </div>
      </form>
    </StepCard>
  );
}
