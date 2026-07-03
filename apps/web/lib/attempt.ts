/** Логика выбора вариантов при прохождении теста (референс: single — radio, multi — чекбоксы). */
export function toggleChoice(selected: number[], index: number, multi: boolean): number[] {
  if (!multi) return [index];
  return selected.includes(index)
    ? selected.filter((i) => i !== index)
    : [...selected, index].sort((a, b) => a - b);
}

/** Остаток cooldown в формате референса «Повтор через 14:59»; null — cooldown истёк. */
export function formatCooldownLeft(untilIso: string, now: Date = new Date()): string | null {
  const totalSec = Math.floor((new Date(untilIso).getTime() - now.getTime()) / 1000);
  if (totalSec <= 0) return null;
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  const mm = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${String(m).padStart(2, "0")}:${mm}` : `${m}:${mm}`;
}
