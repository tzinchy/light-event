"use client";

import { useRef } from "react";
import { cn } from "@/lib/utils";

export const OTP_LENGTH = 6;

/** Чистая логика ввода в ячейку: возвращает новое значение и куда двигать фокус. */
export function applyOtpChange(
  value: string,
  index: number,
  input: string,
): { value: string; focus: number | null } {
  const digits = input.replace(/\D/g, "");
  if (!digits) return { value, focus: null };
  const chars = value.padEnd(OTP_LENGTH, " ").split("");
  let cursor = index;
  for (const d of digits) {
    if (cursor >= OTP_LENGTH) break;
    chars[cursor] = d;
    cursor += 1;
  }
  return {
    value: chars.join("").trimEnd(),
    focus: Math.min(cursor, OTP_LENGTH - 1),
  };
}

export function applyOtpBackspace(
  value: string,
  index: number,
): { value: string; focus: number | null } {
  const chars = value.padEnd(OTP_LENGTH, " ").split("");
  if (chars[index] !== " ") {
    chars[index] = " ";
    return { value: chars.join("").trimEnd(), focus: null };
  }
  if (index === 0) return { value, focus: null };
  chars[index - 1] = " ";
  return { value: chars.join("").trimEnd(), focus: index - 1 };
}

export function OtpInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  const focusCell = (i: number | null) => {
    if (i !== null) refs.current[i]?.focus();
  };

  return (
    <div className="flex justify-center gap-2" role="group" aria-label="Код из SMS">
      {Array.from({ length: OTP_LENGTH }, (_, i) => (
        <input
          key={i}
          ref={(el) => {
            refs.current[i] = el;
          }}
          inputMode="numeric"
          autoComplete={i === 0 ? "one-time-code" : "off"}
          aria-label={`Цифра ${i + 1}`}
          className={cn(
            "size-12 rounded-lg border bg-card text-center font-mono text-xl outline-none",
            "focus:border-ring focus:ring-2 focus:ring-ring/30",
            disabled && "opacity-50",
          )}
          disabled={disabled}
          value={value[i]?.trim() ?? ""}
          onChange={(e) => {
            const next = applyOtpChange(value, i, e.target.value);
            onChange(next.value);
            focusCell(next.focus);
          }}
          onKeyDown={(e) => {
            if (e.key === "Backspace") {
              e.preventDefault();
              const next = applyOtpBackspace(value, i);
              onChange(next.value);
              focusCell(next.focus);
            }
          }}
          onPaste={(e) => {
            e.preventDefault();
            const next = applyOtpChange(value, i, e.clipboardData.getData("text"));
            onChange(next.value);
            focusCell(next.focus);
          }}
        />
      ))}
    </div>
  );
}
