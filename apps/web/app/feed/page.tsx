"use client";

import { useEffect, useState } from "react";
import { Inbox, Loader2 } from "lucide-react";
import { feedApiV1VacanciesGet, type FeedItemOut } from "@light-event/shared-types";
import { Badge } from "@/components/ui/badge";
import { ShiftCard } from "@/components/shift-card";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";
import { cn } from "@/lib/utils";

// каталог ролей платформы (совпадает с desired_role_catalog backend-конфига)
const ROLES = ["Официант", "Бариста", "Хостес", "Бармен", "Повар", "Ресепшн", "Гардероб", "Промоутер"];

export default function FeedPage() {
  const [shifts, setShifts] = useState<FeedItemOut[] | null>(null);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const { data } = await feedApiV1VacanciesGet({
        query: role ? { role } : undefined,
      });
      setShifts(data ?? []);
    })();
  }, [role]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <div className="flex items-baseline justify-between">
          <h1 className="text-xl font-semibold">{DICT.feedTitle}</h1>
          {shifts && shifts.length > 0 && (
            <Badge variant="outline" className="border-brand-border bg-brand-soft text-brand-strong">
              {shifts.length} {DICT.openShifts}
            </Badge>
          )}
        </div>

        <div className="mt-4 flex gap-1.5 overflow-x-auto pb-1">
          <button
            className={cn(
              "shrink-0 rounded-full border px-3 py-1 text-sm font-medium",
              role === null ? "border-primary bg-primary text-primary-foreground" : "hover:bg-secondary",
            )}
            onClick={() => setRole(null)}
          >
            {DICT.filterAll}
          </button>
          {ROLES.map((r) => (
            <button
              key={r}
              className={cn(
                "shrink-0 rounded-full border px-3 py-1 text-sm font-medium",
                role === r ? "border-primary bg-primary text-primary-foreground" : "hover:bg-secondary",
              )}
              onClick={() => setRole(r)}
            >
              {r}
            </button>
          ))}
        </div>

        {shifts === null ? (
          <div className="mt-16 flex justify-center text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
          </div>
        ) : shifts.length === 0 ? (
          <div className="mt-16 flex flex-col items-center text-center text-muted-foreground">
            <Inbox className="size-8" />
            <p className="mt-3 text-sm">{DICT.feedEmpty}</p>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {shifts.map((shift) => (
              <ShiftCard key={shift.vacancy_uuid} shift={shift} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
