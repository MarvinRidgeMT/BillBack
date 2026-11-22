"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { getPolicyPage, type PolicyPage } from "@/lib/extras";
import { useT } from "@/lib/i18n";
import { EASE_DIVE, EASE_OUT } from "@/lib/motion";

const CORAL = "#ff6b4a";
const ZOOM_DELAY_MS = 600;
const MAX_ZOOM = 4;
const PAD = 0.05; // of the page width, around the boxes when zoomed
const CONTEXT_LINES = 0.07; // extra page height shown above and below the boxes

interface PolicyReceiptProps {
  slug: string;
  page: number;
  quote: string;
  hospital: string;
  reduce: boolean;
}

type Load = { phase: "loading" } | { phase: "ready"; data: PolicyPage } | { phase: "failed" };

/** "See it in the hospital's policy": the real PDF page with the quoted line boxed, then zoomed in. */
export function PolicyReceipt({ slug, page, quote, hospital, reduce }: PolicyReceiptProps) {
  const t = useT();
  const panelId = useId();
  const [load, setLoad] = useState<Load>({ phase: "loading" });
  const [open, setOpen] = useState(false);
  const toggleRef = useRef<HTMLButtonElement>(null);

  // Prefetch as soon as the result shows, so the button opens instantly in the demo.
  useEffect(() => {
    let live = true;
    getPolicyPage(slug, page, quote).then(
      (data) => live && setLoad({ phase: "ready", data }),
      () => live && setLoad({ phase: "failed" }),
    );
    return () => {
      live = false;
    };
  }, [slug, page, quote]);

  // No PDF on file (404) or the server is away: hide the button entirely.
  if (load.phase === "failed") return null;

  function close() {
    setOpen(false);
    toggleRef.current?.focus();
  }

  return (
    <div className="receipt">
      <Button
        ref={toggleRef}
        variant="ghost"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => (open ? close() : setOpen(true))}
      >
        {open ? t("wow.receipt.hide") : t("wow.receipt.show")}
      </Button>
      <div id={panelId} hidden={!open}>
        {open &&
          (load.phase === "ready" ? (
            <ReceiptPanel data={load.data} quote={quote} hospital={hospital} reduce={reduce} onClose={close} />
          ) : (
            <p className="status-line" role="status">
              <span className="pulse-dot" aria-hidden="true" />
              <span>{t("wow.receipt.loading")}</span>
            </p>
          ))}
      </div>
    </div>
  );
}

interface PanelProps {
  data: PolicyPage;
  quote: string;
  hospital: string;
  reduce: boolean;
  onClose: () => void;
}

function ReceiptPanel({ data, quote, hospital, reduce, onClose }: PanelProps) {
  const t = useT();
  const frameRef = useRef<HTMLDivElement>(null);
  const [frameW, setFrameW] = useState(0);
  const [zoomed, setZoomed] = useState(data.found && reduce);

  useLayoutEffect(() => {
    const el = frameRef.current;
    if (!el) return;
    const measure = () => setFrameW(el.clientWidth);
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!data.found || reduce) return;
    const timer = window.setTimeout(() => setZoomed(true), ZOOM_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [data.found, reduce]);

  const W = frameW;
  const H = W * (data.height / data.width);
  let scale = 1;
  let x = 0;
  let y = 0;
  let frameH = H;
  if (zoomed && data.found && W > 0) {
    const u0 = Math.min(...data.boxes.map((b) => b.x0)) / data.width;
    const u1 = Math.max(...data.boxes.map((b) => b.x1)) / data.width;
    const v0 = Math.min(...data.boxes.map((b) => b.y0)) / data.height;
    const v1 = Math.max(...data.boxes.map((b) => b.y1)) / data.height;
    scale = Math.min(MAX_ZOOM, 1 / (u1 - u0 + 2 * PAD));
    const left = Math.max(0, Math.min(u0 - PAD, 1 - 1 / scale));
    const top = Math.max(0, v0 - CONTEXT_LINES);
    const bottom = Math.min(1, v1 + CONTEXT_LINES);
    x = -left * W * scale;
    y = -top * H * scale;
    frameH = (bottom - top) * H * scale;
  }
  const transition = reduce ? { duration: 0 } : { duration: 0.9, ease: EASE_DIVE };

  return (
    <div
      className="receipt-panel"
      onKeyDown={(e) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          onClose();
        }
      }}
    >
      <motion.div
        ref={frameRef}
        className="receipt-frame"
        initial={false}
        animate={{ height: W > 0 ? frameH : "auto" }}
        transition={transition}
      >
        <motion.div
          className="receipt-page"
          style={{ transformOrigin: "0 0" }}
          initial={false}
          animate={{ x, y, scale }}
          transition={transition}
        >
          {/* eslint-disable-next-line @next/next/no-img-element -- a data URL rendered by our backend */}
          <img
            src={data.image}
            width={data.width}
            height={data.height}
            alt={t("wow.receipt.alt", { page: data.page, hospital, quote })}
          />
          {data.found && (
            <svg viewBox={`0 0 ${data.width} ${data.height}`} preserveAspectRatio="none" aria-hidden="true">
              {data.boxes.map((b, i) => (
                <motion.rect
                  key={i}
                  x={b.x0}
                  y={b.y0}
                  width={b.x1 - b.x0}
                  height={b.y1 - b.y0}
                  rx={4}
                  fill="rgba(255,107,74,0.12)"
                  stroke={CORAL}
                  strokeWidth={3}
                  vectorEffect="non-scaling-stroke"
                  initial={reduce ? false : { pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 0.5, ease: EASE_OUT, delay: 0.1 + i * 0.15 }}
                />
              ))}
            </svg>
          )}
        </motion.div>
      </motion.div>
      <div className="receipt-bar">
        <p className="receipt-note" role="status">
          {data.found ? t("wow.receipt.found", { page: data.page }) : t("wow.receipt.not_found", { page: data.page })}
        </p>
        {data.found && (
          <Button variant="ghost" className="min-h-10 px-4 py-2 text-[15px]" onClick={() => setZoomed((z) => !z)}>
            {zoomed ? t("wow.receipt.full_page") : t("wow.receipt.zoom_in")}
          </Button>
        )}
      </div>
    </div>
  );
}
