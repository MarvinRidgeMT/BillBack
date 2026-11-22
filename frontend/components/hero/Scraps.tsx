import type { CSSProperties } from "react";

// Six torn scraps of the bill: [left %, top %, width px, text, rotation deg, tumble seconds].
const SCRAPS: ReadonlyArray<readonly [number, number, number, string, number, number]> = [
  [28, 52, 110, "$4,8", -14, 26],
  [44, 62, 86, "DUE", 10, 31],
  [88, 18, 70, "12.00", -6, 23],
  [12, 80, 64, "ACCT", 18, 29],
  [58, 86, 74, "$657", -20, 35],
  [92, 58, 58, "88-2", 8, 27],
];

// Seeded, not random: the same jagged edges on the server and in the browser.
const rnd = (i: number, k: number) => (Math.sin(i * 97 + k * 13.7) + 1) / 2;
const n = (v: number) => v.toFixed(2);

function tornEdge(i: number): string {
  const pts: string[] = [];
  for (let k = 0; k <= 8; k++) pts.push(`${k * 12.5},${n(6 + rnd(i, k) * 10)}`);
  for (let k = 0; k <= 5; k++) pts.push(`${n(92 + rnd(i, k + 20) * 8)},${16 + k * 9}`);
  for (let k = 8; k >= 0; k--) pts.push(`${k * 12.5},${n(58 + rnd(i, k + 40) * 10)}`);
  for (let k = 5; k >= 0; k--) pts.push(`${n(rnd(i, k + 60) * 8)},${16 + k * 9}`);
  return pts.join(" ");
}

/** The scraps that sit on one parallax depth (0, 1 or 2). Decoration only. */
export function Scraps({ depth }: { depth: number }) {
  return (
    <>
      {SCRAPS.map(([x, y, w, text, r, seconds], i) => {
        if (i % 3 !== depth) return null;
        const points = tornEdge(i);
        const lineY = n(44 + rnd(i, 3) * 6);
        const style = {
          left: `${x}%`,
          top: `${y}%`,
          width: w,
          "--r": `${r}deg`,
          animationDuration: `${seconds}s`,
          animationDelay: `${n(-seconds * rnd(i, 5))}s`,
        } as CSSProperties;
        return (
          <div key={text} className="scrap" style={style}>
            <svg viewBox="0 0 100 76">
              <polygon points={points} fill="#FFFFFF" />
              <polygon points={points} fill="#0E3B2E" opacity=".04" transform="translate(0 4) scale(1 .5)" />
              <line
                x1="10"
                y1={lineY}
                x2={n(50 + rnd(i, 4) * 30)}
                y2={lineY}
                stroke="#D7DDD8"
                strokeWidth="2"
                strokeDasharray="3 3"
              />
              <text x="12" y="36" fontFamily="ui-monospace,Menlo,monospace" fontSize="17" fontWeight="700" fill="#2B3A34">
                {text}
              </text>
            </svg>
          </div>
        );
      })}
    </>
  );
}
