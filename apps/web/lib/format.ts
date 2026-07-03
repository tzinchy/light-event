/** Деньги приходят из API целыми копейками (skill money-ledger). */
export function kopToRub(kop: number): string {
  const sign = kop < 0 ? "−" : "";
  const abs = Math.abs(kop);
  // ru-RU разделяет тысячи NBSP — нормализуем в обычный пробел, чтобы строки были предсказуемыми
  const rub = Math.floor(abs / 100).toLocaleString("ru-RU").replace(/ /g, " ");
  const rest = abs % 100;
  return rest === 0 ? `${sign}${rub} ₽` : `${sign}${rub},${String(rest).padStart(2, "0")} ₽`;
}

/** Ввод суммы в рублях (возможна запятая) → целые копейки; null, если не парсится. */
export function rubInputToKop(input: string): number | null {
  const normalized = input.replace(/\s/g, "").replace(",", ".");
  if (!/^\d+(\.\d{1,2})?$/.test(normalized)) return null;
  return Math.round(parseFloat(normalized) * 100);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
}

/** «12 июля · 16:00–23:00» для карточки смены. */
export function formatShiftWindow(startsIso: string, endsIso: string): string {
  const starts = new Date(startsIso);
  const ends = new Date(endsIso);
  const day = starts.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  const time = (d: Date) => d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  return `${day} · ${time(starts)}–${time(ends)}`;
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}
