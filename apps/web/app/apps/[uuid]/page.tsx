"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowLeft, Check, Loader2 } from "lucide-react";
import {
  applicationDetailApiV1ApplicationsApplicationUuidGet,
  myApplicationsApiV1ApplicationsMyGet,
  type ApplicationDetailOut,
  type MyApplicationOut,
} from "@light-event/shared-types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { APP_STATUS } from "@/app/apps/page";
import { DICT } from "@/lib/dict";
import { formatDateTime, formatShiftWindow, kopToRub } from "@/lib/format";
import { cn } from "@/lib/utils";

// 4 шага таймлайна референса: Отклик → Подтверждение → Смена → Выплата
const TIMELINE_STEPS = [
  { kind: "applied", label: DICT.tlApplied },
  { kind: "confirmed", label: DICT.tlConfirmed },
  { kind: "shift", label: DICT.tlShift },
  { kind: "payout", label: DICT.tlPayout },
] as const;

export default function ApplicationPage() {
  const { uuid } = useParams<{ uuid: string }>();
  const [detail, setDetail] = useState<ApplicationDetailOut | null>(null);
  const [summary, setSummary] = useState<MyApplicationOut | null>(null);

  useEffect(() => {
    void (async () => {
      const [d, my] = await Promise.all([
        applicationDetailApiV1ApplicationsApplicationUuidGet({ path: { application_uuid: uuid } }),
        myApplicationsApiV1ApplicationsMyGet(),
      ]);
      setDetail(d.data ?? null);
      setSummary((my.data ?? []).find((a) => a.application_uuid === uuid) ?? null);
    })();
  }, [uuid]);

  if (!detail) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <div className="mx-auto mt-24 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      </div>
    );
  }

  const passed = new Map(detail.timeline.map((e) => [e.kind, e.occurred_at]));
  const status = APP_STATUS[detail.status] ?? { label: detail.status, className: "" };

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <Link
          href="/apps"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          {DICT.myApps}
        </Link>

        <div className="mt-4 flex items-start justify-between gap-3">
          <h1 className="text-xl font-semibold">{DICT.appCard}</h1>
          <span className={cn("status-badge", status.className)}>{status.label}</span>
        </div>

        {summary && (
          <Card className="mt-4">
            <CardContent className="pt-6">
              <div className="font-semibold">{summary.vacancy.role_name}</div>
              <div className="mt-0.5 text-sm text-muted-foreground">
                {summary.company_name} · {summary.vacancy.event_title}
              </div>
              <div className="mt-1 flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {formatShiftWindow(summary.vacancy.starts_at, summary.vacancy.ends_at)}
                </span>
                <span className="font-mono font-semibold">
                  {kopToRub(summary.vacancy.pay_total_kop)}
                </span>
              </div>
              <Link
                href={`/shift/${summary.vacancy_uuid}`}
                className="mt-2 inline-block text-sm underline"
              >
                Открыть смену
              </Link>
            </CardContent>
          </Card>
        )}

        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-base">{DICT.timeline}</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4">
              {TIMELINE_STEPS.map((step, i) => {
                const at = passed.get(step.kind);
                return (
                  <li key={step.kind} className="flex items-start gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className={cn(
                          "flex size-6 items-center justify-center rounded-full border text-[10px] font-semibold",
                          at
                            ? "border-brand bg-brand text-white"
                            : "bg-secondary text-muted-foreground",
                        )}
                      >
                        {at ? <Check className="size-3.5" /> : i + 1}
                      </div>
                      {i < TIMELINE_STEPS.length - 1 && (
                        <div className={cn("mt-1 h-6 w-px", at ? "bg-brand" : "bg-border")} />
                      )}
                    </div>
                    <div>
                      <div className={cn("text-sm font-medium", !at && "text-muted-foreground")}>
                        {step.label}
                      </div>
                      {at && (
                        <div className="text-xs text-muted-foreground">{formatDateTime(at)}</div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
