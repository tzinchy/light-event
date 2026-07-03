"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import {
  BadgeCheck,
  Building2,
  CalendarPlus,
  ClipboardList,
  Loader2,
  MapPin,
  Phone,
  Wallet,
  XCircle,
} from "lucide-react";
import {
  adminListTopupRequestsApiV1AdminTopupRequestsGet,
  adminResolveTopupApiV1AdminTopupRequestsTopupRequestUuidResolvePost,
  listCompaniesApiV1AdminCompaniesGet,
  listRequestsApiV1AdminRequestsGet,
  moderateTestApiV1AdminTestsTestUuidModeratePost,
  moderateVacancyApiV1AdminVacanciesVacancyUuidModeratePost,
  rejectCompanyApiV1AdminCompaniesCompanyUuidRejectPost,
  verifyCompanyApiV1AdminCompaniesCompanyUuidVerifyPost,
  type CompanyModerationOut,
  type ModerationRequestOut,
  type TopupRequestOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime, kopToRub } from "@/lib/format";
import { cn } from "@/lib/utils";

function detailText(error: unknown, fallback: string): string {
  return String((error as { detail?: string })?.detail ?? fallback);
}

function ApplicationCard({
  company,
  onDone,
}: {
  company: CompanyModerationOut;
  onDone: () => void;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<"verify" | "reject" | null>(null);

  async function verify() {
    setBusy("verify");
    const { error } = await verifyCompanyApiV1AdminCompaniesCompanyUuidVerifyPost({
      path: { company_uuid: company.company_uuid },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось подтвердить"));
      return;
    }
    toast.success(`«${company.name}» подтверждена`);
    onDone();
  }

  async function reject() {
    setBusy("reject");
    const { error } = await rejectCompanyApiV1AdminCompaniesCompanyUuidRejectPost({
      path: { company_uuid: company.company_uuid },
      body: { reason: reason.trim() },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось отклонить"));
      return;
    }
    toast.success(`«${company.name}» отклонена`);
    onDone();
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              <Building2 className="size-4 text-muted-foreground" />
              {company.name}
            </h3>
            {company.description && (
              <p className="mt-1 text-sm text-muted-foreground">{company.description}</p>
            )}
          </div>
          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
            На проверке
          </span>
        </div>

        <dl className="mt-3 grid gap-x-6 gap-y-1.5 text-sm sm:grid-cols-2">
          <div className="flex justify-between gap-2 sm:justify-start">
            <dt className="text-muted-foreground">ИНН</dt>
            <dd className="font-mono">{company.inn || "—"}</dd>
          </div>
          <div className="flex justify-between gap-2 sm:justify-start">
            <dt className="text-muted-foreground">ОГРН</dt>
            <dd className="font-mono">{company.ogrn || "—"}</dd>
          </div>
          <div className="flex items-center gap-1.5 sm:col-span-2">
            <MapPin className="size-3.5 shrink-0 text-muted-foreground" />
            <span>{company.address || "адрес не указан"}</span>
            <span className="font-mono text-xs text-muted-foreground">
              ({company.lat.toFixed(4)}, {company.lon.toFixed(4)})
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Phone className="size-3.5 shrink-0 text-muted-foreground" />
            <span className="font-mono">{company.contact_phone || "—"}</span>
          </div>
        </dl>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Button size="sm" disabled={busy !== null} onClick={() => void verify()}>
            {busy === "verify" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <BadgeCheck className="size-4" />
            )}
            Подтвердить
          </Button>
          <div className="flex flex-1 gap-2">
            <Input
              className="h-8 flex-1"
              placeholder="Причина отклонения"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              size="sm"
              variant="outline"
              className="text-destructive"
              disabled={busy !== null || reason.trim().length < 3}
              onClick={() => void reject()}
            >
              {busy === "reject" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <XCircle className="size-4" />
              )}
              Отклонить
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function RequestCard({ item, onDone }: { item: ModerationRequestOut; onDone: () => void }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);
  const isVacancy = item.kind === "vacancy";

  async function moderate(action: "approve" | "reject") {
    setBusy(action);
    const body = { action, reason: action === "reject" ? reason.trim() : null };
    const { error } = isVacancy
      ? await moderateVacancyApiV1AdminVacanciesVacancyUuidModeratePost({
          path: { vacancy_uuid: item.ref_uuid },
          body,
        })
      : await moderateTestApiV1AdminTestsTestUuidModeratePost({
          path: { test_uuid: item.ref_uuid },
          body,
        });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось обработать заявку"));
      return;
    }
    toast.success(action === "approve" ? "Опубликовано" : "Отклонено");
    onDone();
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              {isVacancy ? (
                <CalendarPlus className="size-4 text-muted-foreground" />
              ) : (
                <ClipboardList className="size-4 text-muted-foreground" />
              )}
              {item.title}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {item.company_name ?? "—"} · оплачено {formatDateTime(item.submitted_at)}
            </p>
          </div>
          <span
            className={cn(
              "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
              isVacancy ? "bg-brand-soft text-brand-strong" : "bg-violet-50 text-violet-700",
            )}
          >
            {isVacancy ? "Публикация смены" : "Тест компании"}
          </span>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Button size="sm" disabled={busy !== null} onClick={() => void moderate("approve")}>
            {busy === "approve" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <BadgeCheck className="size-4" />
            )}
            Одобрить
          </Button>
          <div className="flex flex-1 gap-2">
            <Input
              className="h-8 flex-1"
              placeholder="Причина отклонения"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              size="sm"
              variant="outline"
              className="text-destructive"
              disabled={busy !== null || reason.trim().length < 3}
              onClick={() => void moderate("reject")}
            >
              {busy === "reject" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <XCircle className="size-4" />
              )}
              Отклонить
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function TopupCard({ topup, onDone }: { topup: TopupRequestOut; onDone: () => void }) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<"approve" | "reject" | null>(null);

  async function resolve(action: "approve" | "reject") {
    setBusy(action);
    const { error } = await adminResolveTopupApiV1AdminTopupRequestsTopupRequestUuidResolvePost({
      path: { topup_request_uuid: topup.topup_request_uuid },
      body: { action, reason: action === "reject" ? reason.trim() : null },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось обработать пополнение"));
      return;
    }
    toast.success(action === "approve" ? "Пополнение зачислено" : "Пополнение отклонено");
    onDone();
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              <Wallet className="size-4 text-muted-foreground" />
              <span className="font-mono">{kopToRub(topup.amount_kop)}</span>
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Заявка от {formatDateTime(topup.created_at)}
              {topup.payment_details ? ` · ${topup.payment_details}` : ""}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
            Ожидает зачисления
          </span>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Button size="sm" disabled={busy !== null} onClick={() => void resolve("approve")}>
            {busy === "approve" ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <BadgeCheck className="size-4" />
            )}
            Зачислить
          </Button>
          <div className="flex flex-1 gap-2">
            <Input
              className="h-8 flex-1"
              placeholder="Причина отклонения"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              size="sm"
              variant="outline"
              className="text-destructive"
              disabled={busy !== null || reason.trim().length < 3}
              onClick={() => void resolve("reject")}
            >
              {busy === "reject" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <XCircle className="size-4" />
              )}
              Отклонить
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyCard({ text }: { text: string }) {
  return (
    <Card>
      <CardContent className="py-10 text-center text-sm text-muted-foreground">{text}</CardContent>
    </Card>
  );
}

type TabKey = "companies" | "requests" | "topups";

export default function AdminPage() {
  const router = useRouter();
  const { me, loading: authLoading } = useAuth();
  const [tab, setTab] = useState<TabKey>("companies");
  const [companies, setCompanies] = useState<CompanyModerationOut[] | null>(null);
  const [requests, setRequests] = useState<ModerationRequestOut[] | null>(null);
  const [topups, setTopups] = useState<TopupRequestOut[] | null>(null);

  const isAdmin = me?.platform_role === "admin";

  const reload = useCallback(async () => {
    const [companiesResp, requestsResp, topupsResp] = await Promise.all([
      listCompaniesApiV1AdminCompaniesGet({ query: { status: "pending" } }),
      listRequestsApiV1AdminRequestsGet(),
      adminListTopupRequestsApiV1AdminTopupRequestsGet(),
    ]);
    setCompanies(companiesResp.data ?? []);
    setRequests(requestsResp.data ?? []);
    setTopups((topupsResp.data ?? []).filter((t) => t.status === "pending"));
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!me) {
      router.replace("/auth");
      return;
    }
    if (!isAdmin) {
      router.replace("/");
      return;
    }
    void reload();
  }, [authLoading, me, isAdmin, router, reload]);

  if (authLoading || !isAdmin || companies === null || requests === null || topups === null) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  const tabs: { key: TabKey; label: string; count: number }[] = [
    { key: "companies", label: "Организации", count: companies.length },
    { key: "requests", label: "Публикации", count: requests.length },
    { key: "topups", label: "Пополнения", count: topups.length },
  ];

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <h1 className="text-xl font-bold">Модерация</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Заявки организаций, платные публикации и пополнения счетов.
      </p>

      <div className="mt-4 flex gap-1.5 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            className={cn(
              "flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium",
              tab === t.key
                ? "border-primary bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground",
            )}
            onClick={() => setTab(t.key)}
          >
            {t.label}
            <span
              className={cn(
                "rounded-full px-1.5 text-xs",
                tab === t.key ? "bg-primary-foreground/20" : "bg-secondary",
              )}
            >
              {t.count}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-5 space-y-3">
        {tab === "companies" &&
          (companies.length === 0 ? (
            <EmptyCard text="Пока нет заявок на проверку" />
          ) : (
            companies.map((c) => (
              <ApplicationCard key={c.company_uuid} company={c} onDone={() => void reload()} />
            ))
          ))}
        {tab === "requests" &&
          (requests.length === 0 ? (
            <EmptyCard text="Очередь модерации пуста" />
          ) : (
            requests.map((r) => (
              <RequestCard key={`${r.kind}-${r.ref_uuid}`} item={r} onDone={() => void reload()} />
            ))
          ))}
        {tab === "topups" &&
          (topups.length === 0 ? (
            <EmptyCard text="Нет заявок на пополнение" />
          ) : (
            topups.map((t) => (
              <TopupCard key={t.topup_request_uuid} topup={t} onDone={() => void reload()} />
            ))
          ))}
      </div>
    </div>
  );
}
