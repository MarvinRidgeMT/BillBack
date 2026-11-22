"use client";

import { motion } from "motion/react";
import { SNAPPY } from "@/lib/motion";

interface StampProps {
  top: string;
  bottom: string;
  /** Flip to true to slam the stamp down. */
  show: boolean;
  reduce: boolean;
  /** Starting scale of the slam. */
  from?: number;
}

/** The coral circle stamp. It slams in from large and tilted, then rests at 14 degrees. */
export function Stamp({ top, bottom, show, reduce, from = 2.4 }: StampProps) {
  const away = { opacity: 0, rotate: 30, scale: from };
  const landed = { opacity: 1, rotate: 14, scale: 1 };
  return (
    <motion.div
      className="stamp"
      initial={reduce ? false : away}
      animate={show ? landed : away}
      transition={reduce ? { duration: 0 } : SNAPPY}
    >
      <div>
        <b>{top}</b>
        <span>{bottom}</span>
      </div>
    </motion.div>
  );
}
