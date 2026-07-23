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
  adminExecutePayoutApiV1AdminPayoutsPayoutUuidExecutePost,
  adminListPayoutsApiV1AdminPayoutsGet,
  adminOpenComplaintsApiV1AdminComplaintsGet,
  adminResolveComplaintApiV1AdminComplaintsComplaintUuidResolvePost,
  adminListTopupRequestsApiV1AdminTopupRequestsGet,
  adminResolveTopupApiV1AdminTopupRequestsTopupRequestUuidResolvePost,
  adminModeratedMessagesApiV1ChatAdminModeratedMessagesGet,
  type AdminMessageOut,
  companyPricesAdminApiV1AdminCompaniesCompanyUuidPricingGet,
  setCompanyPriceApiV1AdminCompaniesCompanyUuidPricingKeyPut,
  createAccountApiV1AdminPaymentAccountsPost,
  listAccountsApiV1AdminPaymentAccountsGet,
  listEmailsApiV1AdminEmailsGet,
  sendEmailApiV1AdminEmailsSendPost,
  type EmailMessageOut,
  setPriorityApiV1AdminPaymentAccountsPaymentAccountUuidPriorityPost,
  updateAccountApiV1AdminPaymentAccountsPaymentAccountUuidPatch,
  type PaymentAccountOut,
  listApplicationsApiV1AdminCompanyApplicationsGet,
  approveApplicationApiV1AdminCompanyApplicationsApplicationUuidApprovePost,
  rejectApplicationApiV1AdminCompanyApplicationsApplicationUuidRejectPost,
  type AdminApplicationOut,
  listUsersApiV1AdminUsersGet,
  createUserApiV1AdminUsersPost,
  userDetailApiV1AdminUsersUserUuidGet,
  updateUserApiV1AdminUsersUserUuidPatch,
  approveUserApiV1AdminUsersUserUuidApprovePost,
  resubmitUserApiV1AdminUsersUserUuidResubmitPost,
  banUserApiV1AdminUsersUserUuidBanPost,
  unbanUserApiV1AdminUsersUserUuidUnbanPost,
  type AdminUserOut,
  type AdminUserDetailOut,
  type ModerationStatus,
  listCompaniesApiV1AdminCompaniesGet,
  listPricesApiV1AdminPricingGet,
  listRequestsApiV1AdminRequestsGet,
  overviewApiV1AdminOverviewGet,
  moderateTestApiV1AdminTestsTestUuidModeratePost,
  moderateVacancyApiV1AdminVacanciesVacancyUuidModeratePost,
  rejectCompanyApiV1AdminCompaniesCompanyUuidRejectPost,
  setPriceApiV1AdminPricingKeyPut,
  verifyCompanyApiV1AdminCompaniesCompanyUuidVerifyPost,
  type CompanyModerationOut,
  type ComplaintOut,
  type OverviewOut,
  type ModerationRequestOut,
  type PayoutOut,
  type PriceOut,
  type TopupRequestOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getTokens } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDateTime, kopToRub, rubInputToKop } from "@/lib/format";
import { Banknote, LogOut, MessageSquareWarning } from "lucide-react";
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
          <div className="sm:col-span-2">
            <dt className="text-muted-foreground">Заявитель</dt>
            <dd>
              {company.contact_name} · {company.contact_position} · {company.contact_email}
            </dd>
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

  async function viewProof() {
    const tokens = getTokens();
    const resp = await fetch(`/api/v1/documents/${topup.proof_document_uuid}/content`, {
      headers: tokens ? { Authorization: `Bearer ${tokens.access}` } : undefined,
    });
    if (!resp.ok) {
      toast.error("Не удалось открыть подтверждение оплаты");
      return;
    }
    window.open(URL.createObjectURL(await resp.blob()), "_blank");
  }

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
          <button
            className="shrink-0 rounded-lg border px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
            onClick={() => void viewProof()}
          >
            Посмотреть чек
          </button>
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

function PayoutCard({ payout, onDone }: { payout: PayoutOut; onDone: () => void }) {
  const [busy, setBusy] = useState(false);

  async function execute() {
    setBusy(true);
    const { error } = await adminExecutePayoutApiV1AdminPayoutsPayoutUuidExecutePost({
      path: { payout_uuid: payout.payout_uuid },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось провести выплату"));
      return;
    }
    toast.success("Выплата проведена");
    onDone();
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              <Banknote className="size-4 text-muted-foreground" />
              {payout.event_title}
            </h3>
            <p className="mt-1 text-sm text-muted-foreground">
              {payout.company_name} · {payout.workers_count} чел. · подана{" "}
              {formatDateTime(payout.created_at)}
            </p>
          </div>
          <span className="shrink-0 font-mono text-lg font-semibold">
            {kopToRub(payout.amount_kop)}
          </span>
        </div>

        <div className="mt-4">
          <Button size="sm" disabled={busy} onClick={() => void execute()}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : <BadgeCheck className="size-4" />}
            Провести выплату
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

const SEVERITY: Record<string, { label: string; className: string }> = {
  low: { label: "Низкая", className: "bg-secondary text-muted-foreground" },
  medium: { label: "Средняя", className: "bg-amber-50 text-amber-700" },
  high: { label: "Высокая", className: "bg-red-50 text-red-700" },
};

function ComplaintCard({ complaint, onDone }: { complaint: ComplaintOut; onDone: () => void }) {
  const [resolution, setResolution] = useState("");
  const [busy, setBusy] = useState<"resolved" | "dismissed" | null>(null);
  const severity = SEVERITY[complaint.severity] ?? SEVERITY.medium;

  async function resolve(action: "resolved" | "dismissed") {
    setBusy(action);
    const { error } = await adminResolveComplaintApiV1AdminComplaintsComplaintUuidResolvePost({
      path: { complaint_uuid: complaint.complaint_uuid },
      body: { action, resolution: resolution.trim() },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось обработать жалобу"));
      return;
    }
    toast.success(action === "resolved" ? "Жалоба решена" : "Жалоба отклонена");
    onDone();
  }

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              <MessageSquareWarning className="size-4 text-muted-foreground" />
              {complaint.kind}
            </h3>
            <p className="mt-1 text-sm">{complaint.text}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Подана {formatDateTime(complaint.created_at)}
            </p>
          </div>
          <span
            className={cn(
              "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
              severity.className,
            )}
          >
            {severity.label}
          </span>
        </div>

        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <Input
            className="h-8 flex-1"
            placeholder="Резолюция (обязательна)"
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={busy !== null || resolution.trim().length < 3}
              onClick={() => void resolve("resolved")}
            >
              {busy === "resolved" ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <BadgeCheck className="size-4" />
              )}
              Решена
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-destructive"
              disabled={busy !== null || resolution.trim().length < 3}
              onClick={() => void resolve("dismissed")}
            >
              {busy === "dismissed" ? (
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

function PriceRow({ price, onSaved }: { price: PriceOut; onSaved: () => void }) {
  const [rub, setRub] = useState(String(Math.round(price.amount_kop / 100)));
  const [busy, setBusy] = useState(false);
  const kop = rubInputToKop(rub);
  const dirty = kop !== null && kop !== price.amount_kop;

  async function save() {
    if (kop === null) return;
    setBusy(true);
    const { error } = await setPriceApiV1AdminPricingKeyPut({
      path: { key: price.key },
      body: { amount_kop: kop },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось сохранить цену"));
      return;
    }
    toast.success(`Тариф «${price.label}» обновлён`);
    onSaved();
  }

  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <div className="min-w-0 flex-1">
          <div className="font-medium">{price.label}</div>
          <div className="text-xs text-muted-foreground">Текущая цена: {kopToRub(price.amount_kop)}</div>
        </div>
        <div className="relative">
          <Input
            className="w-32 pr-6 text-right font-mono"
            inputMode="numeric"
            value={rub}
            onChange={(e) => setRub(e.target.value.replace(/[^\d]/g, ""))}
          />
          <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
            ₽
          </span>
        </div>
        <Button size="sm" disabled={!dirty || busy} onClick={() => void save()}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : "Сохранить"}
        </Button>
      </CardContent>
    </Card>
  );
}

function CompanyPriceRow({
  companyUuid,
  price,
  onSaved,
}: {
  companyUuid: string;
  price: PriceOut;
  onSaved: () => void;
}) {
  const [rub, setRub] = useState(String(Math.round(price.amount_kop / 100)));
  const [busy, setBusy] = useState(false);
  const kop = rubInputToKop(rub);
  const dirty = kop !== null && kop !== price.amount_kop;

  async function save() {
    if (kop === null) return;
    setBusy(true);
    const { error } = await setCompanyPriceApiV1AdminCompaniesCompanyUuidPricingKeyPut({
      path: { company_uuid: companyUuid, key: price.key },
      body: { amount_kop: kop },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось сохранить цену"));
      return;
    }
    toast.success(`Тариф «${price.label}» для компании обновлён`);
    onSaved();
  }

  return (
    <div className="flex items-center gap-3 border-b py-3 last:border-b-0">
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">{price.label}</div>
        <div className="text-xs text-muted-foreground">
          {price.company_override ? "Свой тариф компании" : "Общий тариф"} · {kopToRub(price.amount_kop)}
        </div>
      </div>
      <div className="relative">
        <Input
          className="w-32 pr-6 text-right font-mono"
          inputMode="numeric"
          value={rub}
          onChange={(e) => setRub(e.target.value.replace(/[^\d]/g, ""))}
        />
        <span className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
          ₽
        </span>
      </div>
      <Button size="sm" disabled={!dirty || busy} onClick={() => void save()}>
        {busy ? <Loader2 className="size-4 animate-spin" /> : "Сохранить"}
      </Button>
    </div>
  );
}

function CompanyPricingPanel() {
  const [companies, setCompanies] = useState<CompanyModerationOut[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [prices, setPrices] = useState<PriceOut[] | null>(null);

  useEffect(() => {
    void (async () => {
      const { data } = await listCompaniesApiV1AdminCompaniesGet({ query: { status: "verified" } });
      setCompanies(data ?? []);
    })();
  }, []);

  const loadPrices = useCallback(async () => {
    if (!selected) {
      setPrices(null);
      return;
    }
    const { data } = await companyPricesAdminApiV1AdminCompaniesCompanyUuidPricingGet({
      path: { company_uuid: selected },
    });
    setPrices(data ?? []);
  }, [selected]);

  useEffect(() => {
    void loadPrices();
  }, [loadPrices]);

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="font-semibold">Тарифы конкретной компании</div>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Свой тариф компании имеет приоритет над общим.
        </p>
        <select
          className="mt-3 h-9 w-full rounded-lg border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Выберите компанию…</option>
          {companies.map((c) => (
            <option key={c.company_uuid} value={c.company_uuid}>
              {c.name}
            </option>
          ))}
        </select>
        {selected && prices && (
          <div className="mt-2">
            {prices.map((p) => (
              <CompanyPriceRow key={p.key} companyUuid={selected} price={p} onSaved={() => void loadPrices()} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ModeratedChatsPanel() {
  const [items, setItems] = useState<AdminMessageOut[] | null>(null);

  useEffect(() => {
    void (async () => {
      const { data } = await adminModeratedMessagesApiV1ChatAdminModeratedMessagesGet();
      setItems(data ?? []);
    })();
  }, []);

  if (items === null) {
    return (
      <div className="flex justify-center py-10 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }
  if (items.length === 0) {
    return <EmptyCard text="Отредактированных или удалённых сообщений нет" />;
  }
  return (
    <div className="space-y-3">
      {items.map((m) => (
        <Card key={m.chat_message_uuid}>
          <CardContent className="pt-5">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{m.event_title}</span>
              <span>отправлено {formatDateTime(m.sent_at)}</span>
              {m.edited_at && <span className="text-amber-700">изменено {formatDateTime(m.edited_at)}</span>}
              {m.deleted_at && (
                <span className="text-status-danger">удалено {formatDateTime(m.deleted_at)}</span>
              )}
            </div>
            <p className={cn("mt-2 text-sm", m.deleted_at && "line-through opacity-70")}>{m.text}</p>
            {m.revisions.length > 0 && (
              <div className="mt-2 rounded-lg border bg-secondary/30 p-2.5">
                <div className="text-xs font-medium text-muted-foreground">Прежние версии</div>
                <ol className="mt-1 space-y-1">
                  {m.revisions.map((r, i) => (
                    <li key={i} className="text-sm">
                      <span className="text-xs text-muted-foreground">{formatDateTime(r.replaced_at)} · </span>
                      {r.text}
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function PaymentAccountsPanel() {
  const [accounts, setAccounts] = useState<PaymentAccountOut[] | null>(null);
  const [name, setName] = useState("");
  const [requisites, setRequisites] = useState("");
  const [limitRub, setLimitRub] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    const { data } = await listAccountsApiV1AdminPaymentAccountsGet();
    setAccounts(data ?? []);
  }, []);
  useEffect(() => {
    void reload();
  }, [reload]);

  async function create() {
    const kop = rubInputToKop(limitRub);
    if (name.trim().length < 2 || requisites.trim().length < 2 || !kop) return;
    setBusy(true);
    const { error } = await createAccountApiV1AdminPaymentAccountsPost({
      body: {
        name: name.trim(),
        requisites: requisites.trim(),
        monthly_limit_kop: kop,
        is_priority: (accounts ?? []).length === 0, // первый счёт сразу приоритетный
      },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось создать счёт"));
      return;
    }
    setName("");
    setRequisites("");
    setLimitRub("");
    void reload();
  }

  async function makePriority(uuid: string) {
    await setPriorityApiV1AdminPaymentAccountsPaymentAccountUuidPriorityPost({
      path: { payment_account_uuid: uuid },
    });
    void reload();
  }

  async function toggleActive(acc: PaymentAccountOut) {
    await updateAccountApiV1AdminPaymentAccountsPaymentAccountUuidPatch({
      path: { payment_account_uuid: acc.payment_account_uuid },
      body: { active: !acc.active },
    });
    void reload();
  }

  if (accounts === null) {
    return (
      <div className="flex justify-center py-10 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-3 pt-5">
          <div className="font-semibold">Новый счёт для приёма пополнений</div>
          <Input placeholder="Название (напр. «Карта Сбер»)" value={name} onChange={(e) => setName(e.target.value)} />
          <textarea
            className="min-h-16 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
            placeholder="Реквизиты: банк, номер карты/счёта, получатель"
            value={requisites}
            onChange={(e) => setRequisites(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Input
              className="w-48"
              inputMode="numeric"
              placeholder="Лимит в месяц, ₽"
              value={limitRub}
              onChange={(e) => setLimitRub(e.target.value.replace(/[^\d]/g, ""))}
            />
            <Button size="sm" disabled={busy} onClick={() => void create()}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : "Добавить счёт"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {accounts.length === 0 ? (
        <EmptyCard text="Счетов пока нет — добавьте хотя бы один для приёма пополнений" />
      ) : (
        accounts.map((acc) => {
          const received = acc.received_this_month_kop ?? 0;
          const pct = Math.min(100, Math.round((received / acc.monthly_limit_kop) * 100));
          return (
            <Card key={acc.payment_account_uuid} className={cn(!acc.active && "opacity-60")}>
              <CardContent className="pt-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{acc.name}</span>
                      {acc.is_priority && (
                        <span className="rounded-full bg-brand-soft px-2 py-0.5 text-xs font-medium text-brand-strong">
                          Приоритетный
                        </span>
                      )}
                      {!acc.active && <span className="text-xs text-muted-foreground">выключен</span>}
                    </div>
                    <div className="mt-0.5 whitespace-pre-line text-sm text-muted-foreground">{acc.requisites}</div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {!acc.is_priority && acc.active && (
                      <Button variant="outline" size="sm" onClick={() => void makePriority(acc.payment_account_uuid)}>
                        Сделать основным
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => void toggleActive(acc)}>
                      {acc.active ? "Выключить" : "Включить"}
                    </Button>
                  </div>
                </div>
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Принято за месяц</span>
                    <span className="font-mono">
                      {kopToRub(received)} / {kopToRub(acc.monthly_limit_kop)}
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-secondary">
                    <div className={cn("h-full", pct >= 100 ? "bg-status-danger" : "bg-brand")} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })
      )}
    </div>
  );
}

function EmailsPanel() {
  const [letters, setLetters] = useState<EmailMessageOut[] | null>(null);
  const [toEmail, setToEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    const { data } = await listEmailsApiV1AdminEmailsGet({ query: { limit: 100 } });
    setLetters(data ?? []);
  }, []);
  useEffect(() => {
    void reload();
  }, [reload]);

  async function send() {
    if (!toEmail.includes("@") || !subject.trim() || !body.trim()) return;
    setBusy(true);
    const { error } = await sendEmailApiV1AdminEmailsSendPost({
      body: { to_email: toEmail.trim(), subject: subject.trim(), body: body.trim() },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось отправить письмо"));
      void reload(); // неудачная попытка тоже попадает в журнал
      return;
    }
    toast.success("Письмо отправлено");
    setToEmail("");
    setSubject("");
    setBody("");
    void reload();
  }

  if (letters === null) {
    return (
      <div className="flex justify-center py-10 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-3 pt-5">
          <div className="font-semibold">Отправить письмо</div>
          <Input
            type="email"
            placeholder="Кому (email)"
            value={toEmail}
            onChange={(e) => setToEmail(e.target.value)}
          />
          <Input placeholder="Тема" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <textarea
            className="min-h-24 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
            placeholder="Текст письма"
            value={body}
            onChange={(e) => setBody(e.target.value)}
          />
          <Button size="sm" disabled={busy} onClick={() => void send()}>
            {busy ? <Loader2 className="size-4 animate-spin" /> : "Отправить"}
          </Button>
        </CardContent>
      </Card>

      {letters.length === 0 ? (
        <EmptyCard text="Писем пока нет — здесь появится каждый отправленный код и письмо" />
      ) : (
        letters.map((m) => (
          <Card key={m.email_message_uuid}>
            <CardContent className="pt-5">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 font-medium",
                    m.status === "sent"
                      ? "bg-brand-soft text-brand-strong"
                      : "bg-status-danger/10 text-status-danger",
                  )}
                >
                  {m.status === "sent" ? "Отправлено" : "Ошибка"}
                </span>
                <span className="rounded-full bg-secondary px-2 py-0.5">
                  {m.kind === "otp" ? "Код входа" : "От админа"}
                </span>
                <span className="font-mono">{m.to_email}</span>
                <span>· {formatDateTime(m.created_at)}</span>
              </div>
              <div className="mt-2 text-sm font-medium">{m.subject}</div>
              <p className="mt-1 whitespace-pre-line text-sm text-muted-foreground">{m.body}</p>
              {m.error && <p className="mt-1 text-xs text-status-danger">{m.error}</p>}
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

const MOD_STATUS: Record<string, { label: string; cls: string }> = {
  pending: { label: "На проверке", cls: "bg-status-warn-bg text-status-warn" },
  approved: { label: "Подтверждён", cls: "bg-brand-soft text-brand-strong" },
  resubmit: { label: "Дослать документ", cls: "bg-status-info-bg text-status-info" },
  banned: { label: "Заблокирован", cls: "bg-status-danger/10 text-status-danger" },
};
const MOD_FILTERS: { key: string; label: string }[] = [
  { key: "", label: "Все" },
  { key: "pending", label: "На проверке" },
  { key: "approved", label: "Подтверждены" },
  { key: "resubmit", label: "На дослать" },
  { key: "banned", label: "Заблокированы" },
];
const ROLE_LABEL: Record<string, string> = { user: "Пользователь", vip_user: "VIP", admin: "Администратор" };
const ROLE_OPTIONS = ["user", "vip_user", "admin"];

function ModBadge({ status }: { status: string }) {
  const s = MOD_STATUS[status] ?? { label: status, cls: "bg-secondary text-muted-foreground" };
  return <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", s.cls)}>{s.label}</span>;
}

async function viewDocument(documentUuid: string) {
  const tokens = getTokens();
  const resp = await fetch(`/api/v1/documents/${documentUuid}/content`, {
    headers: tokens ? { Authorization: `Bearer ${tokens.access}` } : undefined,
  });
  if (!resp.ok) {
    toast.error("Не удалось открыть документ");
    return;
  }
  window.open(URL.createObjectURL(await resp.blob()), "_blank");
}

function UserDetailView({
  user,
  meUuid,
  onBack,
  onChanged,
}: {
  user: AdminUserDetailOut;
  meUuid: string;
  onBack: () => void;
  onChanged: () => void;
}) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const isSelf = user.user_uuid === meUuid;

  async function run(label: string, fn: () => Promise<{ error?: unknown }>, ok: string, needReason = false) {
    if (needReason && reason.trim().length < 3) {
      toast.error("Укажите причину (минимум 3 символа)");
      return;
    }
    setBusy(label);
    const { error } = await fn();
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось выполнить действие"));
      return;
    }
    toast.success(ok);
    setReason("");
    onChanged();
  }

  return (
    <div className="space-y-4">
      <button className="text-sm text-muted-foreground hover:text-foreground" onClick={onBack}>
        ← К списку
      </button>

      <Card>
        <CardContent className="space-y-3 pt-5">
          <div className="flex items-center justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate font-semibold">{user.name ?? user.email ?? "Без имени"}</div>
              <div className="truncate text-xs text-muted-foreground">
                {user.email ?? user.phone ?? user.user_uuid}
              </div>
            </div>
            <ModBadge status={user.moderation_status} />
          </div>
          {user.moderation_reason && (
            <p className="text-sm text-muted-foreground">Причина: {user.moderation_reason}</p>
          )}

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Роль</span>
            <select
              className="rounded-lg border bg-transparent px-2 py-1 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30 disabled:opacity-50"
              value={user.platform_role}
              disabled={isSelf || busy !== null}
              onChange={(e) =>
                void run(
                  "role",
                  () =>
                    updateUserApiV1AdminUsersUserUuidPatch({
                      path: { user_uuid: user.user_uuid },
                      body: { platform_role: e.target.value },
                    }),
                  "Роль обновлена",
                )
              }
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABEL[r]}
                </option>
              ))}
            </select>
            {isSelf && <span className="text-xs text-muted-foreground">(своя учётка)</span>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-2 pt-5">
          <div className="font-semibold">Документы</div>
          {(user.documents ?? []).length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">Документов нет</p>
          ) : (
            (user.documents ?? []).map((d) => (
              <div key={d.document_uuid} className="flex items-center justify-between gap-2 border-b py-2 last:border-0">
                <div className="min-w-0">
                  <div className="truncate text-sm">{d.kind}</div>
                  <div className="text-xs text-muted-foreground">{formatDateTime(d.created_at)}</div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="text-xs text-muted-foreground">{d.status}</span>
                  <Button variant="outline" size="sm" onClick={() => void viewDocument(d.document_uuid)}>
                    Открыть
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {!isSelf && (
        <Card>
          <CardContent className="space-y-3 pt-5">
            <div className="font-semibold">Модерация</div>
            <Input
              placeholder="Причина (для «дослать» и блокировки)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                disabled={busy !== null}
                onClick={() =>
                  void run(
                    "approve",
                    () => approveUserApiV1AdminUsersUserUuidApprovePost({ path: { user_uuid: user.user_uuid } }),
                    "Пользователь подтверждён",
                  )
                }
              >
                Подтвердить
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={busy !== null}
                onClick={() =>
                  void run(
                    "resubmit",
                    () =>
                      resubmitUserApiV1AdminUsersUserUuidResubmitPost({
                        path: { user_uuid: user.user_uuid },
                        body: { reason: reason.trim() },
                      }),
                    "Запрошена повторная загрузка",
                    true,
                  )
                }
              >
                Запросить повторно
              </Button>
              {user.moderation_status === "banned" ? (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={busy !== null}
                  onClick={() =>
                    void run(
                      "unban",
                      () => unbanUserApiV1AdminUsersUserUuidUnbanPost({ path: { user_uuid: user.user_uuid } }),
                      "Пользователь разблокирован",
                    )
                  }
                >
                  Разблокировать
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="text-status-danger"
                  disabled={busy !== null}
                  onClick={() =>
                    void run(
                      "ban",
                      () =>
                        banUserApiV1AdminUsersUserUuidBanPost({
                          path: { user_uuid: user.user_uuid },
                          body: { reason: reason.trim() },
                        }),
                      "Пользователь заблокирован",
                      true,
                    )
                  }
                >
                  Заблокировать
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function UsersPanel({ meUuid }: { meUuid: string }) {
  const [users, setUsers] = useState<AdminUserOut[] | null>(null);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [openUuid, setOpenUuid] = useState<string | null>(null);
  const [detail, setDetail] = useState<AdminUserDetailOut | null>(null);
  const [createEmail, setCreateEmail] = useState("");
  const [createRole, setCreateRole] = useState("user");
  const [busy, setBusy] = useState(false);

  const reload = useCallback(async () => {
    const { data } = await listUsersApiV1AdminUsersGet({
      query: { status: (status || undefined) as ModerationStatus | undefined, q: q.trim() || undefined },
    });
    setUsers(data ?? []);
  }, [status, q]);
  useEffect(() => {
    void reload();
  }, [reload]);

  const openDetail = useCallback(async (userUuid: string) => {
    setOpenUuid(userUuid);
    setDetail(null);
    const { data } = await userDetailApiV1AdminUsersUserUuidGet({ path: { user_uuid: userUuid } });
    setDetail(data ?? null);
  }, []);

  async function createUser() {
    if (!createEmail.includes("@")) return;
    setBusy(true);
    const { error } = await createUserApiV1AdminUsersPost({
      body: { email: createEmail.trim(), platform_role: createRole },
    });
    setBusy(false);
    if (error) {
      toast.error(detailText(error, "Не удалось создать пользователя"));
      return;
    }
    toast.success("Пользователь создан");
    setCreateEmail("");
    setCreateRole("user");
    void reload();
  }

  if (openUuid) {
    if (!detail) {
      return (
        <div className="flex justify-center py-10 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      );
    }
    return (
      <UserDetailView
        user={detail}
        meUuid={meUuid}
        onBack={() => {
          setOpenUuid(null);
          void reload();
        }}
        onChanged={() => void openDetail(openUuid)}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-3 pt-5">
          <div className="font-semibold">Создать пользователя</div>
          <div className="flex flex-wrap gap-2">
            <Input
              type="email"
              placeholder="Email"
              className="flex-1"
              value={createEmail}
              onChange={(e) => setCreateEmail(e.target.value)}
            />
            <select
              className="rounded-lg border bg-transparent px-2 py-1 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
              value={createRole}
              onChange={(e) => setCreateRole(e.target.value)}
            >
              {ROLE_OPTIONS.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABEL[r]}
                </option>
              ))}
            </select>
            <Button size="sm" disabled={busy} onClick={() => void createUser()}>
              {busy ? <Loader2 className="size-4 animate-spin" /> : "Создать"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-wrap items-center gap-2">
        {MOD_FILTERS.map((f) => (
          <button
            key={f.key || "all"}
            onClick={() => setStatus(f.key)}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              status === f.key
                ? "border-primary bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground",
            )}
          >
            {f.label}
          </button>
        ))}
        <Input
          placeholder="Поиск по email или имени"
          className="ml-auto w-full max-w-xs"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {users === null ? (
        <div className="flex justify-center py-10 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      ) : users.length === 0 ? (
        <EmptyCard text="Пользователи не найдены" />
      ) : (
        users.map((u) => (
          <button key={u.user_uuid} className="block w-full text-left" onClick={() => void openDetail(u.user_uuid)}>
            <Card className="transition-colors hover:border-ring">
              <CardContent className="flex items-center justify-between gap-3 pt-5">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{u.name ?? u.email ?? "Без имени"}</div>
                  <div className="truncate text-xs text-muted-foreground">{u.email ?? u.phone ?? u.user_uuid}</div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="text-xs text-muted-foreground">{ROLE_LABEL[u.platform_role] ?? u.platform_role}</span>
                  {(u.documents_count ?? 0) > 0 && (
                    <span className="rounded-full bg-secondary px-1.5 text-xs tabular-nums">{u.documents_count}📄</span>
                  )}
                  <ModBadge status={u.moderation_status} />
                </div>
              </CardContent>
            </Card>
          </button>
        ))
      )}
    </div>
  );
}

function ApplicationsPanel() {
  const [apps, setApps] = useState<AdminApplicationOut[] | null>(null);
  const [reason, setReason] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const reload = useCallback(async () => {
    const { data } = await listApplicationsApiV1AdminCompanyApplicationsGet({ query: { status: "pending" } });
    setApps(data ?? []);
  }, []);
  useEffect(() => {
    void reload();
  }, [reload]);

  async function approve(uuid: string) {
    setBusy(uuid);
    const { error } = await approveApplicationApiV1AdminCompanyApplicationsApplicationUuidApprovePost({
      path: { application_uuid: uuid },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось одобрить заявку"));
      return;
    }
    toast.success("Отель подключён, владельцу отправлен доступ");
    void reload();
  }

  async function reject(uuid: string) {
    const r = (reason[uuid] ?? "").trim();
    if (r.length < 3) {
      toast.error("Укажите причину отказа");
      return;
    }
    setBusy(uuid);
    const { error } = await rejectApplicationApiV1AdminCompanyApplicationsApplicationUuidRejectPost({
      path: { application_uuid: uuid },
      body: { reason: r },
    });
    setBusy(null);
    if (error) {
      toast.error(detailText(error, "Не удалось отклонить заявку"));
      return;
    }
    toast.success("Заявка отклонена");
    void reload();
  }

  if (apps === null) {
    return (
      <div className="flex justify-center py-10 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }
  if (apps.length === 0) {
    return <EmptyCard text="Новых заявок на подключение отеля нет" />;
  }

  return (
    <div className="space-y-4">
      {apps.map((a) => (
        <Card key={a.company_application_uuid}>
          <CardContent className="space-y-3 pt-5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate font-semibold">{a.name}</div>
                <div className="text-xs text-muted-foreground">
                  ИНН {a.inn} · ОГРН {a.ogrn}
                </div>
                <div className="text-xs text-muted-foreground">{a.address}</div>
              </div>
              {a.has_document ? (
                <Button variant="outline" size="sm" onClick={() => void viewApplicationProof(a.company_application_uuid)}>
                  Документ
                </Button>
              ) : (
                <span className="text-xs text-status-warn">без документа</span>
              )}
            </div>
            <div className="text-sm">
              {a.contact_name} · {a.contact_position}
              <div className="text-xs text-muted-foreground">
                {a.contact_email} · {a.contact_phone}
              </div>
            </div>
            <Input
              placeholder="Причина отказа"
              value={reason[a.company_application_uuid] ?? ""}
              onChange={(e) => setReason((prev) => ({ ...prev, [a.company_application_uuid]: e.target.value }))}
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                disabled={busy !== null}
                onClick={() => void approve(a.company_application_uuid)}
              >
                Одобрить и завести кабинет
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-status-danger"
                disabled={busy !== null}
                onClick={() => void reject(a.company_application_uuid)}
              >
                Отклонить
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

async function viewApplicationProof(applicationUuid: string) {
  const tokens = getTokens();
  const resp = await fetch(`/api/v1/admin/company-applications/${applicationUuid}/document`, {
    headers: tokens ? { Authorization: `Bearer ${tokens.access}` } : undefined,
  });
  if (!resp.ok) {
    toast.error("Не удалось открыть документ");
    return;
  }
  window.open(URL.createObjectURL(await resp.blob()), "_blank");
}

type TabKey =
  | "overview"
  | "users"
  | "applications"
  | "companies"
  | "requests"
  | "topups"
  | "payouts"
  | "complaints"
  | "chats"
  | "pricing"
  | "accounts"
  | "emails";

function adminInitials(text: string | null | undefined): string {
  const src = (text ?? "").trim();
  if (!src) return "AD";
  const parts = src.split(/\s+/).filter(Boolean);
  return (parts.length >= 2 ? parts[0][0] + parts[1][0] : src.slice(0, 2)).toUpperCase();
}

const SEVERITY_LABEL: Record<string, string> = { high: "Высокая", medium: "Средняя", low: "Низкая" };

export default function AdminPage() {
  const router = useRouter();
  const { me, loading: authLoading, logout } = useAuth();
  const [tab, setTab] = useState<TabKey>("overview");
  const [companies, setCompanies] = useState<CompanyModerationOut[] | null>(null);
  const [requests, setRequests] = useState<ModerationRequestOut[] | null>(null);
  const [topups, setTopups] = useState<TopupRequestOut[] | null>(null);
  const [payouts, setPayouts] = useState<PayoutOut[] | null>(null);
  const [complaints, setComplaints] = useState<ComplaintOut[] | null>(null);
  const [overview, setOverview] = useState<OverviewOut | null>(null);
  const [prices, setPrices] = useState<PriceOut[] | null>(null);

  const isAdmin = me?.platform_role === "admin";

  const reload = useCallback(async () => {
    const [companiesResp, requestsResp, topupsResp, payoutsResp, complaintsResp, overviewResp, pricesResp] =
      await Promise.all([
        listCompaniesApiV1AdminCompaniesGet({ query: { status: "pending" } }),
        listRequestsApiV1AdminRequestsGet(),
        adminListTopupRequestsApiV1AdminTopupRequestsGet(),
        adminListPayoutsApiV1AdminPayoutsGet(),
        adminOpenComplaintsApiV1AdminComplaintsGet(),
        overviewApiV1AdminOverviewGet(),
        listPricesApiV1AdminPricingGet(),
      ]);
    setCompanies(companiesResp.data ?? []);
    setRequests(requestsResp.data ?? []);
    setTopups((topupsResp.data ?? []).filter((t) => t.status === "pending"));
    setPayouts(payoutsResp.data ?? []);
    setComplaints(complaintsResp.data ?? []);
    setOverview(overviewResp.data ?? null);
    setPrices(pricesResp.data ?? []);
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

  if (
    authLoading ||
    !isAdmin ||
    companies === null ||
    requests === null ||
    topups === null ||
    payouts === null ||
    complaints === null ||
    prices === null
  ) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  const NAV: { key: TabKey; label: string; count: number | null }[] = [
    { key: "overview", label: "Обзор", count: null },
    { key: "users", label: "Пользователи", count: null },
    { key: "applications", label: "Заявки на отель", count: null },
    { key: "companies", label: "Организации", count: companies.length },
    { key: "requests", label: "Публикации", count: requests.length },
    { key: "topups", label: "Пополнения", count: topups.length },
    { key: "payouts", label: "Выплаты", count: payouts.length },
    { key: "complaints", label: "Жалобы", count: complaints.length },
    { key: "chats", label: "Чаты", count: null },
    { key: "accounts", label: "Счета", count: null },
    { key: "pricing", label: "Тарифы", count: null },
    { key: "emails", label: "Письма", count: null },
  ];
  const TITLES: Record<TabKey, { title: string; subtitle: string }> = {
    overview: { title: "Обзор", subtitle: "Здоровье платформы · реальное время" },
    users: { title: "Пользователи", subtitle: "Модерация KYC · роли · создание" },
    applications: { title: "Заявки на отель", subtitle: "Публичные заявки без аккаунта · документ должности" },
    companies: { title: "Организации", subtitle: "Заявки на подтверждение" },
    requests: { title: "Публикации", subtitle: "Модерация событий и тестов" },
    topups: { title: "Пополнения", subtitle: "Заявки на зачисление средств" },
    payouts: { title: "Выплаты", subtitle: "Выплаты соискателям по сменам" },
    complaints: { title: "Жалобы", subtitle: "Открытые споры" },
    chats: { title: "Чаты", subtitle: "Отредактированные и удалённые сообщения · версии" },
    accounts: { title: "Счета", subtitle: "Приём пополнений · лимиты по месяцам" },
    pricing: { title: "Тарифы", subtitle: "Стоимость услуг платформы" },
    emails: { title: "Письма", subtitle: "Журнал исходящих · ручная отправка" },
  };
  const head = TITLES[tab];

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <div className="mx-auto max-w-[1280px] px-4 py-6">
        <div className="flex min-h-[calc(100dvh-3rem)] overflow-hidden rounded-2xl border bg-card shadow-sm">
          <aside className="hidden w-64 shrink-0 flex-col border-r md:flex">
            <div className="flex items-center gap-3 border-b px-4 py-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-sm font-bold text-primary-foreground">
                L
              </div>
              <div className="min-w-0">
                <div className="truncate font-semibold">light-event</div>
                <div className="truncate text-xs text-muted-foreground">Admin Console</div>
              </div>
            </div>

            <nav className="flex-1 space-y-0.5 p-3">
              {NAV.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setTab(item.key)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    tab === item.key
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  {item.label}
                  {item.count ? (
                    <span className="ml-auto rounded-full bg-primary px-1.5 text-xs text-primary-foreground tabular-nums">
                      {item.count}
                    </span>
                  ) : null}
                </button>
              ))}
            </nav>

            <div className="border-t p-3">
              <div className="flex items-center gap-3 rounded-xl border px-3 py-2.5">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  {adminInitials(me?.name ?? me?.email)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{me?.name ?? me?.email ?? "Админ"}</div>
                  <div className="truncate text-xs text-muted-foreground">Администратор</div>
                </div>
                <button
                  className="shrink-0 text-muted-foreground hover:text-foreground"
                  title="Выйти"
                  onClick={() => {
                    logout();
                    router.replace("/");
                  }}
                >
                  <LogOut className="size-4" />
                </button>
              </div>
            </div>
          </aside>

          <main className="min-w-0 flex-1">
            <nav className="sticky top-0 z-10 flex gap-1.5 overflow-x-auto border-b bg-card px-3 py-2 md:hidden">
              {NAV.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setTab(item.key)}
                  className={cn(
                    "flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    tab === item.key
                      ? "border-primary bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  {item.label}
                  {item.count ? <span className="rounded-full bg-secondary px-1.5 tabular-nums">{item.count}</span> : null}
                </button>
              ))}
            </nav>

            <div className="px-6 py-8 md:px-10">
              <h1 className="text-2xl font-bold tracking-tight">{head.title}</h1>
              <p className="mt-1 text-sm text-muted-foreground">{head.subtitle}</p>

              {tab === "overview" && (
                <>
                  {overview && (
                    <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
                      {[
                        { label: "Пользователи", value: String(overview.users_count), to: "users" as TabKey },
                        { label: "KYC пройден", value: `${overview.kyc_verified_pct}%`, to: undefined },
                        { label: "Оборот", value: kopToRub(overview.turnover_kop), to: undefined },
                        { label: "Споры", value: String(overview.open_complaints), to: "complaints" as TabKey },
                      ].map((stat) => (
                        <Card
                          key={stat.label}
                          onClick={stat.to ? () => setTab(stat.to as TabKey) : undefined}
                          className={cn(stat.to && "cursor-pointer transition-colors hover:border-ring")}
                        >
                          <CardContent className="pt-5">
                            <div className="text-sm text-muted-foreground">{stat.label}</div>
                            <div className="mt-2 text-3xl font-bold tracking-tight tabular-nums">{stat.value}</div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}

                  <div className="mt-4 grid gap-4 lg:grid-cols-2">
                    <Card>
                      <CardContent className="pt-5">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">Очередь на модерацию</span>
                          <button
                            className="text-sm text-muted-foreground hover:text-foreground"
                            onClick={() => setTab("companies")}
                          >
                            Все →
                          </button>
                        </div>
                        <div className="mt-3 space-y-2">
                          {companies.length === 0 ? (
                            <p className="py-6 text-center text-sm text-muted-foreground">Очередь пуста</p>
                          ) : (
                            companies.slice(0, 5).map((c) => (
                              <div key={c.company_uuid} className="flex items-center justify-between gap-2">
                                <span className="truncate text-sm">{c.name}</span>
                                <span className="shrink-0 text-xs text-muted-foreground">на проверке</span>
                              </div>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardContent className="pt-5">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold">Жалобы</span>
                          <button
                            className="text-sm text-muted-foreground hover:text-foreground"
                            onClick={() => setTab("complaints")}
                          >
                            Все →
                          </button>
                        </div>
                        <div className="mt-3 space-y-2">
                          {complaints.length === 0 ? (
                            <p className="py-6 text-center text-sm text-muted-foreground">Открытых жалоб нет</p>
                          ) : (
                            complaints.slice(0, 5).map((c) => (
                              <div key={c.complaint_uuid} className="flex items-start justify-between gap-2">
                                <span className="min-w-0 flex-1 truncate text-sm">{c.text}</span>
                                <span className="shrink-0 text-xs font-medium text-muted-foreground">
                                  {SEVERITY_LABEL[c.severity] ?? c.severity}
                                </span>
                              </div>
                            ))
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </>
              )}

              <div className="mt-6 space-y-3">
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
        {tab === "payouts" &&
          (payouts.length === 0 ? (
            <EmptyCard text="Нет выплат к проведению" />
          ) : (
            payouts.map((p) => (
              <PayoutCard key={p.payout_uuid} payout={p} onDone={() => void reload()} />
            ))
          ))}
        {tab === "complaints" &&
          (complaints.length === 0 ? (
            <EmptyCard text="Открытых жалоб нет" />
          ) : (
            complaints.map((c) => (
              <ComplaintCard key={c.complaint_uuid} complaint={c} onDone={() => void reload()} />
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
        {tab === "chats" && <ModeratedChatsPanel />}
        {tab === "accounts" && <PaymentAccountsPanel />}
        {tab === "users" && <UsersPanel meUuid={me?.user_uuid ?? ""} />}
        {tab === "applications" && <ApplicationsPanel />}
        {tab === "emails" && <EmailsPanel />}
        {tab === "pricing" && (
          <>
            {prices.map((p) => (
              <PriceRow key={p.key} price={p} onSaved={() => void reload()} />
            ))}
            <CompanyPricingPanel />
          </>
        )}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
