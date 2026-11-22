"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useMotionValue, useSpring, type MotionValue } from "motion/react";

// Reference springs from the approved demo (docs/design/hero-demo.html).
export const SNAPPY = { type: "spring", stiffness: 180, damping: 12 } as const;
export const SOFT = { type: "spring", stiffness: 120, damping: 16 } as const;
export const EASE_OUT = [0.22, 1, 0.36, 1] as const;
export const EASE_DIVE = [0.6, 0, 0.3, 1] as const;

// How long each demo spring takes to settle. The hero intro is sequenced on these.
export const SOFT_SETTLE_MS = 780;
export const SNAPPY_SETTLE_MS = 1030;

const QUERY = "(prefers-reduced-motion: reduce)";

function subscribe(onChange: () => void) {
  const mq = window.matchMedia(QUERY);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

/** True when the person asked the system to reduce motion. False on the server. */
export function useReducedMotionPref(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(QUERY).matches,
    () => false,
  );
}

export interface Parallax {
  x: MotionValue<number>;
  y: MotionValue<number>;
}

/** Pointer position as -0.5..0.5 on each axis, lightly sprung. Stays at 0 when disabled or on touch. */
export function useParallax(enabled: boolean): Parallax {
  const rawX = useMotionValue(0);
  const rawY = useMotionValue(0);
  const x = useSpring(rawX, { stiffness: 170, damping: 24, mass: 0.5 });
  const y = useSpring(rawY, { stiffness: 170, damping: 24, mass: 0.5 });

  useEffect(() => {
    if (!enabled || !window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
      rawX.jump(0);
      rawY.jump(0);
      return;
    }
    const onMove = (e: PointerEvent) => {
      rawX.set(e.clientX / window.innerWidth - 0.5);
      rawY.set(e.clientY / window.innerHeight - 0.5);
    };
    window.addEventListener("pointermove", onMove, { passive: true });
    return () => window.removeEventListener("pointermove", onMove);
  }, [enabled, rawX, rawY]);

  return { x, y };
}
