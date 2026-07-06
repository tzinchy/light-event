import { expect, test, type Page } from "@playwright/test";
import { grantAdmin, loginByEmail, pickMapPoint } from "./helpers";

// Полный продуктовый цикл (PLAN §11.3): заявка организации с точкой на карте →
// верификация админом → пополнение с пруфом → зачисление админом →
// платная публикация смены → модерация публикации → отклик соискателя → найм.
// Нужен полный стенд (make full): grant-admin выполняется в api-контейнере.
test("полный цикл: организация → модерация → публикация → отклик → найм", async ({ browser }) => {
  test.setTimeout(120_000);
  const orgName = `Гранд Холл E2E ${Date.now()}`;
  const eventTitle = `Банкет E2E ${Date.now()}`;

  // — менеджер подаёт заявку на регистрацию организации
  const managerCtx = await browser.newContext();
  const manager = await managerCtx.newPage();
  await loginByEmail(manager);

  await manager.goto("/org");
  await manager.getByLabel("Название организации").fill(orgName);
  await manager.getByLabel("ИНН").fill("7707083893");
  await manager.getByLabel("ОГРН").fill("1027700132195");
  await manager.getByLabel("Контактный телефон").fill("+79990001122");
  await manager.getByLabel("ФИО заявителя").fill("Марина Кузнецова");
  await manager.getByLabel("Должность").fill("Управляющий");
  await manager.getByLabel("Почта заявителя").fill("manager-e2e@example.com");
  await manager.getByLabel("Адрес").fill("Москва, Тверская, 1");

  // точка на карте: клик по Yandex-карте ставит маркер (ждём готовности API)
  await pickMapPoint(manager);
  await expect(manager.getByText(/^5\d\.\d+, \d+\.\d+$/)).toBeVisible();

  const submit = manager.getByRole("button", { name: "Отправить заявку" });
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(manager.getByText("Заявка на проверке")).toBeVisible();

  // — админ (назначается операторской CLI) подтверждает заявку в /admin
  const adminCtx = await browser.newContext();
  const admin = await adminCtx.newPage();
  const adminEmail = await loginByEmail(admin);
  grantAdmin(adminEmail);

  await admin.goto("/admin");
  // дефолт админки — «Обзор»; очередь заявок на подтверждение — в разделе «Организации»
  await admin.getByRole("button", { name: "Организации" }).click();
  const orgCard = admin.locator('[data-slot="card"]').filter({ hasText: orgName });
  await expect(orgCard.getByText("На проверке")).toBeVisible();
  await orgCard.getByRole("button", { name: "Подтвердить" }).click();
  await expect(admin.getByText(`«${orgName}» подтверждена`)).toBeVisible();

  // — кабинет открылся: заявка на пополнение с пруфом платежа
  await manager.goto("/org/balance");
  await manager.getByRole("button", { name: "Пополнить" }).click();
  const topupDialog = manager.getByRole("dialog");
  // 990 ₽ публикация + резерв 3 150 ₽ (7 ч × 450) под одного подтверждённого
  await topupDialog.getByLabel("Сумма, ₽").fill("5000");
  await topupDialog
    .locator('input[type="file"]')
    .setInputFiles({ name: "proof.jpg", mimeType: "image/jpeg", buffer: Buffer.from("proof-bytes") });
  await topupDialog.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(manager.getByText("Заявка на пополнение отправлена администратору")).toBeVisible();

  // — админ зачисляет пополнение во вкладке «Пополнения»
  await admin.goto("/admin");
  await admin.getByRole("button", { name: "Пополнения" }).click();
  const topupCard = admin.locator('[data-slot="card"]').filter({ hasText: "5 000 ₽" }).first();
  await topupCard.getByRole("button", { name: "Зачислить" }).click();
  await expect(admin.getByText("Пополнение зачислено")).toBeVisible();

  await manager.goto("/org/balance");
  await expect(manager.getByText("5 000 ₽").first()).toBeVisible();

  // — создание смены и платная публикация (990 ₽)
  await manager.goto("/org/create");
  await manager.getByRole("button", { name: "Новый филиал" }).click();
  const filialDialog = manager.getByRole("dialog");
  await filialDialog.getByLabel("Название").fill("Основная площадка");
  await filialDialog.getByLabel("Адрес").fill("Тверская, 9");
  await pickMapPoint(manager, filialDialog); // координаты филиала теперь обязательны
  await filialDialog.getByRole("button", { name: "Создать" }).click();
  await expect(filialDialog).toBeHidden();

  await manager.getByLabel("Название события").fill(eventTitle);
  const tomorrow = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 10);
  await manager.getByLabel("Дата").fill(tomorrow);

  await manager.getByRole("button", { name: "Оплатить и опубликовать" }).click();
  await expect(manager.getByText("Оплачено · отправлено на модерацию администратора")).toBeVisible();

  // — админ одобряет публикацию во вкладке «Публикации»
  await admin.goto("/admin");
  await admin.getByRole("button", { name: "Публикации" }).click();
  const pubCard = admin.locator('[data-slot="card"]').filter({ hasText: eventTitle });
  await expect(pubCard.getByText("Публикация смены")).toBeVisible();
  await pubCard.getByRole("button", { name: "Одобрить" }).click();
  await expect(pubCard).toBeHidden();

  // — соискатель находит смену в ленте и откликается
  const workerCtx = await browser.newContext();
  const worker = await workerCtx.newPage();
  await loginByEmail(worker);
  await worker.goto("/feed");
  await worker.getByText(eventTitle).first().click();
  await worker.getByRole("button", { name: "Откликнуться" }).click();
  await expect(worker.getByText("Отклик отправлен").first()).toBeVisible();

  // — менеджер нанимает (отклики сгруппированы по событию)
  await manager.goto("/org/candidates");
  await manager.getByRole("button", { name: "Нанять", exact: true }).first().click();
  await expect(manager.getByRole("button", { name: "Нанят", exact: true })).toBeVisible();

  // — админ проводит выплату во вкладке «Выплаты»
  await admin.goto("/admin");
  await admin.getByRole("button", { name: "Выплаты" }).click();
  const payoutCard = admin.locator('[data-slot="card"]').filter({ hasText: eventTitle });
  await payoutCard.getByRole("button", { name: "Провести выплату" }).click();
  await expect(admin.getByText("Выплата проведена")).toBeVisible();

  // — у организации резерв списан, выплата в истории «Выплачено»
  await manager.goto("/org/balance");
  await expect(
    manager.locator('[data-slot="card"]').filter({ hasText: "Выплаты к проведению" }).getByText("Выплачено"),
  ).toBeVisible();

  // — после выплаты соискатель оставляет отзыв об организации
  await worker.goto("/apps");
  await worker.getByText(eventTitle).first().click();
  await expect(worker.getByText("Оставить отзыв об организации")).toBeVisible();
  await worker.getByRole("radio", { name: "Оценка 5" }).click();
  await worker
    .getByPlaceholder("Как прошла смена? Что понравилось, что улучшить")
    .fill("Всё чётко, выплата пришла сразу");
  await worker.getByRole("button", { name: "Отправить отзыв" }).click();
  await expect(worker.getByText("Отзыв по этой смене отправлен")).toBeVisible();

  // — организация видит отзыв и рейтинг
  await manager.goto("/org/reviews");
  await expect(manager.getByText("Всё чётко, выплата пришла сразу")).toBeVisible();
  await expect(manager.getByText("5.0")).toBeVisible();

  // — соискатель подаёт жалобу, админ решает её во вкладке «Жалобы»
  await worker.getByRole("button", { name: "Пожаловаться на организацию" }).click();
  const complaintDialog = worker.getByRole("dialog");
  await complaintDialog.getByPlaceholder("Опишите, что произошло").fill("Тестовая жалоба e2e");
  await complaintDialog.getByRole("button", { name: "Отправить жалобу" }).click();
  await expect(worker.getByText("Жалоба отправлена администратору")).toBeVisible();

  await admin.goto("/admin");
  // сводка платформы видна на лендинге «Обзор»
  await expect(admin.getByText("Оборот")).toBeVisible();
  await admin.getByRole("button", { name: "Жалобы" }).click();
  const complaintCard = admin.locator('[data-slot="card"]').filter({ hasText: "Тестовая жалоба e2e" }).first();
  await complaintCard.getByPlaceholder("Резолюция (обязательна)").fill("Проверено, выплата проведена");
  await complaintCard.getByRole("button", { name: "Решена" }).click();
  await expect(admin.getByText("Жалоба решена")).toBeVisible();

  // мобильный адаптив: на <md сайдбар скрыт, навигация кабинета — чипсами в main
  await manager.setViewportSize({ width: 390, height: 844 });
  await expect(manager.locator("main").getByRole("link", { name: "Баланс" })).toBeVisible();

  await managerCtx.close();
  await adminCtx.close();
  await workerCtx.close();
});
