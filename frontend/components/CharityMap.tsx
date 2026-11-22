"use client";

import { useEffect, useId, useState } from "react";
import { useI18n, type MessageKey } from "@/lib/i18n";

// Standard US tile-grid layout: [state, column, row]. Pure CSS grid, no map library.
const TILES: ReadonlyArray<readonly [string, number, number]> = [
  ["AK", 0, 0], ["ME", 11, 0],
  ["WI", 6, 1], ["VT", 10, 1], ["NH", 11, 1],
  ["WA", 1, 2], ["ID", 2, 2], ["MT", 3, 2], ["ND", 4, 2], ["MN", 5, 2], ["IL", 6, 2], ["MI", 7, 2], ["NY", 9, 2], ["MA", 10, 2],
  ["OR", 1, 3], ["NV", 2, 3], ["WY", 3, 3], ["SD", 4, 3], ["IA", 5, 3], ["IN", 6, 3], ["OH", 7, 3], ["PA", 8, 3], ["NJ", 9, 3], ["CT", 10, 3], ["RI", 11, 3],
  ["CA", 1, 4], ["UT", 2, 4], ["CO", 3, 4], ["NE", 4, 4], ["MO", 5, 4], ["KY", 6, 4], ["WV", 7, 4], ["VA", 8, 4], ["MD", 9, 4], ["DE", 10, 4],
  ["AZ", 2, 5], ["NM", 3, 5], ["KS", 4, 5], ["AR", 5, 5], ["TN", 6, 5], ["NC", 7, 5], ["SC", 8, 5], ["DC", 9, 5],
  ["OK", 4, 6], ["LA", 5, 6], ["MS", 6, 6], ["AL", 7, 6], ["GA", 8, 6],
  ["HI", 0, 7], ["TX", 4, 7], ["FL", 9, 7],
];

type Band = "200" | "250" | "300" | "400" | "none";
const BANDS: { band: Band; key: MessageKey }[] = [
  { band: "200", key: "map.band_200" },
  { band: "250", key: "map.band_250" },
  { band: "300", key: "map.band_300" },
  { band: "400", key: "map.band_400" },
  { band: "none", key: "map.band_none" },
];

interface MapHospital {
  slug: string;
  name: string;
  state: string;
  free: number | null;
  discount: number | null;
  url: string | null;
}

function band(free: number | null): Band {
  if (free === null) return "none";
  if (free <= 200) return "200";
  if (free <= 250) return "250";
  if (free <= 300) return "300";
  return "400";
}

function safeUrl(url: unknown): string | null {
  if (typeof url !== "string") return null;
  try {
    const u = new URL(url);
    return u.protocol === "https:" || u.protocol === "http:" ? u.href : null;
  } catch {
    return null;
  }
}

const num = (v: unknown) => (typeof v === "number" && Number.isFinite(v) ? v : null);

function useMapHospitals(): MapHospital[] {
  const [rows, setRows] = useState<MapHospital[]>([]);
  useEffect(() => {
    let live = true;
    fetch("/api/hospitals", { signal: AbortSignal.timeout(8000) })
      .then((r) => r.json())
      .then((body: { data?: unknown }) => {
        if (!live || !Array.isArray(body?.data)) return;
        setRows(
          body.data
            .filter((h) => h && typeof h.slug === "string" && typeof h.name === "string" && typeof h.state === "string")
            .map((h) => ({
              slug: h.slug,
              name: h.name,
              state: h.state,
              free: num(h.free_max_percent),
              discount: num(h.discount_max_percent),
              url: safeUrl(h.source_url),
            })),
        );
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, []);
  return rows;
}

/** "Same bill, very different rules": a tile map of the hospitals whose policies we've read. */
export function CharityMap() {
  const { t } = useI18n();
  const id = useId();
  const hospitals = useMapHospitals();
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (hospitals.length === 0) return null;
  const limits = hospitals.map((h) => h.free).filter((v): v is number => v !== null);
  const byState = new Map<string, MapHospital[]>();
  for (const h of hospitals) byState.set(h.state, [...(byState.get(h.state) ?? []), h]);
  const pct = (v: number | null) => (v === null ? t("map.not_stated") : `${Math.round(v)}%`);

  return (
    <section className="how charity-map" aria-labelledby={`${id}-title`}>
      <h2 id={`${id}-title`}>{t("map.title")}</h2>
      <p className="map-lead">
        {t("map.lead", { n: hospitals.length, min: Math.min(...limits), max: Math.max(...limits) })}
      </p>

      <div className="tile-map">
        {TILES.map(([state, col, row]) => {
          const here = byState.get(state) ?? [];
          return (
            <div
              key={state}
              className={`tile${here.length ? " has" : ""}`}
              data-edge={col <= 2 ? "left" : col >= 9 ? "right" : undefined}
              style={{ gridColumn: col + 1, gridRow: row + 1 }}
            >
              <span className="tile-code" aria-hidden="true">
                {state}
              </span>
              {here.length > 0 && (
                <span className="tile-dots">
                  {here.map((h) => {
                    const isOpen = open === h.slug;
                    return (
                      <span
                        key={h.slug}
                        className="dot-wrap"
                        onMouseLeave={() => setOpen((o) => (o === h.slug ? null : o))}
                        onBlur={(e) => {
                          if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
                            setOpen((o) => (o === h.slug ? null : o));
                          }
                        }}
                      >
                        <button
                          type="button"
                          className={`map-dot band-${band(h.free)}`}
                          aria-expanded={isOpen}
                          aria-controls={`${id}-${h.slug}`}
                          aria-label={t("map.dot_label", { name: h.name, state, free: pct(h.free) })}
                          onClick={() => setOpen(h.slug)}
                          onMouseEnter={() => setOpen(h.slug)}
                          onFocus={() => setOpen(h.slug)}
                        />
                        {isOpen && (
                          <span className="map-tip" id={`${id}-${h.slug}`} role="tooltip">
                            <b>{h.name}</b>
                            <span>{t("map.tip_free", { pct: pct(h.free) })}</span>
                            <span>{t("map.tip_discount", { pct: pct(h.discount) })}</span>
                            {h.url && (
                              <a className="text-link" href={h.url} target="_blank" rel="noopener noreferrer">
                                {t("result.read_policy")}
                                <span className="sr-only"> {t("result.new_tab")}</span>
                              </a>
                            )}
                          </span>
                        )}
                      </span>
                    );
                  })}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <ul className="map-legend">
        {BANDS.map(({ band: b, key }) => (
          <li key={b}>
            <span className={`map-dot static band-${b}`} aria-hidden="true" /> {t(key)}
          </li>
        ))}
      </ul>

      <table className="sr-only">
        <caption>{t("map.table_caption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("map.col_hospital")}</th>
            <th scope="col">{t("map.col_state")}</th>
            <th scope="col">{t("map.col_free")}</th>
            <th scope="col">{t("map.col_discount")}</th>
          </tr>
        </thead>
        <tbody>
          {hospitals.map((h) => (
            <tr key={h.slug}>
              <th scope="row">{h.name}</th>
              <td>{h.state}</td>
              <td>{pct(h.free)}</td>
              <td>{pct(h.discount)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
