"use client";

import { useState, type ReactNode } from "react";
import { DevPanel } from "@/components/DevPanel";
import { LiveErrorBanner, LivePolicyStep } from "@/components/flow/LivePolicyStep";
import { NotListed, type PolicyInput } from "@/components/flow/NotListed";
import { QuestionsStep } from "@/components/flow/QuestionsStep";
import { BlurryBanner } from "@/components/flow/ReadingBanners";
import { ReadingStep } from "@/components/flow/ReadingStep";
import { PacketStatus, ResultStep } from "@/components/flow/ResultStep";
import { UploadStep } from "@/components/flow/UploadStep";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { I18nProvider, useT, type Lang, type MessageKey } from "@/lib/i18n";
import { MOCK_BILL_READ } from "@/lib/mock";
import type { BillReadData, ConfirmedBill, EligibilityData, PolicyReadData } from "@/lib/types";
import type { TimingSnapshot } from "@/lib/timings";

// Everything on this page is sample data. Nothing here calls the backend: every promise is made up front.

function quiet<T>(p: Promise<T>): Promise<T> {
  p.catch(() => {});
  return p;
}
const noop = () => {};

const UNREADABLE: BillReadData = {
  ...MOCK_BILL_READ,
  fields: {
    ...MOCK_BILL_READ.fields,
    amount_due: { value: "$4,8?2.00", confidence: 0.41, note: "", normalized: null },
    account_number: { value: null, confidence: 0.2, note: "", normalized: null },
  },
  quality: { ok: false, checked: true, reasons: ["blurry", "dark"] },
  unreadable: true,
  weak_fields: ["amount_due", "account_number"],
};
const UNREADABLE_READ = Promise.resolve(UNREADABLE);
const AI_DOWN_READ = quiet<BillReadData>(Promise.reject(new ApiError("unavailable", 503, "", "ai_unavailable")));

const SAMPLE_POLICY: PolicyReadData = {
  slug: "live-0000demo",
  source: "live",
  hospital_name: "Sample General Hospital (fictional)",
  state: "AL",
  seconds: 23.4,
  beta: true,
  needs_checking: ["discount", "application_window"],
  grounded: {
    free_care: {
      value: 200,
      source_quote: "Patients with household income at or below 200% of the Federal Poverty Guidelines receive a 100% discount.",
      page: 3,
      confidence: 0.95,
      status: "stated",
      verified: true,
      needs_checking: false,
      problems: [],
    },
    discount: {
      value: { fpl_max_percent: 400, tiers: [] },
      source_quote: "A partial discount is available up to 400% of the Federal Poverty Guidelines.",
      page: 4,
      confidence: 0.62,
      status: "stated",
      verified: false,
      needs_checking: true,
      problems: ["quote_not_found", "low_confidence"],
    },
    asset_test: {
      value: { applies: false, details: null },
      source_quote: "",
      page: null,
      confidence: 0.9,
      status: "not_stated",
      verified: null,
      needs_checking: false,
      problems: [],
    },
    residency: {
      value: { required: true, area: "the hospital's primary service area" },
      source_quote: "Applicants must reside within the hospital's primary service area.",
      page: 2,
      confidence: 0.88,
      status: "stated",
      verified: true,
      needs_checking: false,
      problems: [],
    },
    application_window: {
      value: { days: null, counted_from: null },
      source_quote: "",
      page: null,
      confidence: 0,
      status: "not_stated",
      verified: null,
      needs_checking: true,
      problems: ["not_stated"],
    },
  },
};
const POLICY_READ = Promise.resolve(SAMPLE_POLICY);

const LIVE_ERRORS: { code: string; kind: PolicyInput["kind"] }[] = [
  { code: "live_off", kind: "url" },
  { code: "bad_url", kind: "url" },
  { code: "fetch_failed", kind: "url" },
  { code: "fetch_timeout", kind: "url" },
  { code: "not_pdf", kind: "url" },
  { code: "no_pdf_link", kind: "url" },
  { code: "pdf_encrypted", kind: "file" },
  { code: "pdf_empty", kind: "file" },
  { code: "too_short", kind: "file" },
  { code: "not_policy", kind: "file" },
  { code: "bad_file", kind: "file" },
  { code: "too_large", kind: "file" },
  { code: "ai_unavailable", kind: "file" },
  { code: "ai_invalid", kind: "url" },
  { code: "demo_only", kind: "url" },
  { code: "invalid_input", kind: "manual" },
  { code: "not_found", kind: "url" },
  { code: "server_error", kind: "url" },
];
const statusFor = (code: string) => (code === "ai_unavailable" ? 503 : code === "server_error" ? 500 : 422);

const BILL: ConfirmedBill = {
  fields: {
    hospital_name: "Sample General Hospital (fictional)",
    hospital_address: "100 Example Street, Sampletown, AL 00000",
    amount_due: "$4,812.00",
    service_date: "Aug 14, 2026",
    account_number: "FAKE-88-20417",
  },
  hospital: { slug: "live-0000demo", name: "Sample General Hospital (fictional)", state: "AL" },
};
const RULES_DOWN = quiet<EligibilityData>(Promise.reject(new ApiError("rejected", 404, "", "not_found")));

const DEV_SAMPLE: TimingSnapshot = {
  entries: [
    { key: "bill_read_s", seconds: 6.42 },
    { key: "bill_read_s", seconds: 5.87 },
    { key: "policy_read_s", seconds: 23.4 },
    { key: "rules_s", seconds: 0.004 },
    { key: "packet_s", seconds: 0.21 },
  ],
  bills: 2,
  lowConfidence: 3,
  fields: 10,
};

function Section({ title, children }: { title: MessageKey; children: ReactNode }) {
  const t = useT();
  return (
    <section className="states-section">
      <h2>{t(title)}</h2>
      {children}
    </section>
  );
}

/** A plain card for pieces shown outside their step (no step bar, no focus moves). */
function Card({ children }: { children: ReactNode }) {
  return <div className="panel states-card">{children}</div>;
}

function Column() {
  const t = useT();
  return (
    <div className="states-col">
      <Section title="states.banners">
        <Card>
          <StatusBanner variant="info" title={t("reading.sample_title")}>
            <p>{t("reading.sample_banner")}</p>
          </StatusBanner>
          <BlurryBanner reasons={["blurry"]} />
          <StatusBanner variant="error" title={t("reading.error_title")} actions={<Button>{t("error.try_again")}</Button>}>
            <p>{t("err.ai_unavailable")}</p>
          </StatusBanner>
          <StatusBanner variant="success" title={t("result.app_ready_title")}>
            <p>{t("result.app_ready")}</p>
          </StatusBanner>
          <StatusBanner variant="error" size="compact">
            {t("hospital.required")}
          </StatusBanner>
          <StatusBanner variant="info" size="compact">
            {t("hospital.not_listed_hint")}
          </StatusBanner>
        </Card>
      </Section>

      <Section title="states.upload_bad">
        <UploadStep entrance="step" reduce onFile={noop} onManual={noop} initialError="upload.bad_file" />
      </Section>

      <Section title="states.unreadable">
        <ReadingStep
          entrance="step"
          reduce
          reading={UNREADABLE_READ}
          sample={false}
          onConfirm={noop}
          onNotListed={noop}
          onRetry={noop}
          onRetake={noop}
          onManual={noop}
          onSample={noop}
        />
      </Section>

      <Section title="states.blurry">
        <Card>
          <BlurryBanner reasons={["blurry", "dark"]} />
        </Card>
      </Section>

      <Section title="states.ai_unavailable">
        <ReadingStep
          entrance="step"
          reduce
          reading={AI_DOWN_READ}
          sample={false}
          onConfirm={noop}
          onNotListed={noop}
          onRetry={noop}
          onRetake={noop}
          onManual={noop}
          onSample={noop}
        />
      </Section>

      <Section title="states.not_listed">
        <NotListed
          entrance="step"
          reduce
          liveMode
          draft={{ url: "", hospital: "Sample General Hospital", state: "AL", free: "", discount: "" }}
          onRead={noop}
          onBack={noop}
        />
      </Section>

      <Section title="states.limits_errors">
        <NotListed
          entrance="step"
          reduce
          liveMode={false}
          draft={{ url: "", hospital: "", state: "A", free: "700", discount: "" }}
          revealErrors
          onRead={noop}
          onBack={noop}
        />
      </Section>

      <Section title="states.live_found">
        <LivePolicyStep
          entrance="step"
          reduce
          reading={POLICY_READ}
          kind="url"
          fallbackName="Sample General Hospital"
          fallbackState="AL"
          onContinue={noop}
          onAction={noop}
          onBack={noop}
        />
      </Section>

      <Section title="states.live_errors">
        <Card>
          {LIVE_ERRORS.map(({ code, kind }) => (
            <div key={code} className="states-code">
              <code>
                {code} · {kind}
              </code>
              <LiveErrorBanner
                error={new ApiError(statusFor(code) === 503 ? "unavailable" : "rejected", statusFor(code), "", code)}
                kind={kind}
                onAction={noop}
              />
            </div>
          ))}
        </Card>
      </Section>

      <Section title="states.household">
        <QuestionsStep
          entrance="step"
          reduce
          initial={{ household: "0", income: "-500", benefits: "skip" }}
          revealErrors
          onSubmit={noop}
          onBack={noop}
        />
        <QuestionsStep
          entrance="step"
          reduce
          initial={{ household: "25", income: "", benefits: "skip" }}
          revealErrors
          onSubmit={noop}
        />
        <QuestionsStep
          entrance="step"
          reduce
          initial={{ household: "", income: "41,000", benefits: "skip" }}
          revealErrors
          onSubmit={noop}
        />
      </Section>

      <Section title="states.unavailable">
        <ResultStep
          entrance="step"
          reduce
          checking={RULES_DOWN}
          bill={BILL}
          household={3}
          income={41000}
          onRetry={noop}
          onEditAnswers={noop}
          onStartOver={noop}
        />
      </Section>

      <Section title="states.packet">
        <Card>
          <PacketStatus state="done" onRetry={noop} />
          <PacketStatus state="failed" onRetry={noop} />
          <p className="result-live-note">{t("result.live_note")}</p>
        </Card>
      </Section>

      <Section title="states.dev">
        <DevPanel force inline snapshot={DEV_SAMPLE} />
      </Section>
    </div>
  );
}

type Show = "both" | Lang;

function Gallery() {
  const t = useT();
  const [show, setShow] = useState<Show>("both");
  const langs: Lang[] = show === "both" ? ["en", "es"] : [show];
  const options: { value: Show; label: string; lang?: Lang }[] = [
    { value: "both", label: t("states.both") },
    { value: "en", label: "English", lang: "en" },
    { value: "es", label: "Español", lang: "es" },
  ];
  return (
    <main className="states-page">
      <header className="states-head">
        <h1>{t("states.title")}</h1>
        <p className="sub">{t("states.sub")}</p>
        <div className="states-toggle" role="group" aria-label={t("states.show")}>
          {options.map((o) => (
            <Button
              key={o.value}
              variant={show === o.value ? "default" : "ghost"}
              aria-pressed={show === o.value}
              lang={o.lang}
              onClick={() => setShow(o.value)}
            >
              {o.label}
            </Button>
          ))}
        </div>
      </header>
      <div className="states-grid" data-cols={langs.length}>
        {langs.map((lang) => (
          <div key={lang} lang={lang}>
            <I18nProvider initialLang={lang} syncDocument={false}>
              <Column />
            </I18nProvider>
          </div>
        ))}
      </div>
    </main>
  );
}

export function StatesGallery() {
  return (
    // syncDocument off: keep the page's own title ("BillBack: every state") from app/states/page.tsx.
    <I18nProvider syncDocument={false}>
      <Gallery />
    </I18nProvider>
  );
}
