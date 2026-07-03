import { describe, expect, it } from "vitest";
import { isValidInn, isValidOgrn } from "./requisites";

describe("isValidInn", () => {
  it("принимает корректный 10-значный ИНН юрлица", () => {
    expect(isValidInn("7707083893")).toBe(true);
  });

  it("принимает корректный 12-значный ИНН ИП", () => {
    // контрольные цифры посчитаны по алгоритму ФНС
    expect(isValidInn("500100732259")).toBe(true);
  });

  it("отклоняет неверную контрольную цифру", () => {
    expect(isValidInn("7707083894")).toBe(false);
    expect(isValidInn("500100732258")).toBe(false);
  });

  it("отклоняет неверную длину и нецифровые символы", () => {
    expect(isValidInn("123")).toBe(false);
    expect(isValidInn("77070838930")).toBe(false);
    expect(isValidInn("770708389x")).toBe(false);
    expect(isValidInn("")).toBe(false);
  });
});

describe("isValidOgrn", () => {
  it("принимает корректный 13-значный ОГРН", () => {
    expect(isValidOgrn("1027700132195")).toBe(true);
  });

  it("принимает корректный 15-значный ОГРНИП", () => {
    expect(isValidOgrn("304500116000157")).toBe(true);
  });

  it("отклоняет неверную контрольную цифру", () => {
    expect(isValidOgrn("1027700132196")).toBe(false);
  });

  it("отклоняет неверную длину и нецифровые символы", () => {
    expect(isValidOgrn("10277")).toBe(false);
    expect(isValidOgrn("102770013219x")).toBe(false);
    expect(isValidOgrn("")).toBe(false);
  });
});
