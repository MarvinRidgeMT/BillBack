// Run: node --test frontend/lib/notListedDraft.test.mjs
import assert from "node:assert/strict";
import test from "node:test";
import { nextNotListedDraft } from "./notListedDraft.ts";

const EMPTY = { url: "", hospital: "", state: "", free: "", discount: "" };
const madRiver = { hospital_name: "Mad River Community Hospital", hospital_address: "100 Example St, Arcata, CA 95521" };
const other = { hospital_name: "Lakeview Regional", hospital_address: "9 Lake Rd, Austin, TX 78701" };

test("first visit fills the hospital and state from the bill", () => {
  assert.deepEqual(nextNotListedDraft(EMPTY, null, madRiver, "CA"), { ...EMPTY, hospital: madRiver.hospital_name, state: "CA" });
});

test("coming back with the same bill keeps what the patient typed", () => {
  const typed = { url: "https://x.org/fap.pdf", hospital: "Mad River Hospital", state: "CA", free: "400", discount: "" };
  assert.deepEqual(nextNotListedDraft(typed, madRiver, madRiver, "CA"), typed);
});

test("a different hospital's bill starts fresh (Graphify review: the old hospital used to carry over)", () => {
  const typed = { url: "https://x.org/fap.pdf", hospital: "Mad River Community Hospital", state: "CA", free: "400", discount: "" };
  assert.deepEqual(nextNotListedDraft(typed, madRiver, other, "TX"), { ...EMPTY, hospital: "Lakeview Regional", state: "TX" });
});
