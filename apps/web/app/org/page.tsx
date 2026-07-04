"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useOrg } from "@/lib/org-context";

// Макет «Аналитики» из референса. Значения — только реальные (skill real-data-only):
// пока нет агрегатов по событиям, показываем честные пустые состояния, а не выдуманные цифры.
const METRICS = [
  { label: "Заполняемость", caption: "смен закрыто" },
  { label: "Средний рейтинг", caption: "по отзывам" },
  { label: "Активные события", caption: "опубликовано" },
  { label: "Расходы за месяц", caption: "выплаты + комиссия" },
] as const;

function monthTitle(): string {
  const s = new Date().toLocaleDateString("ru-RU", { month: "long", year: "numeric" }).replace(" г.", "");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export default function OrgHomePage() {
  const { current } = useOrg();

  return (
    <div>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Аналитика</h1>
          <p className="mt-1 text-sm text-muted-foreground">{monthTitle()} · обзор</p>
        </div>
        <Button asChild>
          <Link href="/org/create">
            <Plus className="size-4" />
            Создать событие
          </Link>
        </Button>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {METRICS.map((m) => (
          <Card key={m.label}>
            <CardContent className="pt-5">
              <div className="text-sm text-muted-foreground">{m.label}</div>
              <div className="mt-2 text-3xl font-bold tracking-tight text-muted-foreground/40">—</div>
              <div className="mt-2 text-xs text-muted-foreground">{m.caption}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_360px]">
        <Card>
          <CardContent className="pt-5">
            <div className="font-semibold">Заполняемость · Требования</div>
            <p className="text-sm text-muted-foreground">Заполняемость смен за неделю</p>
            <div className="mt-8 flex h-56 items-center justify-center text-center text-sm text-muted-foreground">
              Данные появятся после первых опубликованных событий
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-5">
            <div className="font-semibold">Лучшие по рейтингу</div>
            <div className="mt-8 flex h-40 items-center justify-center text-center text-sm text-muted-foreground">
              Пока нет соискателей с отзывами
            </div>
          </CardContent>
        </Card>
      </div>

      <p className="mt-6 text-xs text-muted-foreground">
        Показатели «{current?.company.name}» наполняются по мере публикации событий, откликов и выплат.
      </p>
    </div>
  );
}
