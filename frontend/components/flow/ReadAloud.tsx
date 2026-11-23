"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Pause, Play, Square, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useI18n, type Lang } from "@/lib/i18n";

const PREFERRED: Record<Lang, string[]> = {
  en: ["en-US", "en-GB", "en"],
  es: ["es-US", "es-MX", "es-419", "es"],
  vi: ["vi-VN", "vi"],
  "zh-CN": ["zh-CN", "zh"],
  tl: ["fil-PH", "tl-PH", "fil", "tl"],
};

function pickVoice(voices: SpeechSynthesisVoice[], lang: Lang): SpeechSynthesisVoice | null {
  for (const want of PREFERRED[lang]) {
    const exact = voices.filter((v) => v.lang.toLowerCase().replace("_", "-").startsWith(want.toLowerCase()));
    if (exact.length) return exact.find((v) => v.localService) ?? exact[0];
  }
  return null;
}

function useVoice(lang: Lang): { supported: boolean; voice: SpeechSynthesisVoice | null } {
  const [state, setState] = useState<{ supported: boolean; voice: SpeechSynthesisVoice | null }>({
    supported: false,
    voice: null,
  });
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const update = () => setState({ supported: true, voice: pickVoice(window.speechSynthesis.getVoices(), lang) });
    update();
    window.speechSynthesis.addEventListener("voiceschanged", update);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", update);
  }, [lang]);
  return state;
}

interface ReadAloudProps {
  /** Part 1: status, plain reason and the policy line, already in the page language. */
  summary: string[];
  /** Part 2: what to say when calling the billing office. */
  script: string[];
  /** Hide the call-script disclosure when this is reading an on-screen form. */
  scriptTitle?: string;
}

type Playback = "idle" | "playing" | "paused";

/**
 * "Read it to me". Uses the voice already on the device (speechSynthesis), so nothing is downloaded or sent.
 * Never autoplays. Everything being read is visible on screen.
 */
export function ReadAloud({ summary, script, scriptTitle }: ReadAloudProps) {
  const { t, lang } = useI18n();
  const id = useId();
  const { supported, voice } = useVoice(lang);
  const [playback, setPlayback] = useState<Playback>("idle");
  const [current, setCurrent] = useState(-1);
  const runId = useRef(0);
  const lines = [...summary, ...script];

  // Stop when leaving the screen or switching language.
  useEffect(() => {
    return () => {
      runId.current += 1;
      if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    };
  }, [lang]);

  function stop() {
    runId.current += 1;
    window.speechSynthesis.cancel();
    setPlayback("idle");
    setCurrent(-1);
  }

  function play() {
    if (playback === "paused") {
      window.speechSynthesis.resume();
      setPlayback("playing");
      return;
    }
    const run = ++runId.current;
    window.speechSynthesis.cancel();
    setPlayback("playing");
    lines.forEach((text, i) => {
      const u = new SpeechSynthesisUtterance(text);
      if (voice) {
        u.voice = voice;
        u.lang = voice.lang;
      } else {
        u.lang = lang === "es" ? "es-US" : lang === "vi" ? "vi-VN" : lang === "zh-CN" ? "zh-CN" : lang === "tl" ? "fil-PH" : "en-US";
      }
      u.rate = 0.95;
      u.onstart = () => run === runId.current && setCurrent(i);
      u.onend = () => {
        if (run === runId.current && i === lines.length - 1) {
          setPlayback("idle");
          setCurrent(-1);
        }
      };
      u.onerror = () => run === runId.current && i === lines.length - 1 && setPlayback("idle");
      window.speechSynthesis.speak(u);
    });
  }

  function pause() {
    window.speechSynthesis.pause();
    setPlayback("paused");
  }

  // Spanish with no Spanish voice on this device: show the script only, no button.
  const canSpeak = supported && (voice !== null || lang === "en");

  return (
    <section className="readaloud" aria-labelledby={`${id}-title`}>
      <h3 className="sr-only" id={`${id}-title`}>
        {t("wow.read.title")}
      </h3>
      {canSpeak && (
        <div className="btn-row readaloud-controls">
          <Button
            variant="ghost"
            aria-pressed={playback === "playing"}
            onClick={playback === "playing" ? pause : play}
          >
            {playback === "playing" ? <Pause aria-hidden="true" /> : playback === "paused" ? <Play aria-hidden="true" /> : <Volume2 aria-hidden="true" />}
            {playback === "playing" ? t("wow.read.pause") : playback === "paused" ? t("wow.read.resume") : t("wow.read.button")}
          </Button>
          {playback !== "idle" && (
            <Button variant="ghost" onClick={stop}>
              <Square aria-hidden="true" />
              {t("wow.read.stop")}
            </Button>
          )}
        </div>
      )}
      {playback !== "idle" && (
        <ol className="readaloud-summary" aria-label={t("wow.read.now_reading")}>
          {summary.map((text, i) => (
            <li key={i} data-current={current === i || undefined}>
              {text}
            </li>
          ))}
        </ol>
      )}
      {script.length > 0 && (
        <details className="call-script" open={playback !== "idle" && current >= summary.length ? true : undefined}>
          <summary>{scriptTitle ?? t("wow.read.script_title")}</summary>
          {script.map((text, i) => (
            <p key={i} data-current={current === summary.length + i || undefined}>
              {text}
            </p>
          ))}
        </details>
      )}
    </section>
  );
}
