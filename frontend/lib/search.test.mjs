// Run: node --test frontend/lib/search.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { filterHospitals } from "./search.ts";

const LIST = [
  { slug: "usa-health", name: "USA Health", state: "AL" },
  { slug: "fort", name: "Fort HealthCare", state: "WI" },
  { slug: "marsh", name: "Marshfield Clinic Health System", state: "WI" },
  { slug: "boys", name: "Boys Town National Research Hospital", state: "NE" },
  { slug: "san-jose", name: "Hospital San José", state: "TX" },
];
const slugs = (xs) => xs.map((h) => h.slug);

test("empty query lists the first hospitals", () => {
  assert.equal(filterHospitals(LIST, "").length, 5);
  assert.equal(filterHospitals(LIST, "  ", 2).length, 2);
});

test("a state code lists that state", () => {
  assert.deepEqual(slugs(filterHospitals(LIST, "wi")), ["fort", "marsh"]);
});

test("word prefixes match, name-start first, accents ignored", () => {
  assert.deepEqual(slugs(filterHospitals(LIST, "marsh clin")), ["marsh"]);
  assert.deepEqual(slugs(filterHospitals(LIST, "health")), ["fort", "marsh", "usa-health"]);
  assert.deepEqual(slugs(filterHospitals(LIST, "hospital")), ["san-jose", "boys"]);
  assert.deepEqual(slugs(filterHospitals(LIST, "jose")), ["san-jose"]);
  assert.deepEqual(slugs(filterHospitals(LIST, "boys town")), ["boys"]);
  assert.deepEqual(filterHospitals(LIST, "zzz"), []);
});

test("results are capped", () => {
  assert.equal(filterHospitals(LIST, "h", 2).length, 2);
});
