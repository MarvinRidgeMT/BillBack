"use client";

import { motion, type Variants } from "motion/react";
import { useT } from "@/lib/i18n";
import { EASE_OUT, SNAPPY, type Parallax } from "@/lib/motion";
import { FloatingBill } from "./FloatingBill";

// Where the $2.7B figure comes from.
const SOURCE_URL = "https://kffhealthnews.org/news/patients-eligible-for-charity-care-instead-get-big-bills";

const line = (delay: number): Variants => ({
  hidden: { opacity: 0, y: 40 },
  show: { opacity: 1, y: 0, transition: { duration: 0.9, ease: EASE_OUT, delay } },
  exit: { opacity: 0, y: -60, transition: { duration: 0.6, ease: EASE_OUT } },
});

const side = (delay: number): Variants => ({
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.7, ease: EASE_OUT, delay } },
  exit: { opacity: 0, scale: 0.9, transition: { duration: 0.35, ease: EASE_OUT } },
});

const cta: Variants = {
  hidden: { scale: 0 },
  show: { scale: 1, transition: { ...SNAPPY, delay: 0.7 } },
  exit: { opacity: 0, scale: 0.9, transition: { duration: 0.35, ease: EASE_OUT } },
};

interface HeroProps {
  onStart: () => void;
  parallax: Parallax;
  reduce: boolean;
}

/** Poster hero: the headline, the floating bill stamped $0 OWED, and the coral CTA. */
export function Hero({ onStart, parallax, reduce }: HeroProps) {
  const t = useT();
  return (
    <motion.section
      className="hero"
      aria-labelledby="hero-title"
      initial={reduce ? false : "hidden"}
      animate="show"
      exit={reduce ? undefined : "exit"}
    >
      <h1 id="hero-title">
        <motion.span className="l1" variants={line(0)}>
          {t("hero.line1")}
        </motion.span>{" "}
        <motion.span className="l2" variants={line(0.12)}>
          {t("hero.line2")}
        </motion.span>
      </h1>

      <FloatingBill
        parallax={parallax}
        reduce={reduce}
        stampTop={t("result.stamp.free_top")}
        stampBottom={t("result.stamp.free_bottom")}
      />

      <motion.p className="side l" variants={side(0.5)}>
        {t("hero.side_left_1")}{" "}
        <br />
        {t("hero.side_left_2")}
      </motion.p>
      <motion.p className="side r" variants={side(0.6)}>
        {t("hero.side_right_1")}{" "}
        <br />
        {t("hero.side_right_2")}
        <br />
        <a className="source-link" href={SOURCE_URL} target="_blank" rel="noopener noreferrer">
          {t("hero.source")}
          <span className="sr-only"> {t("result.new_tab")}</span>
        </a>
      </motion.p>

      <motion.div className="cta-wrap" variants={cta}>
        <button type="button" className="cta" id="hero-cta" onClick={onStart}>
          {t("hero.cta_1")}
          <br />
          {t("hero.cta_2")}
        </button>
      </motion.div>
    </motion.section>
  );
}
