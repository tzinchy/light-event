import { execFileSync } from "node:child_process";
import { expect, type Page } from "@playwright/test";

const MAILPIT_URL = process.env.E2E_MAILPIT_URL ?? "http://localhost:8025";

/** Уникальная почта на прогон — случайная: параллельные worker'ы не коллидируют. */
export function uniqueEmail(): string {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}@example.com`;
}

/** Код подтверждения — из Mailpit HTTP API (реальное SMTP-письмо в dev-стенде). */
export async function emailCode(email: string): Promise<string> {
  for (let attempt = 0; attempt < 10; attempt++) {
    const resp = await fetch(`${MAILPIT_URL}/api/v1/search?query=to:${encodeURIComponent(email)}`);
    const data = (await resp.json()) as { messages: { Subject: string }[] };
    const match = data.messages?.[0]?.Subject.match(/(\d{6})/);
    if (match) return match[1];
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Письмо для ${email} не пришло в Mailpit`);
}

/** platform_role=admin через операторскую CLI в api-контейнере (нужен полный стенд — make full). */
export function grantAdmin(email: string): void {
  const out = execFileSync(
    "docker",
    ["exec", "light-event-api-1", "uv", "run", "--no-dev", "python", "-m", "app.cli", "grant-admin", email],
    { encoding: "utf8" },
  );
  if (!out.includes("администратор")) throw new Error(`grant-admin не сработал: ${out}`);
}

/** Полный вход по e-mail-OTP через UI. Возвращает использованную почту. */
export async function loginByEmail(page: Page, email = uniqueEmail()): Promise<string> {
  await page.goto("/auth");
  await page.getByRole("button", { name: "Войти по почте" }).click();
  await page.getByLabel("Электронная почта").fill(email);
  await page.getByRole("button", { name: "Получить код" }).click();

  await expect(page.getByText("Код отправлен на")).toBeVisible();
  const code = await emailCode(email);
  await page.getByRole("group", { name: "Код подтверждения" }).locator("input").first().click();
  await page.keyboard.type(code);
  await page.getByRole("button", { name: "Подтвердить", exact: true }).click();
  // ждём KYC-шаг: уйти раньше — гонка, токены могут не успеть сохраниться в localStorage
  await expect(page.getByRole("button", { name: "Завершить верификацию" })).toBeVisible();
  return email;
}
