import { defineConfig } from "@playwright/test";

// e2e ходят на живой dev-стенд: make infra + make api + make web (см. README).
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
