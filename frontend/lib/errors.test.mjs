// Run: node --test frontend/lib/errors.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { ERROR_CODES, errorKey, isErrorCode, isFileProblem, liveActions } from "./errors.ts";
import en from "../messages/en.json" with { type: "json" };
import es from "../messages/es.json" with { type: "json" };

test("every backend code has an English and a Spanish message", () => {
  for (const code of ERROR_CODES) {
    assert.ok(en[`err.${code}`], `en err.${code}`);
    assert.ok(es[`err.${code}`], `es err.${code}`);
  }
  assert.ok(en["err.network"] && es["err.network"]);
});

test("known codes win; no code falls back by kind", () => {
  assert.equal(errorKey({ code: "ai_unavailable", kind: "unavailable" }), "err.ai_unavailable");
  assert.equal(errorKey({ code: "not_policy", kind: "rejected" }), "err.not_policy");
  assert.equal(errorKey({ code: null, kind: "unavailable" }), "err.network");
  assert.equal(errorKey({ code: null, kind: "failed" }), "err.server_error");
  assert.equal(errorKey({ code: null, kind: "rejected" }), null);
  assert.equal(errorKey({ code: "made_up", kind: "rejected" }), null);
  assert.equal(isErrorCode("bad_url"), true);
  assert.equal(isErrorCode("nope"), false);
});

test("link problems offer the PDF upload first", () => {
  for (const code of ["bad_url", "fetch_failed", "fetch_timeout", "not_pdf", "no_pdf_link"]) {
    assert.deepEqual(liveActions(code), ["upload", "manual"], code);
  }
});

test("unreadable PDFs and reader problems offer typing the limits first", () => {
  for (const code of ["pdf_encrypted", "pdf_empty", "too_short", "not_policy", "ai_invalid"]) {
    assert.equal(liveActions(code)[0], "manual", code);
  }
  assert.deepEqual(liveActions("ai_unavailable"), ["retry", "manual"]);
});

test("live mode off: upload only; unknown or no code: retry or type", () => {
  assert.deepEqual(liveActions("live_off"), ["upload"]);
  assert.deepEqual(liveActions(null), ["retry", "manual"]);
  assert.deepEqual(liveActions("server_error"), ["retry", "manual"]);
});

test("file problems can't be fixed by sending the same file again", () => {
  assert.equal(isFileProblem("bad_file"), true);
  assert.equal(isFileProblem("too_large"), true);
  assert.equal(isFileProblem("ai_unavailable"), false);
  assert.equal(isFileProblem(null), false);
});
