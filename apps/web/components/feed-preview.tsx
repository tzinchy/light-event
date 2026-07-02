"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { feedApiV1VacanciesGet, type FeedItemOut } from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { ShiftCard } from "@/components/shift-card";
import { DICT } from "@/lib/dict";

/** Превью 3 реальных смен на лендинге; при пустой ленте секция не показывается (real-data-only). */
export function FeedPreview() {
  const [shifts, setShifts] = useState<FeedItemOut[]>([]);

  useEffect(() => {
    void (async () => {
      const { data } = await feedApiV1VacanciesGet();
      setShifts((data ?? []).slice(0, 3));
    })();
  }, []);

  if (shifts.length === 0) return null;

  return (
    <section className="mx-auto w-full max-w-6xl px-4 pb-16">
      <div className="mb-6 flex items-baseline justify-between">
        <h2 className="text-2xl font-semibold">{DICT.feedTitle}</h2>
        <Button asChild variant="ghost" size="sm">
          <Link href="/feed">Все смены →</Link>
        </Button>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {shifts.map((shift) => (
          <ShiftCard key={shift.vacancy_uuid} shift={shift} />
        ))}
      </div>
    </section>
  );
}
