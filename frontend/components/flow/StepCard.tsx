"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { motion } from "motion/react";
import { EASE_OUT, SOFT } from "@/lib/motion";
import { StepBar, type StepNumber } from "./StepBar";

/** "hero": the first card glides up from further away as the hero leaves. "step": the calm step change. */
export type Entrance = "hero" | "step";

interface StepCardProps {
  step: StepNumber;
  entrance: Entrance;
  reduce: boolean;
  children: ReactNode;
}

/** One white card on the sky. The old card fades up, the new one glides in. */
export function StepCard({ step, entrance, reduce, children }: StepCardProps) {
  const from = entrance === "hero" ? { opacity: 0, y: 60, scale: 0.97 } : { opacity: 0, y: 22, scale: 1 };
  return (
    <motion.div
      className="app"
      initial={reduce ? false : from}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={reduce ? undefined : { opacity: 0, y: -14, transition: { duration: 0.22, ease: EASE_OUT } }}
      transition={SOFT}
    >
      <section className="panel">
        <StepBar step={step} reduce={reduce} />
        {children}
      </section>
    </motion.div>
  );
}

/** The step's heading. It takes focus when it appears, so keyboard and screen-reader users land on the new step. */
export function StepHeading({ children }: { children: ReactNode }) {
  const ref = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    ref.current?.focus({ preventScroll: true });
  }, []);
  return (
    <h2 ref={ref} tabIndex={-1}>
      {children}
    </h2>
  );
}
