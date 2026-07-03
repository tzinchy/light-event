import { defineConfig } from "@playwright/test";

// e2e ходят на живой стенд: `make full` (nginx на :8080 — дефолт `make e2e`)
// или dev-стенд make infra + make api + make web (E2E_BASE_URL=http://localhost:3000).
// Коды перехватываются через реальные интерфейсы: SMS — Redis, почта — Mailpit API.
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
});
