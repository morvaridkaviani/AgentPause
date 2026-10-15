import path from "node:path";
import type { NextConfig } from "next";

// Two ways to build:
// - Server (default): a standalone Next.js server that forwards /api/v1, /docs and /redoc to the
//   FastAPI backend. BACKEND_URL is read at build time (rewrites are compiled into the build).
// - Static online demo (STATIC_EXPORT=1): plain files for GitHub Pages. There is no server; the
//   API runs in the browser (see public/py-worker.js). NEXT_PUBLIC_BASE_PATH is the URL prefix,
//   e.g. "/AgentPause" for https://<user>.github.io/AgentPause/.
const backend = process.env.BACKEND_URL ?? "http://localhost:8000";
const staticExport = process.env.STATIC_EXPORT === "1";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || undefined;

const nextConfig: NextConfig = staticExport
  ? {
      output: "export",
      basePath,
      trailingSlash: true,
      images: { unoptimized: true },
      reactStrictMode: true,
      poweredByHeader: false,
    }
  : {
      output: "standalone",
      outputFileTracingRoot: path.join(__dirname, ".."),
      reactStrictMode: true,
      poweredByHeader: false,
      async rewrites() {
        return [
          { source: "/api/:path*", destination: `${backend}/api/:path*` },
          { source: "/docs", destination: `${backend}/docs` },
          { source: "/redoc", destination: `${backend}/redoc` },
        ];
      },
    };

export default nextConfig;
