"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { BellOff, CalendarDays, Loader2 } from "lucide-react";
import {
  listNotificationsApiV1NotificationsGet,
  markReadApiV1NotificationsReadPost,
  type NotificationOut,
} from "@light-event/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

export default function NotificationsPage() {
  const router = useRouter();
  const { me, loading } = useAuth();
  const [items, setItems] = useState<NotificationOut[] | null>(null);

  useEffect(() => {
    if (!loading && !me) router.replace("/auth");
  }, [loading, me, router]);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await listNotificationsApiV1NotificationsGet();
      setItems(data?.items ?? []);
      // открытие списка помечает всё прочитанным (бейдж в шапке сбросится при следующей навигации)
      if ((data?.unread ?? 0) > 0) void markReadApiV1NotificationsReadPost();
    })();
  }, [me]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <h1 className="text-xl font-bold">Уведомления</h1>
        <div className="mt-5 space-y-2">
          {items === null ? (
            <div className="mt-16 flex justify-center text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
            </div>
          ) : items.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <BellOff className="size-8 text-muted-foreground" />
                <p className="mt-3 text-sm text-muted-foreground">
                  Уведомлений нет. Добавьте компании в избранное — и новые смены будут приходить сюда.
                </p>
              </CardContent>
            </Card>
          ) : (
            items.map((n) => {
              const href = n.vacancy_uuid ? `/shift/${n.vacancy_uuid}` : `/company/${n.company_uuid}`;
              return (
                <Link key={n.notification_uuid} href={href}>
                  <Card className={cn("transition-colors hover:bg-secondary", !n.read_at && "border-brand-border")}>
                    <CardContent className="flex items-center gap-3 py-4">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand-strong">
                        <CalendarDays className="size-4" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate font-medium">{n.title}</div>
                        <div className="text-xs text-muted-foreground">{formatDateTime(n.created_at)}</div>
                      </div>
                      {!n.read_at && <span className="size-2 shrink-0 rounded-full bg-brand" />}
                    </CardContent>
                  </Card>
                </Link>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}
