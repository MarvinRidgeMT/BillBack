"use client";

import { AnimatePresence, MotionConfig } from "motion/react";
import { HowItWorks } from "@/components/HowItWorks";
import { Nav } from "@/components/Nav";
import { Hero } from "@/components/hero/Hero";
import { Sky } from "@/components/hero/Sky";
import { I18nProvider } from "@/lib/i18n";
import { useParallax, useReducedMotionPref } from "@/lib/motion";

function FlowInner() {
  const reduce = useReducedMotionPref();
  const parallax = useParallax(!reduce);

  return (
    <MotionConfig reducedMotion="user">
      <div className="stage">
        <Sky parallax={parallax} />
        <Nav />
        <AnimatePresence mode="wait">
          <Hero key={reduce ? "hero-still" : "hero"} onStart={() => {}} parallax={parallax} reduce={reduce} />
        </AnimatePresence>
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
