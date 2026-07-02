"use client";

import Link from "next/link";
import { Users, Wallet } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { useOrg } from "@/lib/org-context";

/** Дашборд появится вместе с vacancy-модулем; пока — входы в готовые разделы. */
export default function OrgHomePage() {
  const { current } = useOrg();

  return (
    <div>
      <h1 className="text-xl font-semibold">{current?.company.name}</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Аналитика откроется после первых событий. Сейчас доступны команда и баланс.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Link href="/org/team">
          <Card className="transition-colors hover:bg-secondary">
            <CardContent className="flex items-center gap-3 pt-6">
              <div className="flex size-10 items-center justify-center rounded-xl bg-brand-soft text-brand-strong">
                <Users className="size-5" />
              </div>
              <div>
                <div className="font-semibold">Команда и роли</div>
                <div className="text-sm text-muted-foreground">
                  Права доступа и пригласительные ссылки
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link href="/org/balance">
          <Card className="transition-colors hover:bg-secondary">
            <CardContent className="flex items-center gap-3 pt-6">
              <div className="flex size-10 items-center justify-center rounded-xl bg-brand-soft text-brand-strong">
                <Wallet className="size-5" />
              </div>
              <div>
                <div className="font-semibold">Баланс и счёт</div>
                <div className="text-sm text-muted-foreground">
                  Пополнение и операции по счёту
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
