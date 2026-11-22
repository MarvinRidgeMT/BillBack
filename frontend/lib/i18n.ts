"use client";

import {
  createContext,
  createElement,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import en from "@/messages/en.json";
import es from "@/messages/es.json";

export type Lang = "en" | "es";
export type MessageKey = keyof typeof en;
export type Translate = (key: MessageKey, vars?: Record<string, string | number>) => string;

// Typing es against en's keys makes a missing Spanish key a build error.
const MESSAGES: Record<Lang, Record<MessageKey, string>> = { en, es };

interface I18nValue {
  lang: Lang;
  toggleLang: () => void;
  t: Translate;
}

/** The English text for a key, for comparing against English text from the backend. */
export function enMessage(key: MessageKey): string {
  return en[key];
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  // Not persisted: nothing about the patient is stored, including language.
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = MESSAGES[lang]["meta.title"];
  }, [lang]);

  const t = useCallback<Translate>(
    (key, vars) => {
      const template = MESSAGES[lang][key] ?? MESSAGES.en[key] ?? key;
      if (!vars) return template;
      return template.replace(/\{(\w+)\}/g, (match, name: string) =>
        name in vars ? String(vars[name]) : match,
      );
    },
    [lang],
  );

  const toggleLang = useCallback(() => setLang((l) => (l === "en" ? "es" : "en")), []);
  const value = useMemo(() => ({ lang, toggleLang, t }), [lang, toggleLang, t]);

  return createElement(I18nContext.Provider, { value }, children);
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside <I18nProvider>");
  return ctx;
}

export function useT(): Translate {
  return useI18n().t;
}
