import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

function messages(locale) {
  return JSON.parse(readFileSync(new URL(`../messages/${locale}.json`, import.meta.url), "utf8"));
}

const en = messages("en");
const es = messages("es");
const machineLocales = ["vi", "zh-CN", "tl"];
const required = [
  "language.label",
  "language.ai_notice",
  "language.letters_notice",
  "language.official_notice",
  "hero.line1",
  "upload.title",
  "questions.title",
  "result.title.likely_free",
  "insurance.review_title",
  "access.easy_off",
];

test("human-reviewed English and Spanish catalogs have identical keys", () => {
  assert.deepEqual(Object.keys(es).sort(), Object.keys(en).sort());
});

for (const locale of machineLocales) {
  test(`${locale} has the disclosure and critical patient-flow messages`, () => {
    const catalog = messages(locale);
    for (const key of required) assert.equal(typeof catalog[key], "string", `${locale} missing ${key}`);
  });
}
