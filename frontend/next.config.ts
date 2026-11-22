import path from "node:path";
import type { NextConfig } from "next";

// The browser only ever talks to this Next.js app. /api/* is proxied to the
// FastAPI backend, so the backend needs no CORS setup and no URL is exposed.
const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/+$/, "");

// Pin the project root to this folder so a stray lockfile higher up (e.g. in $HOME) is never picked up.
const ROOT = path.resolve(__dirname);

const nextConfig: NextConfig = {
  outputFileTracingRoot: ROOT,
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    root: ROOT,
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` }];
  },
};

export default nextConfig;
