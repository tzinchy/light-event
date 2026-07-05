import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone — минимальный рантайм для docker-образа (infra/docker-compose.yml, профиль full)
  output: "standalone",
  // в dev проксируем API на uvicorn; в проде это делает nginx (infra/nginx)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL ?? "http://localhost:8000"}/api/:path*`,
      },
      {
        // WS-чат: в dev проксируем на uvicorn (в проде — nginx /ws/)
        source: "/ws/:path*",
        destination: `${process.env.API_URL ?? "http://localhost:8000"}/ws/:path*`,
      },
    ];
  },
};

export default nextConfig;
