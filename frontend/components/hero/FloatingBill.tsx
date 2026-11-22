"use client";

import { useEffect, useState } from "react";
import { motion, useAnimationControls, useTransform, type Variants } from "motion/react";
import { EASE_DIVE, SNAPPY_SETTLE_MS, SOFT, SOFT_SETTLE_MS, type Parallax } from "@/lib/motion";
import { Stamp } from "./Stamp";

const DRIFT_IN_DELAY_MS = 250;
const PAUSE_BEFORE_STAMP_MS = 250;

// Drifts in from up-right, and dives down and shrinks when the flow starts.
const billVariants: Variants = {
  hidden: { opacity: 0, x: "40%", y: "20%", rotate: 18, scale: 0.8 },
  show: {
    opacity: 1,
    x: "0%",
    y: "0%",
    rotate: 0,
    scale: 1,
    transition: { ...SOFT, delay: DRIFT_IN_DELAY_MS / 1000 },
  },
  exit: {
    opacity: 0,
    x: "0%",
    y: "60%",
    rotate: -4,
    scale: 0.35,
    transition: { duration: 0.65, ease: EASE_DIVE },
  },
};

interface FloatingBillProps {
  parallax: Parallax;
  reduce: boolean;
  stampTop: string;
  stampBottom: string;
}

/** The big object in the middle: a crumpled hospital bill, built in HTML, that gets stamped $0 OWED. */
export function FloatingBill({ parallax, reduce, stampTop, stampBottom }: FloatingBillProps) {
  const [stamped, setStamped] = useState(reduce);
  const [landed, setLanded] = useState(reduce);
  const dip = useAnimationControls();
  const x = useTransform(parallax.x, (v) => v * 14);
  const y = useTransform(parallax.y, (v) => v * 10);

  useEffect(() => {
    if (reduce) return;
    const stampAt = DRIFT_IN_DELAY_MS + SOFT_SETTLE_MS + PAUSE_BEFORE_STAMP_MS;
    const timers = [
      window.setTimeout(() => setStamped(true), stampAt),
      window.setTimeout(() => {
        setLanded(true);
        void dip.start({ y: [0, 6, 0], transition: { duration: 0.22, ease: "easeOut" } });
      }, stampAt + SNAPPY_SETTLE_MS),
    ];
    return () => timers.forEach(window.clearTimeout);
  }, [reduce, dip]);

  return (
    <div className="bill-anchor" aria-hidden="true">
      <motion.div style={{ x, y }}>
        <motion.div className="bill-fill" variants={billVariants}>
          <motion.div
            className="bill-fill"
            animate={landed && !reduce ? { y: [0, -14] } : { y: 0 }}
            transition={
              landed && !reduce
                ? { duration: 3.2, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }
                : { duration: 0 }
            }
          >
            <motion.div className={landed ? "bill struck" : "bill"} style={{ rotate: -8 }} animate={dip}>
              <svg className="creases" viewBox="0 0 100 128" preserveAspectRatio="none">
                <path d="M0 40 L45 52 L100 34" stroke="#C9D2CC" strokeWidth=".5" fill="none" opacity=".7" />
                <path d="M30 0 L38 60 L26 128" stroke="#C9D2CC" strokeWidth=".4" fill="none" opacity=".5" />
                <path d="M0 92 L60 84 L100 98" stroke="#C9D2CC" strokeWidth=".5" fill="none" opacity=".6" />
                <path d="M45 52 L100 34 L100 0 L70 0Z" fill="#0E3B2E" opacity=".035" />
                <path d="M0 92 L60 84 L100 98 L100 128 L0 128Z" fill="#0E3B2E" opacity=".03" />
              </svg>
              {/* A made-up statement. Decoration, hidden from screen readers. */}
              <div className="h">MERCY GENERAL HOSPITAL</div>
              <div className="s">Patient statement · Acct 88-20417</div>
              <div className="bill-row">
                <span>Emergency visit</span>
                <span>$2,940</span>
              </div>
              <div className="bill-row">
                <span>Imaging</span>
                <span>$1,215</span>
              </div>
              <div className="bill-row">
                <span>Lab services</span>
                <span>$657</span>
              </div>
              <div className="due">AMOUNT DUE</div>
              <div className="amt">$4,812.00</div>
            </motion.div>
            <Stamp top={stampTop} bottom={stampBottom} show={stamped} reduce={reduce} />
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  );
}
