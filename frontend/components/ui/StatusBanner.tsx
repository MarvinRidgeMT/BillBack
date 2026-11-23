"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { CircleAlert, CircleCheck, Info, TriangleAlert, type LucideIcon } from "lucide-react";

export type StatusVariant = "info" | "warning" | "error" | "success";

const ICONS: Record<StatusVariant, LucideIcon> = {
  info: Info,
  warning: TriangleAlert,
  error: CircleAlert,
  success: CircleCheck,
};

interface StatusBannerProps {
  variant: StatusVariant;
  /** Short heading. Optional for compact inline field messages. */
  title?: ReactNode;
  /** The explanation. Plain text or a few inline elements. */
  children?: ReactNode;
  /** Buttons for the way forward, shown in a row under the text. */
  actions?: ReactNode;
  id?: string;
  /** "compact" = one-line inline message under a form field. */
  size?: "default" | "compact";
  /** Move keyboard focus here when it appears (for errors that replace what the patient was doing). */
  focusOnMount?: boolean;
  className?: string;
  /** Language of the text when it differs from the page (e.g. an English-only backend message). */
  lang?: string;
}

/**
 * Every message in the app: one layout (icon, heading, text, actions), four tones from CSS tokens.
 * Errors and warnings are role="alert" (announced right away); info and success are a polite status.
 */
export function StatusBanner({
  variant,
  title,
  children,
  actions,
  id,
  size = "default",
  focusOnMount = false,
  className,
  lang,
}: StatusBannerProps) {
  const ref = useRef<HTMLDivElement>(null);
  const Icon = ICONS[variant];
  const urgent = variant === "error" || variant === "warning";

  useEffect(() => {
    if (focusOnMount) ref.current?.focus({ preventScroll: true });
  }, [focusOnMount]);

  return (
    <div
      ref={ref}
      id={id}
      className={className ? `status ${className}` : "status"}
      data-variant={variant}
      data-size={size}
      role={urgent ? "alert" : "status"}
      aria-live={urgent ? undefined : "polite"}
      tabIndex={focusOnMount ? -1 : undefined}
      lang={lang}
    >
      <Icon className="status-icon" size={size === "compact" ? 18 : 22} aria-hidden="true" strokeWidth={2.2} />
      {title && <p className="status-title">{title}</p>}
      {children && <div className="status-body">{children}</div>}
      {actions && <div className="status-actions">{actions}</div>}
    </div>
  );
}
