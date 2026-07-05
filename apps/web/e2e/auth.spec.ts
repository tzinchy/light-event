import { expect, test } from "@playwright/test";
import { emailCode, loginByEmail, uniqueEmail } from "./helpers";

test("новый пользователь входит по e-mail-OTP и попадает на шаг верификации", async ({ page }) => {
  await loginByEmail(page);

  // новый пользователь после кода попадает на KYC-шаг с согласием на обработку ПДн
  await expect(page.getByText("согласие на обработку персональных данных")).toBeVisible();
  await expect(page.getByRole("button", { name: "Завершить верификацию" })).toBeDisabled();
});

test("пользователь меняет почту в профиле и подтверждает кодом из письма", async ({ page }) => {
  await loginByEmail(page);
  const newEmail = uniqueEmail();

  await page.goto("/profile");
  await page.getByLabel("Почта — ваш логин").fill(newEmail);
  await page.getByRole("button", { name: "Получить код" }).click();
  await expect(page.getByText("Введите код из письма")).toBeVisible();

  const code = await emailCode(newEmail);
  await page.getByRole("group", { name: "Код подтверждения" }).locator("input").first().click();
  await page.keyboard.type(code);
  await page.getByRole("button", { name: "Подтвердить почту" }).click();

  await expect(page.getByText("Подтверждена").first()).toBeVisible();
});
