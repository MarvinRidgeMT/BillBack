"use client";

import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { Search } from "lucide-react";
import { StatusBanner } from "@/components/ui/StatusBanner";
import { searchHospitals } from "@/lib/api";
import { NOT_LISTED, useHospitals } from "@/lib/hospitals";
import { useT } from "@/lib/i18n";
import { filterHospitals } from "@/lib/search";
import type { Hospital } from "@/lib/types";

/** The patient's choice: a hospital, "my hospital isn't listed", or nothing yet. */
export type HospitalPick = Hospital | typeof NOT_LISTED | null;

const DEBOUNCE_MS = 200;
const MIN_REMOTE_CHARS = 2;

interface HospitalSearchProps {
  value: HospitalPick;
  onChange: (pick: HospitalPick) => void;
  /** True when the current value is our guess from the bill, so we say so. */
  matched: boolean;
  /** True when we tried to match the bill's hospital and found nothing close enough. */
  matchFailed?: boolean;
  /** True when the patient tried to continue without choosing. */
  showRequired: boolean;
}

type Remote = { q: string; hits: Hospital[] } | null;

const label = (h: Hospital) => (h.state ? `${h.name} (${h.state})` : h.name);

/**
 * "Which hospital is this?" An ARIA 1.2 combobox: type to search (debounced, backend fuzzy search,
 * the loaded list as a fallback), arrows to move, Enter to pick, Escape to close.
 * "My hospital isn't listed" is always the last option.
 */
export function HospitalSearch({ value, onChange, matched, matchFailed = false, showRequired }: HospitalSearchProps) {
  const t = useT();
  const id = useId();
  const listId = `${id}-list`;
  const hintId = `${id}-hint`;
  const all = useHospitals();
  const [changing, setChanging] = useState(false);
  const [query, setQuery] = useState<string | null>(null); // null = show the chosen value
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [remote, setRemote] = useState<Remote>(null);

  const chosen = value && value !== NOT_LISTED ? value : null;
  const shown = query ?? (chosen ? label(chosen) : value === NOT_LISTED ? t("hospital.not_listed") : "");
  const q = (query ?? "").trim();
  const wantsRemote = q.length >= MIN_REMOTE_CHARS;

  // Ask the backend after a short pause. Until it answers (or if it can't), filter the list we already have.
  useEffect(() => {
    if (!wantsRemote) return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      searchHospitals(q, controller.signal).then(
        (hits) => setRemote({ q, hits }),
        () => {
          if (!controller.signal.aborted) setRemote({ q, hits: filterHospitals(all, q) });
        },
      );
    }, DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [q, wantsRemote, all]);

  const settled = !wantsRemote || remote?.q === q;
  const results = wantsRemote && remote?.q === q ? remote.hits : filterHospitals(all, q);
  const options: HospitalPick[] = [...results, NOT_LISTED];
  const activeIndex = active >= options.length ? options.length - 1 : active;
  const optionId = (i: number) => `${id}-opt-${i}`;

  if (matched && chosen && !changing) {
    return (
      <div className="form-field">
        <p className="match-line" aria-live="polite">
          {t("hospital.we_think")} <strong>{chosen.name}</strong>
          {chosen.state ? ` (${chosen.state})` : ""}
          {" — "}
          <button type="button" className="text-link inline-btn" onClick={() => setChanging(true)}>
            {t("hospital.change")}
          </button>
        </p>
      </div>
    );
  }

  function pick(next: HospitalPick) {
    onChange(next);
    setQuery(null);
    setOpen(false);
    setActive(-1);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (!open) {
          setOpen(true);
          setActive(0);
        } else {
          setActive((i) => Math.min(i + 1, options.length - 1));
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (!open) {
          setOpen(true);
          setActive(options.length - 1);
        } else {
          setActive((i) => Math.max(i - 1, 0));
        }
        break;
      case "Enter":
        if (open && activeIndex >= 0) {
          e.preventDefault();
          pick(options[activeIndex]);
        }
        break;
      case "Escape":
        if (open) {
          e.preventDefault();
          setOpen(false);
          setActive(-1);
        } else if (shown) {
          e.preventDefault();
          setQuery("");
          if (value !== null) onChange(null);
        }
        break;
    }
  }

  const invalid = showRequired && value === null;
  const count = results.length;
  const announce = !open
    ? ""
    : !settled
      ? t("hospital.searching")
      : count === 0
        ? t("hospital.no_results")
        : count === 1
          ? t("hospital.results_one")
          : t("hospital.results_many", { n: count });

  return (
    <div className="form-field">
      <label htmlFor={`${id}-input`}>{t("hospital.label")}</label>
      <div className="combo-input">
        <Search size={18} aria-hidden="true" />
        <input
          id={`${id}-input`}
          type="text"
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={open && activeIndex >= 0 ? optionId(activeIndex) : undefined}
          aria-describedby={hintId}
          aria-invalid={invalid || undefined}
          autoComplete="off"
          spellCheck={false}
          placeholder={t("hospital.search_placeholder")}
          value={shown}
          autoFocus={changing}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            setActive(-1);
            if (value !== null) onChange(null);
          }}
          onFocus={() => setOpen(true)}
          onClick={() => setOpen(true)}
          onBlur={() => {
            setOpen(false);
            setActive(-1);
          }}
          onKeyDown={onKeyDown}
        />
      </div>

      {open && (
        <ul className="combo-list" id={listId} role="listbox" aria-label={t("hospital.label")}>
          {options.map((opt, i) => {
            const isNotListed = opt === NOT_LISTED;
            const h = isNotListed ? null : (opt as Hospital);
            const selected = isNotListed ? value === NOT_LISTED : chosen?.slug === h?.slug;
            return (
              <li
                key={h ? h.slug : NOT_LISTED}
                id={optionId(i)}
                role="option"
                aria-selected={i === activeIndex}
                data-chosen={selected || undefined}
                className={isNotListed ? "not-listed" : undefined}
                // Keep focus in the input, so the list doesn't close before the click lands.
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pick(opt)}
              >
                {h ? (
                  <>
                    <span>{h.name}</span>
                    {h.state && <small>{h.state}</small>}
                  </>
                ) : (
                  <span>{t("hospital.not_listed")}</span>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <p className="sr-only" aria-live="polite">
        {announce}
      </p>

      <div id={hintId}>
        {invalid ? (
          <StatusBanner variant="error" size="compact">
            {t("hospital.required")}
          </StatusBanner>
        ) : value === NOT_LISTED ? (
          <StatusBanner variant="info" size="compact">
            {t("hospital.not_listed_hint")}
          </StatusBanner>
        ) : value === null && matchFailed ? (
          <p className="hint">{t("hospital.no_match")}</p>
        ) : value === null ? (
          <p className="hint">{t("hospital.pick_hint")}</p>
        ) : null}
      </div>
    </div>
  );
}
