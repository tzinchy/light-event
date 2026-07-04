import { describe, expect, it } from "vitest";
import { canReview, reviewReady } from "./review";

describe("canReview", () => {
  it("отзыв доступен после выплаты и завершения", () => {
    expect(canReview("paid")).toBe(true);
    expect(canReview("done")).toBe(true);
  });

  it("до выплаты отзыв недоступен", () => {
    expect(canReview("review")).toBe(false);
    expect(canReview("confirmed")).toBe(false);
    expect(canReview("reserve")).toBe(false);
  });
});

describe("reviewReady", () => {
  it("нужна оценка 1–5", () => {
    expect(reviewReady(0)).toBe(false);
    expect(reviewReady(1)).toBe(true);
    expect(reviewReady(5)).toBe(true);
    expect(reviewReady(6)).toBe(false);
  });
});
