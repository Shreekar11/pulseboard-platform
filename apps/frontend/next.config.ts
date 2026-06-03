import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN;
    if (!origin) return [];
    return [
      { source: "/api/:path*", destination: `${origin}/api/:path*` },
      { source: "/healthz", destination: `${origin}/healthz` },
      { source: "/readyz", destination: `${origin}/readyz` },
    ];
  },
};

export default nextConfig;
