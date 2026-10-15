import path from "node:path";
import type { NextConfig } from "next";

// The browser talks to the API through this app (same origin), so no CORS setup is needed.
// BACKEND_URL is read at build time (rewrites are compiled into the build).
const backend = process.env.BACKEND_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
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
