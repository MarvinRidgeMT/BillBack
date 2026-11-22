// The application packet: a three-page PDF built in the browser with pdf-lib.
// Nothing is uploaded or stored. Every number on it is one the patient typed or
// confirmed, or one the backend returned. Nothing is calculated here.

import type { PDFFont, PDFPage } from "pdf-lib";
import type { MessageKey, Translate } from "./i18n";
import { CONFIRM_THRESHOLD, type ConfirmedBill, type EligibilityData } from "./types";

export interface PacketInput {
  /** Translator for the language the packet should be written in. */
  t: Translate;
  lang: "en" | "es";
  bill: ConfirmedBill;
  household: number;
  /** Whole dollars per year, as the patient typed it. */
  income: number;
  data: EligibilityData;
}

/** The packet is only offered when the result is likely free or likely discounted. */
export function canMakePacket(data: EligibilityData): boolean {
  return data.status === "likely_free" || data.status === "likely_discounted";
}

const PAGE_W = 612; // US Letter, in points
const PAGE_H = 792;
const MARGIN = 64;
const CONTENT_W = PAGE_W - MARGIN * 2;
const FOOTER_TOP = 70;
const LINE = 1.42;

const dollars = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

// Characters the built-in PDF fonts can't draw, swapped for ones they can.
const SWAPS: Record<string, string> = {
  "‐": "-",
  "‑": "-",
  "−": "-",
  "≤": "<=",
  "≥": ">=",
  "→": "->",
  "­": "",
};

function safeHttpUrl(url: string | null): string {
  if (!url) return "";
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : "";
  } catch {
    return "";
  }
}

export async function buildPacket({ t, lang, bill, household, income, data }: PacketInput): Promise<Uint8Array> {
  const { PDFDocument, StandardFonts, rgb } = await import("pdf-lib");
  const doc = await PDFDocument.create();
  const regular = await doc.embedFont(StandardFonts.Helvetica);
  const bold = await doc.embedFont(StandardFonts.HelveticaBold);

  const INK = rgb(14 / 255, 59 / 255, 46 / 255);
  const BODY = rgb(0.1, 0.12, 0.11);
  const SOFT = rgb(0.3, 0.36, 0.33);
  const RULE = rgb(0.72, 0.78, 0.75);
  const TINT = rgb(1, 0.93, 0.9);

  // Bill text and policy quotes can hold anything. Keep what the font can draw.
  const drawable = new Set(regular.getCharacterSet());
  const clean = (text: string): string =>
    Array.from(text.normalize("NFC").replace(/\s+/g, " ").trim())
      .map((ch) => SWAPS[ch] ?? (drawable.has(ch.codePointAt(0) ?? 0) ? ch : "?"))
      .join("");

  function wrap(text: string, font: PDFFont, size: number, width: number): string[] {
    const lines: string[] = [];
    let line = "";
    const fits = (s: string) => font.widthOfTextAtSize(s, size) <= width;
    for (let word of clean(text).split(" ")) {
      // A word longer than the line (a long URL) is broken by letter.
      while (!fits(word)) {
        if (line) {
          lines.push(line);
          line = "";
        }
        let cut = word.length - 1;
        while (cut > 1 && !fits(word.slice(0, cut))) cut -= 1;
        lines.push(word.slice(0, cut));
        word = word.slice(cut);
      }
      const next = line ? `${line} ${word}` : word;
      if (fits(next)) {
        line = next;
      } else {
        lines.push(line);
        line = word;
      }
    }
    if (line) lines.push(line);
    return lines;
  }

  let page!: PDFPage;
  let y = 0;
  const newPage = () => {
    page = doc.addPage([PAGE_W, PAGE_H]);
    y = PAGE_H - MARGIN;
  };
  const room = (height: number) => {
    if (y - height < FOOTER_TOP) newPage();
  };

  interface TextOptions {
    size?: number;
    font?: PDFFont;
    color?: ReturnType<typeof rgb>;
    gap?: number;
    x?: number;
    width?: number;
  }
  function write(text: string, opts: TextOptions = {}) {
    const { size = 11.5, font = regular, color = BODY, gap = 9, x = MARGIN, width = CONTENT_W - (x - MARGIN) } = opts;
    for (const line of wrap(text, font, size, width)) {
      room(size * LINE);
      y -= size * LINE;
      page.drawText(line, { x, y, size, font, color });
    }
    y -= gap;
  }
  const title = (text: string) => {
    write(text, { size: 22, font: bold, color: INK, gap: 6 });
    page.drawLine({ start: { x: MARGIN, y }, end: { x: PAGE_W - MARGIN, y }, thickness: 1.5, color: INK });
    y -= 16;
  };
  const heading = (text: string) => {
    y -= 6;
    write(text, { size: 13, font: bold, color: INK, gap: 5 });
  };
  /** A line to write on, with a small label under it. */
  const blank = (label: string, width = 300, x = MARGIN) => {
    room(38);
    y -= 24;
    page.drawLine({ start: { x, y }, end: { x: x + width, y }, thickness: 0.8, color: BODY });
    write(label, { size: 9, color: SOFT, gap: 0, x });
  };
  /** Two lines to write on, side by side. */
  const blankPair = (left: string, right: string) => {
    room(38);
    const top = y;
    blank(left, 226);
    y = top;
    blank(right, 226, MARGIN + 258);
  };
  /** A label and its value on one line. An empty value becomes a line to write on. */
  const row = (label: string, value: string) => {
    const size = 11.5;
    const at = MARGIN + 150;
    room(size * LINE + 6);
    const top = y;
    write(label, { size, color: SOFT, gap: 0, width: 140 });
    const after = y;
    y = top;
    if (clean(value)) {
      write(value, { size, font: bold, gap: 0, x: at });
    } else {
      page.drawLine({ start: { x: at, y: top - size * LINE }, end: { x: at + 200, y: top - size * LINE }, thickness: 0.8, color: BODY });
    }
    y = Math.min(y, after) - 5;
  };
  /** A small label with its value under it. An empty value becomes a line to write on. */
  const fact = (label: string, value: string) => {
    if (!clean(value)) {
      blank(label);
      y -= 6;
      return;
    }
    room(40);
    write(label, { size: 9.5, color: SOFT, gap: 0 });
    write(value, { size: 12.5, font: bold, gap: 9 });
  };
  const checkbox = (text: string) => {
    room(30);
    const size = 12;
    page.drawRectangle({ x: MARGIN, y: y - size * LINE - 1, width: 12, height: 12, borderColor: BODY, borderWidth: 1 });
    write(text, { size, x: MARGIN + 24, gap: 12 });
  };

  const hospital = data.hospital_name || bill.hospital.name;
  const pct = Math.round(data.percent_of_fpl);
  const resultTitle = t(`result.title.${data.status}` as MessageKey);
  const signedBlock = () => blankPair(t("pdf.signature"), t("pdf.date"));

  // ---------- Page 1: the request letter ----------
  newPage();
  title(t("pdf.letter.title"));

  write(t("pdf.to"), { size: 9.5, color: SOFT, gap: 0 });
  write(t("pdf.billing_office"), { font: bold, gap: 0 });
  write(bill.fields.hospital_name || bill.hospital.name, { gap: 0 });
  if (bill.fields.hospital_address) write(bill.fields.hospital_address, { gap: 0 });
  y -= 14;

  write(t("pdf.re"), { size: 9.5, color: SOFT, gap: 2 });
  row(t("field.account_number"), bill.fields.account_number);
  row(t("field.service_date"), bill.fields.service_date);
  row(t("field.amount_due"), bill.fields.amount_due);
  y -= 12;

  write(t("pdf.letter.greeting"));
  write(t("pdf.letter.p1", { hospital }));
  write(t(data.status === "likely_free" ? "pdf.letter.p2_free" : "pdf.letter.p2_discount"));
  write(
    t(household === 1 ? "pdf.letter.p3_one" : "pdf.letter.p3_other", {
      n: household,
      income: dollars.format(income),
      pct,
    }),
  );
  write(t("pdf.letter.p4"));
  write(t("pdf.letter.thanks"), { gap: 4 });
  write(t("pdf.letter.closing"), { gap: 0 });
  blankPair(t("pdf.signature"), t("pdf.name"));
  blank(t("pdf.address"), CONTENT_W);
  blank(t("pdf.address_2"), CONTENT_W);
  blankPair(t("pdf.phone"), t("pdf.date"));

  // ---------- Page 2: the income statement ----------
  newPage();
  title(t("pdf.income.title"));
  write(t("pdf.income.intro"), { color: SOFT, gap: 16 });
  fact(t("pdf.income.household"), String(household));
  fact(t("pdf.income.income"), dollars.format(income));
  fact(t("pdf.income.pct"), t("pdf.income.pct_value", { pct }));
  fact(t("pdf.income.result"), resultTitle);

  heading(t("pdf.income.policy_title"));
  const quote = data.evidence.quote?.trim() ?? "";
  write(
    typeof data.evidence.page === "number"
      ? t("result.quote_lead_page", { hospital, page: data.evidence.page })
      : t("result.quote_lead", { hospital }),
    { gap: 8 },
  );
  if (quote) {
    const size = 11.5;
    const pad = 12;
    const lines = wrap(`“${quote}”`, regular, size, CONTENT_W - pad * 2);
    const height = lines.length * size * LINE + pad * 2;
    room(height);
    page.drawRectangle({ x: MARGIN, y: y - height, width: CONTENT_W, height, color: TINT });
    y -= pad - 3;
    for (const line of lines) {
      y -= size * LINE;
      page.drawText(line, { x: MARGIN + pad, y, size, font: regular, color: BODY });
    }
    y -= pad + 10;
    if (t("pdf.income.quote_note")) write(t("pdf.income.quote_note"), { size: 9.5, color: SOFT });
    const unsure =
      data.evidence.verified === false ||
      data.evidence.status !== "stated" ||
      data.evidence.confidence < CONFIRM_THRESHOLD;
    if (unsure) write(t("result.double_check"), { font: bold });
  } else {
    write(t("result.no_quote"));
  }
  const url = safeHttpUrl(data.source_url);
  if (url) {
    write(t("pdf.income.full_policy"), { size: 9.5, color: SOFT, gap: 0 });
    write(url, { size: 10 });
  }
  y -= 8;
  write(t("pdf.income.attest"));
  signedBlock();

  // ---------- Page 3: what to attach ----------
  newPage();
  title(t("pdf.check.title"));
  write(t("pdf.check.intro"), { color: SOFT, gap: 16 });
  checkbox(t("pdf.check.income"));
  checkbox(t("pdf.check.id"));
  checkbox(t("pdf.check.bill"));
  checkbox(t("pdf.check.address"));
  checkbox(t("pdf.check.other"));
  y -= 8;
  heading(t("pdf.check.send_title"));
  write(t("pdf.check.send"));
  heading(t("pdf.check.help_title"));
  write(t("pdf.check.help"));

  // ---------- Footer on every page ----------
  const pages = doc.getPages();
  pages.forEach((p, i) => {
    p.drawLine({ start: { x: MARGIN, y: 58 }, end: { x: PAGE_W - MARGIN, y: 58 }, thickness: 0.6, color: RULE });
    p.drawText(clean(t("result.fine")), { x: MARGIN, y: 44, size: 9, font: bold, color: INK });
    p.drawText(clean(t("pdf.footer_help")), { x: MARGIN, y: 31, size: 8.5, font: regular, color: SOFT });
    const num = clean(t("pdf.page", { n: i + 1, total: pages.length }));
    p.drawText(num, {
      x: PAGE_W - MARGIN - regular.widthOfTextAtSize(num, 8.5),
      y: 31,
      size: 8.5,
      font: regular,
      color: SOFT,
    });
  });

  doc.setTitle(clean(t("pdf.doc_title")));
  doc.setLanguage(lang);
  doc.setCreator("BillBack");
  doc.setProducer("BillBack (pdf-lib)");
  return doc.save();
}

/** Hands the finished PDF to the browser as a download. The bytes never leave the page. */
export function downloadPdf(bytes: Uint8Array, filename: string) {
  const url = URL.createObjectURL(new Blob([bytes as BlobPart], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
