import { describe, expect, it } from "vitest";
import { kopToRub, rubInputToKop } from "./format";

describe("kopToRub", () => {
  it("целые рубли без копеек", () => {
    expect(kopToRub(99_000)).toBe("990 ₽");
    expect(kopToRub(150_000)).toBe("1 500 ₽");
  });

  it("копейки через запятую", () => {
    expect(kopToRub(123_456)).toBe("1 234,56 ₽");
    expect(kopToRub(101)).toBe("1,01 ₽");
  });

  it("ноль и отрицательные", () => {
    expect(kopToRub(0)).toBe("0 ₽");
    expect(kopToRub(-37_800_00)).toBe("−37 800 ₽");
  });
});

describe("rubInputToKop", () => {
  it("целые и дробные рубли", () => {
    expect(rubInputToKop("990")).toBe(99_000);
    expect(rubInputToKop("1234,56")).toBe(123_456);
    expect(rubInputToKop("1234.5")).toBe(123_450);
  });

  it("пробелы-разделители допустимы", () => {
    expect(rubInputToKop("200 000")).toBe(20_000_000);
  });

  it("мусор не парсится", () => {
    expect(rubInputToKop("")).toBeNull();
    expect(rubInputToKop("12,345")).toBeNull();
    expect(rubInputToKop("abc")).toBeNull();
    expect(rubInputToKop("-5")).toBeNull();
  });
});
