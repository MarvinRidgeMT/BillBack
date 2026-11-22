"use client";

import { motion } from "motion/react";
import { useT } from "@/lib/i18n";
import { EASE_OUT } from "@/lib/motion";

export type StepNumber = 1 | 2 | 3 | 4;

/** Four-segment progress bar. The segment for the current step fills as the card arrives. */
export function StepBar({ step, reduce }: { step: StepNumber; reduce: boolean }) {
  const t = useT();
  return (
    <>
      <div className="steps" aria-hidden="true">
        {[1, 2, 3, 4].map((i) => (
          <i key={i}>
            {i <= step && (
              <motion.span
                initial={i === step && !reduce ? { scaleX: 0 } : false}
                animate={{ scaleX: 1 }}
                transition={{ duration: 0.6, ease: EASE_OUT, delay: 0.15 }}
              />
            )}
          </i>
        ))}
      </div>
      <p className="sr-only">{t("step.progress", { n: step })}</p>
    </>
  );
}
