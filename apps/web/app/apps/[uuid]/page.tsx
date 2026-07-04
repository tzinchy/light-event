"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Check, Loader2, Star } from "lucide-react";
import {
  applicationDetailApiV1ApplicationsApplicationUuidGet,
  createComplaintApiV1ComplaintsPost,
  createReviewApiV1ReviewsPost,
  myApplicationsApiV1ApplicationsMyGet,
  type ApplicationDetailOut,
  type MyApplicationOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { SiteHeader } from "@/components/site-header";
import { APP_STATUS } from "@/app/apps/page";
import { DICT } from "@/lib/dict";
import { formatDateTime, formatShiftWindow, kopToRub } from "@/lib/format";
import { canReview, reviewReady } from "@/lib/review";
import { cn } from "@/lib/utils";

// 4 шага таймлайна референса: Отклик → Подтверждение → Смена → Выплата
const TIMELINE_STEPS = [
  { kind: "applied", label: DICT.tlApplied },
  { kind: "confirmed", label: DICT.tlConfirmed },
  { kind: "shift", label: DICT.tlShift },
  { kind: "payout", label: DICT.tlPayout },
] as const;

const COMPLAINT_KINDS = ["Задержка оплаты", "Условия не совпали с описанием", "Другое"] as const;

function ComplaintDialog({
  companyUuid,
  vacancyUuid,
}: {
  companyUuid: string;
  vacancyUuid: string;
}) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<string>(COMPLAINT_KINDS[0]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    const { error } = await createComplaintApiV1ComplaintsPost({
      body: {
        target_type: "company",
        target_uuid: companyUuid,
        vacancy_uuid: vacancyUuid,
        kind,
        severity: kind === "Задержка оплаты" ? "high" : "medium",
        text: text.trim(),
      },
    });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось отправить жалобу"));
      return;
    }
    toast.success("Жалоба отправлена администратору");
    setOpen(false);
    setText("");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button className="mt-3 text-sm text-muted-foreground underline hover:text-foreground">
          Пожаловаться на организацию
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Жалоба администратору</DialogTitle>
        </DialogHeader>
        <div className="flex flex-wrap gap-1.5">
          {COMPLAINT_KINDS.map((value) => (
            <button
              key={value}
              type="button"
              className={cn(
                "rounded-full border px-3 py-1 text-sm font-medium",
                kind === value
                  ? "border-primary bg-primary text-primary-foreground"
                  : "hover:bg-secondary",
              )}
              onClick={() => setKind(value)}
            >
              {value}
            </button>
          ))}
        </div>
        <textarea
          className="min-h-24 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
          placeholder="Опишите, что произошло"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <Button disabled={text.trim().length < 3 || busy} onClick={() => void submit()}>
          {busy && <Loader2 className="size-4 animate-spin" />}
          Отправить жалобу
        </Button>
      </DialogContent>
    </Dialog>
  );
}

function ReviewCard({ applicationUuid }: { applicationUuid: string }) {
  const [rating, setRating] = useState(0);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit() {
    setBusy(true);
    const { error } = await createReviewApiV1ReviewsPost({
      body: {
        application_uuid: applicationUuid,
        rating,
        text: text.trim() || null,
        kind: "about_org",
      },
    });
    setBusy(false);
    if (error) {
      const detail = String((error as { detail?: string }).detail ?? "");
      if (detail.includes("уже оставлен")) setSent(true);
      toast.error(detail || "Не удалось отправить отзыв");
      return;
    }
    setSent(true);
    toast.success("Спасибо! Отзыв отправлен");
  }

  if (sent) {
    return (
      <Card className="mt-4">
        <CardContent className="flex items-center gap-2 pt-6 text-sm text-brand-strong">
          <Check className="size-4" />
          Отзыв по этой смене отправлен
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle className="text-base">Оставить отзыв об организации</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex gap-1" role="radiogroup" aria-label="Оценка">
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={rating === value}
              aria-label={`Оценка ${value}`}
              className="p-1"
              onClick={() => setRating(value)}
            >
              <Star
                className={cn(
                  "size-6",
                  value <= rating ? "fill-amber-400 text-amber-400" : "text-muted-foreground/40",
                )}
              />
            </button>
          ))}
        </div>
        <textarea
          className="mt-3 min-h-20 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
          placeholder="Как прошла смена? Что понравилось, что улучшить"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <Button
          className="mt-3"
          disabled={!reviewReady(rating) || busy}
          onClick={() => void submit()}
        >
          {busy && <Loader2 className="size-4 animate-spin" />}
          Отправить отзыв
        </Button>
      </CardContent>
    </Card>
  );
}

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

        {canReview(detail.status) && <ReviewCard applicationUuid={detail.application_uuid} />}

        {summary && (
          <ComplaintDialog
            companyUuid={summary.vacancy.company_uuid}
            vacancyUuid={summary.vacancy_uuid}
          />
        )}
      </main>
    </div>
  );
}
