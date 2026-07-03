import { expect, test } from "@playwright/test";
import { grantAdmin, loginByPhone } from "./helpers";

// Полный путь организации: заявка с точкой на карте → верификация админом →
// кабинет открылся → филиал → черновик смены. Дальше цикла (публикация,
// модерация вакансии, отклик) пока нет админского UI — сценарий дорастим вместе с ним.
test("организация: заявка → верификация админом → черновик смены", async ({ browser }) => {
  test.setTimeout(90_000);
  const orgName = `Гранд Холл E2E ${Date.now()}`;
  const eventTitle = `Банкет E2E ${Date.now()}`;

  // — менеджер подаёт заявку на регистрацию организации
  const managerCtx = await browser.newContext();
  const manager = await managerCtx.newPage();
  await loginByPhone(manager);

  await manager.goto("/org");
  await manager.getByLabel("Название организации").fill(orgName);
  await manager.getByLabel("ИНН").fill("7707083893");
  await manager.getByLabel("ОГРН").fill("1027700132195");
  await manager.getByLabel("Контактный телефон").fill("+79990001122");
  await manager.getByLabel("Адрес").fill("Москва, Тверская, 1");

  // точка на карте: клик по центру canvas MapLibre ставит маркер
  const canvas = manager.locator(".maplibregl-canvas");
  await canvas.click();
  await expect(manager.getByText(/^5\d\.\d+, \d+\.\d+$/)).toBeVisible();

  const submit = manager.getByRole("button", { name: "Отправить заявку" });
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(manager.getByText("Заявка на проверке")).toBeVisible();

  // — админ (назначается операторской CLI) подтверждает заявку в /admin
  const adminCtx = await browser.newContext();
  const admin = await adminCtx.newPage();
  const adminPhone = await loginByPhone(admin);
  grantAdmin(adminPhone);

  await admin.goto("/admin");
  const card = admin.locator('[data-slot="card"]').filter({ hasText: orgName });
  await expect(card.getByText("На проверке")).toBeVisible();
  await card.getByRole("button", { name: "Подтвердить" }).click();
  await expect(admin.getByText(`«${orgName}» подтверждена`)).toBeVisible();

  // — кабинет менеджера открылся: филиал + черновик смены
  await manager.goto("/org/create");
  await expect(manager.getByRole("heading", { name: "Карточка события" })).toBeVisible();

  await manager.getByRole("button", { name: "Новый филиал" }).click();
  const dialog = manager.getByRole("dialog");
  await dialog.getByLabel("Название").fill("Основная площадка");
  await dialog.getByLabel("Адрес").fill("Тверская, 9");
  await dialog.getByRole("button", { name: "Создать" }).click();
  await expect(dialog).toBeHidden();

  await manager.getByLabel("Название события").fill(eventTitle);
  const tomorrow = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 10);
  await manager.getByLabel("Дата").fill(tomorrow);

  await manager.getByRole("button", { name: "Сохранить черновик" }).click();
  await expect(manager.getByText("Черновик сохранён")).toBeVisible();
  await expect(manager).toHaveURL(/\/org\/events$/);
  await expect(manager.getByText(eventTitle)).toBeVisible();

  await managerCtx.close();
  await adminCtx.close();
});
