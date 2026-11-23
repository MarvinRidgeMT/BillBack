// Dev-only, in-memory timing log for this browser tab. Module-level state: nothing is stored,
// nothing is sent, and a refresh empties it. Read by DevPanel (?dev=1). No imports, so node --test can run it.

export const TIMING_KEYS = ["bill_read_s", "policy_read_s", "rules_s", "packet_s"] as const;
export type TimingKey = (typeof TIMING_KEYS)[number];

export interface TimingEntry {
  key: TimingKey;
  seconds: number;
}

export interface TimingSnapshot {
  /** Newest last, at most MAX_ENTRIES. */
  entries: readonly TimingEntry[];
  /** How many bills were read this session. */
  bills: number;
  /** How many bill fields came back under the confidence threshold, across those bills. */
  lowConfidence: number;
  /** How many bill fields were read in all. */
  fields: number;
}

const MAX_ENTRIES = 50;
const EMPTY: TimingSnapshot = { entries: [], bills: 0, lowConfidence: 0, fields: 0 };

let snapshot: TimingSnapshot = EMPTY;
const listeners = new Set<() => void>();

function set(next: TimingSnapshot): void {
  snapshot = next;
  listeners.forEach((l) => l());
}

/** Seconds from the backend's `timings` (or the X-Packet-Seconds header). Bad numbers are ignored. */
export function recordTiming(key: TimingKey, seconds: unknown): void {
  const s = typeof seconds === "string" ? Number(seconds) : seconds;
  if (typeof s !== "number" || !Number.isFinite(s) || s < 0) return;
  set({ ...snapshot, entries: [...snapshot.entries, { key, seconds: s }].slice(-MAX_ENTRIES) });
}

/** One bill read: count the fields and how many were under `threshold`. Only counts, never values. */
export function recordBillRead(confidences: readonly number[], threshold = 0.8): void {
  const low = confidences.filter((c) => !(c >= threshold)).length;
  set({
    ...snapshot,
    bills: snapshot.bills + 1,
    lowConfidence: snapshot.lowConfidence + low,
    fields: snapshot.fields + confidences.length,
  });
}

export function getTimings(): TimingSnapshot {
  return snapshot;
}

export function getServerTimings(): TimingSnapshot {
  return EMPTY;
}

export function subscribeTimings(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Average seconds per key, for the panel. Keys with no entries are left out. */
export function averages(entries: readonly TimingEntry[]): Partial<Record<TimingKey, { avg: number; n: number }>> {
  const out: Partial<Record<TimingKey, { avg: number; n: number }>> = {};
  for (const key of TIMING_KEYS) {
    const xs = entries.filter((e) => e.key === key).map((e) => e.seconds);
    if (xs.length) out[key] = { avg: xs.reduce((a, b) => a + b, 0) / xs.length, n: xs.length };
  }
  return out;
}

/** For tests. */
export function resetTimings(): void {
  set(EMPTY);
}
