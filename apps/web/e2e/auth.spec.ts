import { expect, test } from "@playwright/test";
import { emailCode, loginByPhone } from "./helpers";

test("новый пользователь входит по OTP и попадает на шаг верификации", async ({ page }) => {
  await loginByPhone(page);

  // новый пользователь после кода попадает на KYC-шаг с согласием на обработку ПДн
  await expect(page.getByText("согласие на обработку персональных данных")).toBeVisible();
  await expect(page.getByRole("button", { name: "Завершить верификацию" })).toBeDisabled();
});

test("пользователь подтверждает почту кодом из письма", async ({ page }) => {
  const phone = await loginByPhone(page);
  const email = `e2e-${phone.slice(1)}@example.com`;

  await page.goto("/profile");
  await page.getByLabel("Адрес электронной почты").fill(email);
  await page.getByRole("button", { name: "Получить код" }).click();
  await expect(page.getByText("Введите код из письма")).toBeVisible();

  const code = await emailCode(email);
  await page.getByRole("group", { name: "Код из SMS" }).locator("input").first().click();
  await page.keyboard.type(code);
  await page.getByRole("button", { name: "Подтвердить почту" }).click();

  await expect(page.getByText("Подтверждена").first()).toBeVisible();
});
