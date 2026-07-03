import { describe, expect, it } from "vitest";
import { formatCooldownLeft, toggleChoice } from "./attempt";

describe("toggleChoice", () => {
  it("одиночный вопрос: выбор заменяет предыдущий", () => {
    expect(toggleChoice([], 2, false)).toEqual([2]);
    expect(toggleChoice([2], 0, false)).toEqual([0]);
  });

  it("одиночный вопрос: повторный клик не снимает выбор", () => {
    expect(toggleChoice([1], 1, false)).toEqual([1]);
  });

  it("multi: клики добавляют и снимают, порядок по возрастанию", () => {
    expect(toggleChoice([], 2, true)).toEqual([2]);
    expect(toggleChoice([2], 0, true)).toEqual([0, 2]);
    expect(toggleChoice([0, 2], 2, true)).toEqual([0]);
  });
});

describe("formatCooldownLeft", () => {
  const now = new Date("2026-07-03T12:00:00Z");

  it("минуты и секунды в формате референса «14:59»", () => {
    expect(formatCooldownLeft("2026-07-03T12:14:59Z", now)).toBe("14:59");
    expect(formatCooldownLeft("2026-07-03T12:00:07Z", now)).toBe("0:07");
  });

  it("больше часа — с часами", () => {
    expect(formatCooldownLeft("2026-07-03T13:01:05Z", now)).toBe("1:01:05");
  });

  it("истёк или в прошлом — null", () => {
    expect(formatCooldownLeft("2026-07-03T12:00:00Z", now)).toBeNull();
    expect(formatCooldownLeft("2026-07-03T11:59:00Z", now)).toBeNull();
  });
});
