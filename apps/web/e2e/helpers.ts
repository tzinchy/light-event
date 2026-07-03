import { execFileSync } from "node:child_process";
import { expect, type Page } from "@playwright/test";

/** Уникальный телефон на прогон — тесты не зависят друг от друга и от прошлых прогонов. */
export function uniquePhone(): string {
  return `+7999${String(Date.now()).slice(-7)}`;
}

/** SMS-код достаём из Redis (ConsoleSmsProvider никуда не шлёт — это dev-стенд). */
export function smsCode(phone: string): string {
  const out = execFileSync(
    "docker",
    ["exec", "light-event-redis-1", "redis-cli", "GET", `otp:sms:code:${phone}`],
    { encoding: "utf8" },
  ).trim();
  if (!/^\d{6}$/.test(out)) throw new Error(`SMS-код для ${phone} не найден в Redis: "${out}"`);
  return out;
}

const MAILPIT_URL = process.env.E2E_MAILPIT_URL ?? "http://localhost:8025";

/** Код подтверждения почты — из Mailpit HTTP API (реальное SMTP-письмо). */
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

/** Полный вход по OTP через UI. Возвращает использованный телефон. */
export async function loginByPhone(page: Page, phone = uniquePhone()): Promise<string> {
  await page.goto("/auth");
  await page.getByRole("button", { name: "Войти по номеру телефона" }).click();
  await page.getByLabel("Номер телефона").fill(phone);
  await page.getByRole("button", { name: "Получить код" }).click();

  await expect(page.getByText("Код отправлен на")).toBeVisible();
  const code = smsCode(phone);
  await page.getByRole("group", { name: "Код из SMS" }).locator("input").first().click();
  await page.keyboard.type(code);
  await page.getByRole("button", { name: "Подтвердить", exact: true }).click();
  return phone;
}
