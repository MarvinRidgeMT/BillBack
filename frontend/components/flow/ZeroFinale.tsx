"use client";

import { motion } from "motion/react";
import { EASE_OUT } from "@/lib/motion";

// The hero's bill scraps, bursting out from the mini bill. [text, angle deg, distance px, spin deg]
const BURST: ReadonlyArray<readonly [string, number, number, number]> = [
  ["$4,8", -150, 170, -200],
  ["DUE", -110, 150, 160],
  ["ACCT", -70, 170, -140],
  ["$657", 180, 160, 220],
  ["88-2", 160, 150, -180],
  ["12.00", 110, 140, 120],
];

export const FLIP_S = 0.7;
const BURST_S = 1.2;

/** Confetti of bill scraps for a "$0 owed" result. Decoration only: aria-hidden, no pointer events, plays once. */
export function ScrapBurst({ delay }: { delay: number }) {
  return (
    <div className="scrap-burst" aria-hidden="true">
      {BURST.map(([text, angle, dist, spin], i) => {
        const rad = (angle * Math.PI) / 180;
        return (
          <motion.span
            key={text}
            className="burst-scrap"
            initial={{ x: 0, y: 0, opacity: 0, rotate: 0, scale: 0.6 }}
            animate={{
              x: [0, Math.cos(rad) * dist * 0.7, Math.cos(rad) * dist],
              y: [0, Math.sin(rad) * dist * 0.7, Math.sin(rad) * dist + 120],
              opacity: [0, 1, 0],
              rotate: [0, spin * 0.6, spin],
              scale: [0.6, 1, 0.9],
            }}
            transition={{ duration: BURST_S, ease: EASE_OUT, delay: delay + i * 0.03, times: [0, 0.35, 1] }}
          >
            {text}
          </motion.span>
        );
      })}
    </div>
  );
}
