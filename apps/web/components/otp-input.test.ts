import { describe, expect, it } from "vitest";
import { applyOtpBackspace, applyOtpChange } from "./otp-input";

describe("applyOtpChange", () => {
  it("ввод цифры двигает фокус вперёд", () => {
    expect(applyOtpChange("", 0, "1")).toEqual({ value: "1", focus: 1 });
    expect(applyOtpChange("1", 1, "2")).toEqual({ value: "12", focus: 2 });
  });

  it("вставка целого кода раскладывается по ячейкам", () => {
    expect(applyOtpChange("", 0, "123456")).toEqual({ value: "123456", focus: 5 });
  });

  it("вставка длиннее шести обрезается", () => {
    expect(applyOtpChange("", 0, "12345678").value).toBe("123456");
  });

  it("не-цифры игнорируются", () => {
    expect(applyOtpChange("12", 2, "a")).toEqual({ value: "12", focus: null });
  });

  it("перезапись в середине", () => {
    expect(applyOtpChange("123456", 2, "9").value).toBe("129456");
  });
});

describe("applyOtpBackspace", () => {
  it("стирает текущую ячейку", () => {
    expect(applyOtpBackspace("123", 2)).toEqual({ value: "12", focus: null });
  });

  it("на пустой ячейке стирает предыдущую и двигает фокус назад", () => {
    expect(applyOtpBackspace("12", 2)).toEqual({ value: "1", focus: 1 });
  });

  it("в начале ничего не делает", () => {
    expect(applyOtpBackspace("", 0)).toEqual({ value: "", focus: null });
  });

  it("дырка в середине сохраняется через пробелы", () => {
    expect(applyOtpBackspace("123456", 3).value).toBe("123 56");
  });
});
