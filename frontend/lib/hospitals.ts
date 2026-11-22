import type { Hospital } from "./types";

// The hospitals whose policies are cached (cache/policies/*.json, data/policies/sources.csv).
// Hardcoded until the backend has GET /api/hospitals (asked for in NOTES_FOR_TEAM.md).
export const HOSPITALS: readonly (Hospital & { aliases?: readonly string[] })[] = [
  { slug: "usa-health", name: "USA Health", state: "AL", aliases: ["University of South Alabama"] },
  { slug: "baptist-memorial-health-care-corporation", name: "Baptist Memorial Health Care", state: "MS" },
  { slug: "boys-town-national-research-hospital", name: "Boys Town National Research Hospital", state: "NE" },
  { slug: "fort-healthcare-inc", name: "Fort HealthCare", state: "WI" },
  { slug: "marshfield-clinic-health-system", name: "Marshfield Clinic Health System", state: "WI" },
  { slug: "adena-health-system", name: "Adena Health System", state: "OH" },
];

export const NOT_LISTED = "not-listed";
export const MATCH_THRESHOLD = 0.5;

// Words that say nothing about which hospital it is.
const FILLER = new Set([
  "inc", "the", "corporation", "corp", "llc", "of", "and", "at", "for",
  "hospital", "hospitals", "health", "healthcare", "care", "system", "systems",
  "medical", "center", "centre", "clinic", "clinics",
]);

function tokens(name: string): Set<string> {
  const words = name
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((w) => w && !FILLER.has(w));
  return new Set(words);
}

/** Token overlap (Dice) between two names, 0..1, ignoring filler words. */
function overlap(a: Set<string>, b: Set<string>): number {
  if (a.size === 0 || b.size === 0) return 0;
  let shared = 0;
  for (const w of a) if (b.has(w)) shared += 1;
  return (2 * shared) / (a.size + b.size);
}

/**
 * Best guess at which cached hospital a bill is from. Returns null when nothing
 * scores well, so the patient has to choose. It is only ever a preselection:
 * the patient can always change it.
 */
export function matchHospital(billName: string | null | undefined): Hospital | null {
  if (!billName) return null;
  const bill = tokens(billName);
  let best: Hospital | null = null;
  let bestScore = 0;
  for (const hospital of HOSPITALS) {
    const names = [hospital.name, ...(hospital.aliases ?? [])];
    const score = Math.max(...names.map((n) => overlap(bill, tokens(n))));
    if (score > bestScore) {
      best = hospital;
      bestScore = score;
    }
  }
  return bestScore >= MATCH_THRESHOLD ? best : null;
}

export function hospitalBySlug(slug: string): Hospital | null {
  return HOSPITALS.find((h) => h.slug === slug) ?? null;
}
