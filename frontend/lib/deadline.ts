// Application deadline math and the .ics reminder. Plain date arithmetic in the browser; nothing is sent or stored.

export type DeadlineKind = "from_service" | "at_least" | "none" | "no_date";

export interface Deadline {
  kind: DeadlineKind;
  /** UTC midnight of the deadline day, or null. */
  date: Date | null;
  days: number | null;
  service: Date | null;
  /** Whole days from today to the deadline (0 = today, negative = passed). */
  daysLeft: number | null;
}

const DAY_MS = 86_400_000;

function utcDay(y: number, m: number, d: number): Date | null {
  const date = new Date(Date.UTC(y, m - 1, d));
  return date.getUTCFullYear() === y && date.getUTCMonth() === m - 1 && date.getUTCDate() === d ? date : null;
}

const MONTHS: Record<string, number> = {
  jan: 1, ene: 1, feb: 2, mar: 3, apr: 4, abr: 4, may: 5, jun: 6, jul: 7, aug: 8, ago: 8,
  sep: 9, set: 9, oct: 10, nov: 11, dec: 12, dic: 12,
};

/** "2026-08-14", "08/14/2026", "8/14/26", "Aug 14, 2026" or "14 ago 2026". Anything else -> null (we never guess a date). */
export function parseServiceDate(text: string | null | undefined): Date | null {
  if (!text) return null;
  const s = text.trim();
  let m = /^(\d{4})-(\d{1,2})-(\d{1,2})$/.exec(s);
  if (m) return utcDay(Number(m[1]), Number(m[2]), Number(m[3]));
  m = /^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})$/.exec(s);
  if (m) {
    const year = m[3].length === 2 ? 2000 + Number(m[3]) : Number(m[3]);
    return utcDay(year, Number(m[1]), Number(m[2]));
  }
  m = /^([a-z]{3})[a-z]*\.?\s+(\d{1,2}),?\s+(\d{4})$/i.exec(s);
  if (m && MONTHS[m[1].toLowerCase()]) return utcDay(Number(m[3]), MONTHS[m[1].toLowerCase()], Number(m[2]));
  m = /^(\d{1,2})\s+(?:de\s+)?([a-z]{3})[a-z]*\.?\s+(?:de\s+)?(\d{4})$/i.exec(s);
  if (m && MONTHS[m[2].toLowerCase()]) return utcDay(Number(m[3]), MONTHS[m[2].toLowerCase()], Number(m[1]));
  return null;
}

export function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * DAY_MS);
}

export function todayUtc(now: Date = new Date()): Date {
  return new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
}

/**
 * From the date of service or discharge -> the real deadline.
 * From the first bill after discharge (date unknown to us) -> a conservative "at least until" date:
 * the first bill always comes after the visit, so service date + days is never later than the real deadline.
 */
export function computeDeadline(
  serviceDate: string | null | undefined,
  days: number | null | undefined,
  countedFrom: string | null | undefined,
  now: Date = new Date(),
): Deadline {
  const service = parseServiceDate(serviceDate);
  if (!days || days <= 0) return { kind: "none", date: null, days: null, service, daysLeft: null };
  if (!service) return { kind: "no_date", date: null, days, service: null, daysLeft: null };
  const date = addDays(service, days);
  const daysLeft = Math.round((date.getTime() - todayUtc(now).getTime()) / DAY_MS);
  const exact = countedFrom === "date_of_service" || countedFrom === "discharge";
  return { kind: exact ? "from_service" : "at_least", date, days, service, daysLeft };
}

/** Send-by reminder: 30 days before the deadline, but at least a week from today, and never after the deadline. */
export function reminderDate(deadline: Date, now: Date = new Date()): Date {
  const thirtyBefore = addDays(deadline, -30);
  const weekOut = addDays(todayUtc(now), 7);
  const pick = thirtyBefore.getTime() > weekOut.getTime() ? thirtyBefore : weekOut;
  return pick.getTime() > deadline.getTime() ? deadline : pick;
}

function icsDate(d: Date): string {
  return d.toISOString().slice(0, 10).replace(/-/g, "");
}

function icsText(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/;/g, "\\;").replace(/,/g, "\\,").replace(/\r?\n/g, "\\n");
}

export interface IcsInput {
  hospital: string;
  slug: string;
  deadline: Date;
  reminder: Date;
  description: string;
  now?: Date;
}

/** Two all-day events. CRLF line endings, as RFC 5545 requires. */
export function buildIcs({ hospital, slug, deadline, reminder, description, now = new Date() }: IcsInput): string {
  const stamp = now.toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
  const event = (id: string, day: Date, summary: string) => [
    "BEGIN:VEVENT",
    `UID:billback-${id}-${slug}-${icsDate(day)}@billback`,
    `DTSTAMP:${stamp}`,
    `DTSTART;VALUE=DATE:${icsDate(day)}`,
    `DTEND;VALUE=DATE:${icsDate(addDays(day, 1))}`,
    `SUMMARY:${icsText(summary)}`,
    `DESCRIPTION:${icsText(description)}`,
    "END:VEVENT",
  ];
  return [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//BillBack//Charity care reminder//EN",
    "CALSCALE:GREGORIAN",
    ...event("send", reminder, `Send charity care application to ${hospital}`),
    ...event("deadline", deadline, `Charity care deadline: ${hospital}`),
    "END:VCALENDAR",
    "",
  ].join("\r\n");
}
