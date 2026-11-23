"use client";

import { BookOpen } from "lucide-react";
import { useAccessibility } from "@/lib/accessibility";
import { useT } from "@/lib/i18n";

export function AccessibilityToolbar() {
  const t = useT();
  const { easyRead, setEasyRead } = useAccessibility();
  return (
    <button
      type="button"
      className="nav-link easy-read-toggle"
      aria-pressed={easyRead}
      onClick={() => setEasyRead(!easyRead)}
    >
      <BookOpen size={18} aria-hidden="true" />
      {easyRead ? t("access.easy_on") : t("access.easy_off")}
    </button>
  );
}
