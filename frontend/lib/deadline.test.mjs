// Run: node --test frontend/lib/deadline.test.mjs   (Node 23.6+ strips the TypeScript types)
import assert from "node:assert/strict";
import test from "node:test";
import { buildIcs, computeDeadline, parseServiceDate, reminderDate } from "./deadline.ts";

const iso = (d) => d.toISOString().slice(0, 10);
const NOW = new Date(2026, 10, 22, 12); // Nov 22, 2026 local noon

test("parses ISO and US dates, rejects impossible ones", () => {
  assert.equal(iso(parseServiceDate("2026-08-14")), "2026-08-14");
  assert.equal(iso(parseServiceDate("08/14/2026")), "2026-08-14");
  assert.equal(iso(parseServiceDate("8/4/26")), "2026-08-04");
  assert.equal(iso(parseServiceDate("Aug 14, 2026")), "2026-08-14");
  assert.equal(iso(parseServiceDate("14 ago 2026")), "2026-08-14");
  assert.equal(iso(parseServiceDate("14 de ago. de 2026")), "2026-08-14");
  assert.equal(parseServiceDate("02/30/2026"), null);
  assert.equal(parseServiceDate("next Tuesday"), null);
  assert.equal(parseServiceDate(""), null);
  assert.equal(parseServiceDate(null), null);
});

test("date of service: exact deadline and days left", () => {
  const d = computeDeadline("2026-08-14", 240, "date_of_service", NOW);
  assert.equal(d.kind, "from_service");
  assert.equal(iso(d.date), "2027-04-11");
  assert.equal(d.daysLeft, 140);
});

test("first bill after discharge: conservative 'at least' date", () => {
  const d = computeDeadline("08/14/2026", 240, "first_post_discharge_billing_statement", NOW);
  assert.equal(d.kind, "at_least");
  assert.equal(iso(d.date), "2027-04-11");
});

test("leap years count Feb 29", () => {
  assert.equal(iso(computeDeadline("2028-02-01", 30, "date_of_service", NOW).date), "2028-03-02");
  assert.equal(iso(computeDeadline("2027-02-01", 30, "date_of_service", NOW).date), "2027-03-03");
  assert.equal(iso(parseServiceDate("02/29/2028")), "2028-02-29");
  assert.equal(parseServiceDate("02/29/2027"), null);
});

test("missing window or date", () => {
  assert.equal(computeDeadline("2026-08-14", null, null, NOW).kind, "none");
  assert.equal(computeDeadline(null, 240, "date_of_service", NOW).kind, "no_date");
  assert.equal(computeDeadline("garbage", 240, "date_of_service", NOW).daysLeft, null);
});

test("reminder is 30 days before, at least a week out, never after the deadline", () => {
  assert.equal(iso(reminderDate(new Date(Date.UTC(2027, 3, 11)), NOW)), "2027-03-12");
  assert.equal(iso(reminderDate(new Date(Date.UTC(2026, 11, 10)), NOW)), "2026-11-29");
  assert.equal(iso(reminderDate(new Date(Date.UTC(2026, 10, 25)), NOW)), "2026-11-25");
});

test("ics has two all-day events with escaped text and CRLF", () => {
  const ics = buildIcs({
    hospital: "Fort HealthCare, Inc.",
    slug: "fort",
    deadline: new Date(Date.UTC(2027, 3, 11)),
    reminder: new Date(Date.UTC(2027, 2, 12)),
    description: "Account 123; likely eligible, not a guarantee",
    now: NOW,
  });
  assert.equal((ics.match(/BEGIN:VEVENT/g) ?? []).length, 2);
  assert.ok(ics.includes("DTSTART;VALUE=DATE:20270411"));
  assert.ok(ics.includes("DTEND;VALUE=DATE:20270412"));
  assert.ok(ics.includes("Fort HealthCare\\, Inc."));
  assert.ok(ics.includes("Account 123\\; likely eligible\\, not a guarantee"));
  assert.ok(ics.includes("\r\n"));
});
