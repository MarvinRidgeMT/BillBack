"use client";

import { useRef, useState, type DragEvent } from "react";
import { Button } from "@/components/ui/button";
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
const SAMPLE_URL = "/samples/sample-bill.png";

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
}

export function UploadStep({ entrance, reduce, onFile, onManual }: UploadStepProps) {
  const t = useT();
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState<MessageKey | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  function take(file: File | undefined) {
    if (!file) return;
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
      onFile(new File([blob], "sample-bill.png", { type: "image/png" }));
    } catch {
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
        <Button variant="ghost" onClick={() => input.current?.click()}>
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
        <p className="error-text" role="alert">
          {t(error)}
        </p>
      )}

      <div className="btn-row">
        <Button variant="coral" onClick={trySample} disabled={loadingSample}>
          {t("upload.sample")}
        </Button>
        <Button variant="ghost" onClick={onManual}>
          {t("upload.manual")}
        </Button>
      </div>
    </StepCard>
  );
}
