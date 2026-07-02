"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle2, Loader2, Lock, MapPin, Zap } from "lucide-react";
import {
  applyApiV1VacanciesVacancyUuidApplicationsPost,
  myApplicationsApiV1ApplicationsMyGet,
  vacancyDetailApiV1VacanciesVacancyUuidGet,
  type VacancyOut,
} from "@light-event/shared-types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";
import { formatShiftWindow, kopToRub } from "@/lib/format";

export default function ShiftPage() {
  const { uuid } = useParams<{ uuid: string }>();
  const { me, loading } = useAuth();
  const [shift, setShift] = useState<VacancyOut | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [myStatus, setMyStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      const { data, error } = await vacancyDetailApiV1VacanciesVacancyUuidGet({
        path: { vacancy_uuid: uuid },
      });
      if (error || !data) setNotFound(true);
      else setShift(data);
    })();
  }, [uuid]);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await myApplicationsApiV1ApplicationsMyGet();
      const mine = (data ?? []).find((a) => a.vacancy_uuid === uuid);
      setMyStatus(mine?.status ?? null);
    })();
  }, [me, uuid]);

  async function apply() {
    setBusy(true);
    const { data, error } = await applyApiV1VacanciesVacancyUuidApplicationsPost({
      path: { vacancy_uuid: uuid },
    });
    setBusy(false);
    if (error || !data) {
      toast.error(String((error as { detail?: string })?.detail ?? "Не удалось откликнуться"));
      return;
    }
    setMyStatus(data.status);
    toast.success(DICT.applied);
  }

  if (notFound) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <div className="mx-auto mt-24 text-muted-foreground">Смена не найдена</div>
      </div>
    );
  }

  if (!shift || loading) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <div className="mx-auto mt-24 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <Link
          href="/feed"
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          {DICT.backFeed}
        </Link>

        <div className="mt-4 flex items-start justify-between gap-3">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-semibold">{shift.role_name}</h1>
              {shift.urgent && (
                <span className="status-badge border-status-danger-border bg-status-danger-bg text-status-danger">
                  <Zap className="size-3" />
                  {DICT.urgent}
                </span>
              )}
            </div>
            <p className="mt-1 text-muted-foreground">{shift.event_title}</p>
          </div>
          <div className="shrink-0 text-right">
            <div className="font-mono text-lg font-semibold">
              {kopToRub(shift.pay_hour_kop)}
              <span className="text-xs font-normal text-muted-foreground">{DICT.perHour}</span>
            </div>
            <div className="text-sm text-muted-foreground">
              {kopToRub(shift.pay_total_kop)} {DICT.total}
            </div>
          </div>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base">{DICT.aboutEvent}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div>{formatShiftWindow(shift.starts_at, shift.ends_at)}</div>
            <div className="text-muted-foreground">
              Мест: {shift.slots}
            </div>
            {shift.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {shift.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="font-normal">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {shift.requirements.length > 0 && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="text-base">{DICT.requirements}</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {shift.requirements.map((req) => (
                  <li key={req}>{req}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        <Card className="mt-4">
          <CardHeader>
            <CardTitle className="text-base">{DICT.contacts}</CardTitle>
          </CardHeader>
          <CardContent>
            {me ? (
              <div className="flex items-center gap-2 text-sm">
                <MapPin className="size-4 text-muted-foreground" />
                {shift.venue_address}
              </div>
            ) : (
              <div className="flex flex-col items-start gap-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Lock className="size-4" />
                  {DICT.contactsLocked}
                </div>
                <Button asChild size="sm">
                  <Link href="/auth">{DICT.loginOrSignup}</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {me &&
          (myStatus ? (
            <div className="mt-6 flex items-center justify-center gap-2 rounded-xl border border-brand-border bg-brand-soft py-3 text-sm font-medium text-brand-strong">
              <CheckCircle2 className="size-4" />
              {myStatus === "reserve"
                ? DICT.inReserve
                : myStatus === "confirmed"
                  ? DICT.confirmedApp
                  : DICT.applied}
            </div>
          ) : (
            <Button
              className="mt-6 w-full"
              disabled={busy || shift.status !== "active"}
              onClick={() => void apply()}
            >
              {busy && <Loader2 className="size-4 animate-spin" />}
              {DICT.apply}
            </Button>
          ))}
      </main>
    </div>
  );
}
