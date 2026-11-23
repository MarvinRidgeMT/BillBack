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
import vi from "@/messages/vi.json";
import zhCN from "@/messages/zh-CN.json";
import tl from "@/messages/tl.json";

export type Lang = "en" | "es" | "vi" | "zh-CN" | "tl";
export type MessageKey = keyof typeof en;
export type Translate = (key: MessageKey, vars?: Record<string, string | number>) => string;

// EN/ES remain complete and human-reviewed. New locales are intentionally partial machine translations;
// untranslated keys fall back to English and the UI always discloses that limitation.
const MESSAGES: Record<Lang, Partial<Record<MessageKey, string>>> = { en, es, vi, "zh-CN": zhCN, tl };
const MACHINE_TRANSLATED = new Set<Lang>(["vi", "zh-CN", "tl"]);

export const LANGUAGE_OPTIONS: readonly { code: Lang; label: string }[] = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "vi", label: "Tiếng Việt" },
  { code: "zh-CN", label: "简体中文" },
  { code: "tl", label: "Tagalog" },
];

interface I18nValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  machineTranslated: boolean;
  t: Translate;
}

const I18nContext = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  // Not persisted: nothing about the patient is stored, including language.
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    document.documentElement.lang = lang;
    document.title = MESSAGES[lang]["meta.title"] ?? en["meta.title"];
  }, [lang]);

  const t = useCallback<Translate>(
    (key, vars) => {
      const template = MESSAGES[lang][key] ?? en[key] ?? key;
      if (!vars) return template;
      return template.replace(/\{(\w+)\}/g, (match, name: string) =>
        name in vars ? String(vars[name]) : match,
      );
    },
    [lang],
  );

  const value = useMemo(
    () => ({ lang, setLang, machineTranslated: MACHINE_TRANSLATED.has(lang), t }),
    [lang, t],
  );

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
