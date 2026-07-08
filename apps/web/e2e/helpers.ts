import { execFileSync } from "node:child_process";
import { expect, type Locator, type Page } from "@playwright/test";

/** Кликнуть точку на Yandex-карте (map-picker), дождавшись готовности API — иначе клик до
 * инициализации карты не ставит маркер. `scope` — страница или диалог, где искать карту. */
export async function pickMapPoint(page: Page, scope: Page | Locator = page): Promise<void> {
  await page.waitForFunction(() => Boolean((window as unknown as { ymaps?: { Map?: unknown } }).ymaps?.Map), null, {
    timeout: 20000,
  });
  const map = scope.locator('[data-testid="map-picker"]');
  await map.waitFor();
  await page.waitForTimeout(2000); // дать карте проинициализировать слой событий
  await map.click({ position: { x: 200, y: 120 } });
}

/** Уникальная почта на прогон — случайная: параллельные worker'ы не коллидируют. */
export function uniqueEmail(): string {
  return `e2e-${Date.now()}-${Math.floor(Math.random() * 1_000_000)}@example.com`;
}

/** Код подтверждения — из журнала email_message (§11.14), тема письма содержит код.
 * Для e2e стенд поднимают без реального SMTP (SMTP_HOST= make full) — письма уходят в лог,
 * а журнал заполняется в любом случае. */
export async function emailCode(email: string): Promise<string> {
  for (let attempt = 0; attempt < 10; attempt++) {
    const out = execFileSync(
      "docker",
      [
        "exec",
        "light-event-db-1",
        "psql",
        "-U",
        "light_event",
        "-d",
        "light_event",
        "-tA",
        "-c",
        `SELECT subject FROM email_message WHERE to_email = '${email}' ORDER BY email_message_uuid DESC LIMIT 1`,
      ],
      { encoding: "utf8" },
    );
    const match = out.match(/(\d{6})/);
    if (match) return match[1];
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Письмо для ${email} не появилось в журнале email_message`);
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
