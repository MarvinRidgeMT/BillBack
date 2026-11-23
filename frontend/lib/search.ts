// Client-side hospital filter: used for an empty box and whenever /api/hospitals/search can't answer.
// No imports, so node --test can run it.

export interface Searchable {
  slug: string;
  name: string;
  state: string;
}

export const MAX_RESULTS = 8;

const fold = (s: string) =>
  s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9 ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();

/**
 * A bare 2-letter state lists that state (like the backend). Otherwise every word typed must start a
 * word of the name ("marsh clin" finds "Marshfield Clinic"). Names that start with the query come first.
 */
export function filterHospitals<T extends Searchable>(list: readonly T[], query: string, limit = MAX_RESULTS): T[] {
  const q = fold(query);
  if (!q) return list.slice(0, limit);
  if (/^[a-z]{2}$/.test(q)) {
    const inState = list.filter((h) => h.state.toLowerCase() === q);
    if (inState.length) return inState.slice(0, limit);
  }
  const words = q.split(" ");
  const scored = list
    .map((h) => {
      const name = fold(h.name);
      const nameWords = name.split(" ");
      const all = words.every((w) => nameWords.some((nw) => nw.startsWith(w)) || name.includes(w));
      return all ? { h, rank: name.startsWith(q) ? 0 : 1 } : null;
    })
    .filter((x): x is { h: T; rank: number } => x !== null);
  scored.sort((a, b) => a.rank - b.rank || a.h.name.localeCompare(b.h.name));
  return scored.slice(0, limit).map((x) => x.h);
}
