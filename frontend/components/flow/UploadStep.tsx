"use client";

import { useEffect, useRef, useState, type DragEvent } from "react";
import { Button } from "@/components/ui/button";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { useT, type MessageKey } from "@/lib/i18n";
import { StepCard, StepHeading, type Entrance } from "./StepCard";

const MAX_BYTES = 15 * 1024 * 1024;
const TYPE_BY_EXTENSION: Record<string, string> = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  heic: "image/heic",
  heif: "image/heif",
  pdf: "application/pdf",
};
const ALLOWED_TYPES = new Set(Object.values(TYPE_BY_EXTENSION));
const ACCEPT = ".jpg,.jpeg,.png,.heic,.heif,.pdf,image/jpeg,image/png,image/heic,image/heif,application/pdf";
const SAMPLE_URL = "/samples/sample-bill.jpg";

/** Returns a file the backend will accept, or null. Checked here so a bad file never gets uploaded. */
function acceptable(file: File): File | null {
  if (file.size === 0 || file.size > MAX_BYTES) return null;
  if (ALLOWED_TYPES.has(file.type)) return file;
  // Some browsers leave the type empty for HEIC. Go by the extension and label it for the backend.
  const type = TYPE_BY_EXTENSION[file.name.split(".").pop()?.toLowerCase() ?? ""];
  return type ? new File([file], file.name, { type }) : null;
}

interface UploadStepProps {
  entrance: Entrance;
  reduce: boolean;
  onFile: (file: File) => void;
  onManual: () => void;
  /** Start with this message showing (the /states page). */
  initialError?: UploadError | null;
}

type UploadError = "upload.bad_file" | "upload.sample_failed";
const ERROR_TITLES: Record<UploadError, MessageKey> = {
  "upload.bad_file": "upload.bad_file_title",
  "upload.sample_failed": "upload.sample_failed_title",
};

export function UploadStep({ entrance, reduce, onFile, onManual, initialError = null }: UploadStepProps) {
  const t = useT();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState<UploadError | null>(initialError);
  const [loadingSample, setLoadingSample] = useState(false);
  const alive = useRef(true);
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  function take(file: File | undefined) {
    if (!file || loadingSample) return;
    const ok = acceptable(file);
    if (!ok) {
      setError("upload.bad_file");
      return;
    }
    setError(null);
    onFile(ok);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setOver(false);
    take(e.dataTransfer.files[0]);
  }

  async function trySample() {
    setLoadingSample(true);
    setError(null);
    try {
      const res = await fetch(SAMPLE_URL);
      if (!res.ok) throw new Error("sample missing");
      const blob = await res.blob();
      if (!alive.current) return;
      onFile(new File([blob], "sample-bill.jpg", { type: "image/jpeg" }));
    } catch {
      if (!alive.current) return;
      setError("upload.sample_failed");
      setLoadingSample(false);
    }
  }

  return (
    <StepCard step={1} entrance={entrance} reduce={reduce}>
      <StepHeading>{t("upload.title")}</StepHeading>
      <p className="sub">{t("upload.sub")}</p>

      <div
        className={over ? "drop over" : "drop"}
        onDragEnter={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={onDrop}
      >
        <svg
          width="44"
          height="44"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
        </svg>
        <p className="mt-1.5 mb-0 font-medium">{t("upload.drop")}</p>
        <p className="hint mt-0.5 mb-3">{t("upload.formats")}</p>
        <Button variant="ghost" onClick={() => input.current?.click()} disabled={loadingSample}>
          {t("upload.choose")}
        </Button>
        <input
          ref={input}
          type="file"
          accept={ACCEPT}
          hidden
          tabIndex={-1}
          onChange={(e) => {
            take(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>

      {error && (
        <StatusBanner key={error} variant="error" title={t(ERROR_TITLES[error])}>
          <p>{t(error)}</p>
        </StatusBanner>
      )}

      <div className="btn-row">
        <Button variant="coral" onClick={trySample} disabled={loadingSample}>
          {t("upload.sample")}
        </Button>
        <Button variant="ghost" onClick={onManual} disabled={loadingSample}>
          {t("upload.manual")}
        </Button>
      </div>
    </StepCard>
  );
}
