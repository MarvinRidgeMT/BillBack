"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

interface AccessibilityValue {
  easyRead: boolean;
  setEasyRead: (value: boolean) => void;
}

const AccessibilityContext = createContext<AccessibilityValue | null>(null);

/** Accessibility preferences live only in React memory and reset when the tab refreshes. */
export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [easyRead, setEasyRead] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("easy-read", easyRead);
    return () => document.documentElement.classList.remove("easy-read");
  }, [easyRead]);

  const value = useMemo(() => ({ easyRead, setEasyRead }), [easyRead]);
  return <AccessibilityContext.Provider value={value}>{children}</AccessibilityContext.Provider>;
}

export function useAccessibility(): AccessibilityValue {
  const value = useContext(AccessibilityContext);
  if (!value) throw new Error("useAccessibility must be used inside AccessibilityProvider");
  return value;
}
