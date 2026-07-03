// Валидация реквизитов на клиенте — зеркалит серверную (apps/api/app/company/schemas.py)

function controlDigit(digits: string, weights: number[]): number {
  const sum = weights.reduce((acc, w, i) => acc + w * Number(digits[i]), 0);
  return (sum % 11) % 10;
}

export function isValidInn(value: string): boolean {
  if (!/^\d{10}$|^\d{12}$/.test(value)) return false;
  if (value.length === 10) {
    return controlDigit(value, [2, 4, 10, 3, 5, 9, 4, 6, 8]) === Number(value[9]);
  }
  return (
    controlDigit(value, [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) === Number(value[10]) &&
    controlDigit(value, [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]) === Number(value[11])
  );
}

export function isValidOgrn(value: string): boolean {
  if (!/^\d{13}$|^\d{15}$/.test(value)) return false;
  if (value.length === 13) {
    return Number(BigInt(value.slice(0, 12)) % 11n % 10n) === Number(value[12]);
  }
  return Number(BigInt(value.slice(0, 14)) % 13n % 10n) === Number(value[14]);
}
