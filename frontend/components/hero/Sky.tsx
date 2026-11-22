"use client";

import { motion, useTransform } from "motion/react";
import type { Parallax } from "@/lib/motion";
import { Scraps } from "./Scraps";

// Six clouds: [left %, top %, width px, height px, drift seconds, parallax depth].
const CLOUDS: ReadonlyArray<readonly [number, number, number, number, number, number]> = [
  [6, 14, 220, 70, 48, 0],
  [62, 8, 300, 90, 70, 1],
  [78, 40, 180, 56, 40, 2],
  [-4, 58, 260, 80, 60, 1],
  [40, 70, 200, 60, 52, 0],
  [86, 78, 240, 74, 64, 2],
];

function Layer({ depth, parallax, kind }: { depth: number; parallax: Parallax; kind: "clouds" | "scraps" }) {
  // Nearer layers shift further, against the pointer.
  const reach = (depth + 1) * 8;
  const x = useTransform(parallax.x, (v) => -v * reach);
  const y = useTransform(parallax.y, (v) => -v * reach);
  return (
    <motion.div className={kind === "scraps" ? "sky-layer scrap-layer" : "sky-layer"} style={{ x, y }}>
      {kind === "scraps" && <Scraps depth={depth} />}
      {CLOUDS.map(([left, top, w, h, seconds, d], i) =>
        kind === "clouds" && d === depth ? (
          <div
            key={i}
            className="cloud"
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: w,
              height: h,
              animationDuration: `${seconds}s`,
              animationDelay: `${(-seconds / 3).toFixed(2)}s`,
            }}
          />
        ) : null,
      )}
    </motion.div>
  );
}

/**
 * The mint sky behind every screen: drifting clouds and tumbling scraps of the bill.
 * `calm` is on while a step card is open: the scraps stop and fade back, the clouds keep drifting.
 */
export function Sky({ parallax, calm = false }: { parallax: Parallax; calm?: boolean }) {
  return (
    <div className={calm ? "sky calm" : "sky"} aria-hidden="true">
      {/* Every cloud sits behind every scrap, as in the demo. */}
      {[0, 1, 2].map((depth) => (
        <Layer key={`c${depth}`} depth={depth} parallax={parallax} kind="clouds" />
      ))}
      {[0, 1, 2].map((depth) => (
        <Layer key={`s${depth}`} depth={depth} parallax={parallax} kind="scraps" />
      ))}
    </div>
  );
}
