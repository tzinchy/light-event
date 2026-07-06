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

export const ENGLISH_OPTIONS = [
  { value: "none", label: "Не владею" },
  { value: "basic", label: "Базовый" },
  { value: "intermediate", label: "Средний" },
  { value: "advanced", label: "Продвинутый" },
  { value: "fluent", label: "Свободный" },
] as const;

export const ENGLISH_LABEL: Record<string, string> = Object.fromEntries(
  ENGLISH_OPTIONS.map((o) => [o.value, o.label]),
);

export const EDUCATION_OPTIONS = [
  { value: "secondary", label: "Среднее" },
  { value: "vocational", label: "Среднее специальное" },
  { value: "higher", label: "Высшее" },
] as const;

export const EDUCATION_LABEL: Record<string, string> = Object.fromEntries(
  EDUCATION_OPTIONS.map((o) => [o.value, o.label]),
);

export const GENDER_OPTIONS = [
  { value: "male", label: "Мужской" },
  { value: "female", label: "Женский" },
] as const;

export const GENDER_LABEL: Record<string, string> = Object.fromEntries(
  GENDER_OPTIONS.map((o) => [o.value, o.label]),
);
