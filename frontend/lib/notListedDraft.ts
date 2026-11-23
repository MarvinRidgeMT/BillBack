// No imports, so node --test can run it (like lib/validation.ts).

/** Same shape as NotListedDraft in components/flow/NotListed.tsx (kept here so it can be unit-tested with node). */
export interface DraftFields {
  url: string;
  hospital: string;
  state: string;
  free: string;
  discount: string;
}

interface BillHospital {
  hospital_name: string;
  hospital_address: string;
}

const sameHospital = (a: BillHospital | null, b: BillHospital): boolean =>
  !!a && a.hospital_name.trim() === b.hospital_name.trim() && a.hospital_address.trim() === b.hospital_address.trim();

/**
 * The "my hospital isn't listed" draft when the patient arrives with a bill.
 * Same bill as last time: keep what they typed. A different hospital's bill: start fresh from that bill,
 * so an old hospital name, state, link or limits are never carried into the new hospital's policy check.
 */
export function nextNotListedDraft(
  prev: DraftFields,
  prevBill: BillHospital | null,
  bill: BillHospital,
  billState: string | null,
): DraftFields {
  const fromBill = { hospital: bill.hospital_name, state: billState ?? "" };
  if (!sameHospital(prevBill, bill)) return { url: "", free: "", discount: "", ...fromBill };
  return { ...prev, hospital: prev.hospital || fromBill.hospital, state: prev.state || fromBill.state };
}
