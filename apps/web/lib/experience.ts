// Опыт работы соискателя (PLAN §3.1) — значения синхронны с бэком EXPERIENCE_VALUES.
export const EXPERIENCE_OPTIONS = [
  { value: "none", label: "Без опыта" },
  { value: "up_to_1y", label: "До года" },
  { value: "y1_3", label: "От года до трёх" },
  { value: "y3_6", label: "От трёх до шести лет" },
] as const;

export const EXPERIENCE_LABEL: Record<string, string> = Object.fromEntries(
  EXPERIENCE_OPTIONS.map((o) => [o.value, o.label]),
);
