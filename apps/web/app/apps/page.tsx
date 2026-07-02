"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Inbox, Loader2 } from "lucide-react";
import {
  myApplicationsApiV1ApplicationsMyGet,
  type MyApplicationOut,
} from "@light-event/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";
import { formatShiftWindow, kopToRub } from "@/lib/format";
import { cn } from "@/lib/utils";

export const APP_STATUS: Record<string, { label: string; className: string }> = {
  review: { label: DICT.stReview, className: "border-status-warn-border bg-status-warn-bg text-status-warn" },
  confirmed: { label: DICT.confirmedApp, className: "border-brand-border bg-brand-soft text-brand-strong" },
  reserve: { label: DICT.inReserve, className: "border-status-info-border bg-status-info-bg text-status-info" },
  paid: { label: DICT.stPaid, className: "border-status-info-border bg-status-info-bg text-status-info" },
  done: { label: DICT.stDone, className: "border-border bg-secondary text-muted-foreground" },
};

export default function MyApplicationsPage() {
  const router = useRouter();
  const { me, loading } = useAuth();
  const [apps, setApps] = useState<MyApplicationOut[] | null>(null);

  useEffect(() => {
    if (!loading && !me) router.replace("/auth");
  }, [loading, me, router]);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await myApplicationsApiV1ApplicationsMyGet();
      setApps(data ?? []);
    })();
  }, [me]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <h1 className="text-xl font-semibold">{DICT.myApps}</h1>

        {apps === null ? (
          <div className="mt-16 flex justify-center text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
          </div>
        ) : apps.length === 0 ? (
          <div className="mt-16 flex flex-col items-center text-center text-muted-foreground">
            <Inbox className="size-8" />
            <p className="mt-3 text-sm">{DICT.noApps}</p>
            <Link href="/feed" className="mt-2 text-sm underline">
              {DICT.feedTitle}
            </Link>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {apps.map((app) => {
              const status = APP_STATUS[app.status] ?? { label: app.status, className: "" };
              return (
                <Link key={app.application_uuid} href={`/apps/${app.application_uuid}`}>
                  <Card className="transition-colors hover:bg-secondary/50">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="font-semibold">{app.vacancy.role_name}</div>
                          <div className="mt-0.5 truncate text-sm text-muted-foreground">
                            {app.company_name} · {app.vacancy.event_title}
                          </div>
                          <div className="mt-1 text-sm text-muted-foreground">
                            {formatShiftWindow(app.vacancy.starts_at, app.vacancy.ends_at)}
                          </div>
                        </div>
                        <div className="flex shrink-0 flex-col items-end gap-2">
                          <span className={cn("status-badge", status.className)}>{status.label}</span>
                          <span className="font-mono text-sm font-semibold">
                            {kopToRub(app.vacancy.pay_total_kop)}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
