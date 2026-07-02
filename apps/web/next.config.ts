import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // в dev проксируем API на uvicorn; в проде это делает nginx (infra/nginx)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
