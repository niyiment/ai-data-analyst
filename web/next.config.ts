import type { NextConfig } from "next";

// Empty counts as unset: an empty value would make the rewrite point at itself.
const apiBaseUrl = (process.env.API_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");
if (!/^https?:\/\/[^/]+/.test(apiBaseUrl)) {
  throw new Error(`API_BASE_URL must be an absolute http(s) URL, got "${apiBaseUrl}"`);
}

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
