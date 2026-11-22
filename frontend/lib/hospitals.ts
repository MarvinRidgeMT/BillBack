"use client";

import { useEffect, useState } from "react";
import type { Hospital } from "./types";

// Fallback list, used only if GET /api/hospitals can't be reached. The live list comes
// from the backend (every cached policy in cache/policies/index.json).
const FALLBACK: readonly Hospital[] = [
  { slug: "usa-health", name: "USA Health", state: "AL" },
  { slug: "baptist-memorial-health-care-corporation", name: "Baptist Memorial Health Care", state: "MS" },
  { slug: "boys-town-national-research-hospital", name: "Boys Town National Research Hospital", state: "NE" },
  { slug: "fort-healthcare-inc", name: "Fort HealthCare", state: "WI" },
  { slug: "marshfield-clinic-health-system", name: "Marshfield Clinic Health System", state: "WI" },
  { slug: "adena-health-system", name: "Adena Health System", state: "OH" },
];

export const NOT_LISTED = "not-listed";

let cached: Hospital[] | null = null;
let inflight: Promise<Hospital[]> | null = null;

/** Every hospital with a cached policy, sorted by state then name. */
export function loadHospitals(): Promise<Hospital[]> {
  if (cached) return Promise.resolve(cached);
  if (!inflight) {
    inflight = fetch("/api/hospitals", { signal: AbortSignal.timeout(8000) })
      .then((r) => r.json())
      .then((body: { success?: boolean; data?: unknown }) => {
        const rows = Array.isArray(body?.data) ? body.data : [];
        const list = rows
          .filter((h): h is { slug: string; name: string; state: string | null } =>
            !!h && typeof h === "object" && typeof (h as Hospital).slug === "string" && typeof (h as Hospital).name === "string",
          )
          .map((h) => ({ slug: h.slug, name: h.name, state: typeof h.state === "string" ? h.state : "" }))
          .sort((a, b) => (a.state || "ZZ").localeCompare(b.state || "ZZ") || a.name.localeCompare(b.name));
        cached = list.length ? list : [...FALLBACK];
        return cached;
      })
      .catch(() => {
        inflight = null;
        return [...FALLBACK];
      });
  }
  return inflight;
}

export function useHospitals(): Hospital[] {
  const [list, setList] = useState<Hospital[]>(() => cached ?? [...FALLBACK]);
  useEffect(() => {
    let live = true;
    loadHospitals().then((l) => live && setList(l));
    return () => {
      live = false;
    };
  }, []);
  return list;
}

/**
 * Best cached policy for the bill's hospital, from the backend's matcher (name + address + state,
 * score >= 80). Null when nothing matches well, so the patient picks. It is only ever a preselection.
 */
export async function matchHospital(name: string | null | undefined, address?: string | null): Promise<Hospital | null> {
  if (!name || !name.trim()) return null;
  try {
    const res = await fetch("/api/hospitals/match", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ hospital_name: name, hospital_address: address ?? null }),
      signal: AbortSignal.timeout(8000),
    });
    const body = (await res.json()) as { data?: { slug?: string; matched?: boolean } };
    const slug = body?.data?.matched ? body.data.slug : null;
    if (!slug) return null;
    const list = await loadHospitals();
    return list.find((h) => h.slug === slug) ?? null;
  } catch {
    return null;
  }
}

export function hospitalBySlug(slug: string, list: readonly Hospital[] = cached ?? FALLBACK): Hospital | null {
  return list.find((h) => h.slug === slug) ?? null;
}

let liveModeCache: boolean | null = null;

/** Whether the backend allows reading a policy from a pasted link (LIVE_MODE=1). Off unless it says so. */
export function useLiveMode(): boolean {
  const [live, setLive] = useState<boolean>(liveModeCache ?? false);
  useEffect(() => {
    if (liveModeCache !== null) return;
    let alive = true;
    fetch("/api/config", { signal: AbortSignal.timeout(5000) })
      .then((r) => r.json())
      .then((body: { data?: { live_mode?: unknown } }) => {
        liveModeCache = body?.data?.live_mode === true;
        if (alive) setLive(liveModeCache);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  return live;
}
