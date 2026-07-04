/** Отзыв доступен после выплаты за смену (paid) или полного завершения (done). */
export function canReview(applicationStatus: string): boolean {
  return applicationStatus === "paid" || applicationStatus === "done";
}

/** Форма отзыва готова к отправке: выбрана оценка 1–5 (текст необязателен). */
export function reviewReady(rating: number): boolean {
  return Number.isInteger(rating) && rating >= 1 && rating <= 5;
}
