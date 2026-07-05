"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ArrowDownLeft, ArrowUpRight, FileUp, Loader2, ShieldAlert } from "lucide-react";
import {
  companyAccountApiV1CompaniesCompanyUuidAccountGet,
  companyOperationsApiV1CompaniesCompanyUuidAccountOperationsGet,
  companyPayoutsApiV1CompaniesCompanyUuidPayoutsGet,
  createTopupRequestApiV1CompaniesCompanyUuidTopupRequestsPost,
  topupRequisitesApiV1CompaniesCompanyUuidTopupRequisitesGet,
  uploadDocumentApiV1DocumentsPost,
  type AccountOut,
  type OperationOut,
  type PayoutOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DICT } from "@/lib/dict";
import { useOrg } from "@/lib/org-context";
import { formatDateTime, kopToRub, rubInputToKop } from "@/lib/format";
import { cn } from "@/lib/utils";

const PAYOUT_STATUS: Record<string, { label: string; className: string }> = {
  pending: { label: "Ожидает проведения", className: "bg-amber-50 text-amber-700" },
  processing: { label: "Обрабатывается", className: "bg-blue-50 text-blue-700" },
  paid: { label: "Выплачено", className: "bg-brand-soft text-brand-strong" },
};

const OP_LABEL: Record<string, string> = {
  topup: "Пополнение счёта",
  vacancy_fee: "Публикация смены",
  test_fee: "Создание теста",
  hold: "Резерв под выплату",
  release: "Возврат резерва",
  payout: "Выплата",
  commission: "Комиссия платформы · 6%",
};

function TopupDialog({
  companyUuid,
  onCreated,
}: {
  companyUuid: string;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [amount, setAmount] = useState("");
  const [proof, setProof] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [requisites, setRequisites] = useState<{ account_name?: string | null; requisites?: string | null } | null>(
    null,
  );
  const fileRef = useRef<HTMLInputElement | null>(null);

  const amountKop = rubInputToKop(amount);

  // как только введена сумма — показываем, на какой счёт переводить (подбирается автоматически)
  useEffect(() => {
    if (!amountKop) {
      setRequisites(null);
      return;
    }
    let active = true;
    const t = setTimeout(async () => {
      const { data } = await topupRequisitesApiV1CompaniesCompanyUuidTopupRequisitesGet({
        path: { company_uuid: companyUuid },
        query: { amount_kop: amountKop },
      });
      if (active) setRequisites(data ?? null);
    }, 400);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [amountKop, companyUuid]);

  async function submit() {
    if (!amountKop || !proof) return;
    setBusy(true);
    const upload = await uploadDocumentApiV1DocumentsPost({
      // openapi-ts типизирует binary как string; SDK шлёт multipart и принимает File
      body: { kind: "payment_proof", file: proof as unknown as string },
    });
    if (upload.error || !upload.data) {
      setBusy(false);
      toast.error("Не удалось загрузить подтверждение платежа");
      return;
    }
    const { error } = await createTopupRequestApiV1CompaniesCompanyUuidTopupRequestsPost({
      path: { company_uuid: companyUuid },
      body: {
        amount_kop: amountKop,
        proof_document_uuid: upload.data.document_uuid,
      },
    });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось создать заявку"));
      return;
    }
    toast.success("Заявка на пополнение отправлена администратору");
    setOpen(false);
    setAmount("");
    setProof(null);
    onCreated();
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>{DICT.topUp}</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Заявка на пополнение</DialogTitle>
          <DialogDescription>
            Переведите сумму по реквизитам платформы и приложите подтверждение — администратор
            зачислит средства после проверки.
          </DialogDescription>
        </DialogHeader>
        <div>
          <Label htmlFor="topup-amount">Сумма, ₽</Label>
          <Input
            id="topup-amount"
            className="mt-2 font-mono"
            inputMode="decimal"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="200 000"
          />

          {amountKop && requisites && (
            <div className="mt-3 rounded-xl border bg-secondary/40 p-3 text-sm">
              {requisites.requisites ? (
                <>
                  <div className="text-xs font-medium text-muted-foreground">
                    Переведите на счёт{requisites.account_name ? ` «${requisites.account_name}»` : ""}:
                  </div>
                  <div className="mt-1 whitespace-pre-line font-medium">{requisites.requisites}</div>
                </>
              ) : (
                <div className="text-muted-foreground">
                  Реквизиты подберёт администратор — заявку можно отправить, зачислят после проверки.
                </div>
              )}
            </div>
          )}

          <Button
            variant="outline"
            className="mt-3 w-full"
            onClick={() => fileRef.current?.click()}
            disabled={busy}
          >
            <FileUp className="size-4" />
            {proof ? proof.name : "Приложить подтверждение платежа"}
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*,.pdf"
            className="hidden"
            onChange={(e) => setProof(e.target.files?.[0] ?? null)}
          />
          <Button
            className="mt-4 w-full"
            disabled={!amountKop || !proof || busy}
            onClick={() => void submit()}
          >
            {busy && <Loader2 className="size-4 animate-spin" />}
            Отправить заявку
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function BalancePage() {
  const { current } = useOrg();
  const [account, setAccount] = useState<AccountOut | null>(null);
  const [operations, setOperations] = useState<OperationOut[]>([]);
  const [payouts, setPayouts] = useState<PayoutOut[]>([]);
  const [forbidden, setForbidden] = useState(false);
  const [loading, setLoading] = useState(true);

  const companyUuid = current?.company.company_uuid;

  const load = useCallback(async () => {
    if (!companyUuid) return;
    const [acc, ops, pays] = await Promise.all([
      companyAccountApiV1CompaniesCompanyUuidAccountGet({ path: { company_uuid: companyUuid } }),
      companyOperationsApiV1CompaniesCompanyUuidAccountOperationsGet({
        path: { company_uuid: companyUuid },
      }),
      companyPayoutsApiV1CompaniesCompanyUuidPayoutsGet({ path: { company_uuid: companyUuid } }),
    ]);
    if (acc.error) {
      setForbidden(true);
      setLoading(false);
      return;
    }
    setAccount(acc.data ?? null);
    setOperations(ops.data ?? []);
    setPayouts(pays.data ?? []);
    setLoading(false);
  }, [companyUuid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!companyUuid) return null;

  if (forbidden) {
    return (
      <div className="flex flex-col items-center py-24 text-center">
        <ShieldAlert className="size-8 text-muted-foreground" />
        <h1 className="mt-3 font-semibold">Недостаточно прав</h1>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Раздел «Финансы и баланс» доступен участникам с правом «{DICT.permFinance}». Обратитесь к
          главному менеджеру.
        </p>
      </div>
    );
  }

  if (loading || !account) {
    return (
      <div className="mt-16 flex justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  const stats = [
    { label: DICT.available, value: account.available_kop, accent: true },
    { label: DICT.onHold, value: account.on_hold_kop, accent: false },
    { label: DICT.totalBal, value: account.total_kop, accent: false },
  ];

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{DICT.balanceTitle}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Пополнение проходит ручную проверку администратора платформы.
          </p>
        </div>
        <TopupDialog companyUuid={companyUuid} onCreated={() => void load()} />
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-6">
              <div className="text-xs font-medium text-muted-foreground">{stat.label}</div>
              <div
                className={cn(
                  "mt-1 font-mono text-2xl font-semibold",
                  stat.accent && "text-brand-strong",
                )}
              >
                {kopToRub(stat.value)}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">Выплаты к проведению</CardTitle>
        </CardHeader>
        <CardContent>
          {payouts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Пока нет выплат: они появляются после подтверждения соискателей на смену.
            </p>
          ) : (
            <div className="divide-y">
              {payouts.map((payout) => {
                const status = PAYOUT_STATUS[payout.status] ?? PAYOUT_STATUS.pending;
                return (
                  <div key={payout.payout_uuid} className="flex items-center gap-3 py-3">
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">{payout.event_title}</div>
                      <div className="text-xs text-muted-foreground">
                        {payout.workers_count} чел. · {formatDateTime(payout.created_at)}
                      </div>
                    </div>
                    <span
                      className={cn(
                        "shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium",
                        status.className,
                      )}
                    >
                      {status.label}
                    </span>
                    <div className="font-mono text-sm font-semibold">{kopToRub(payout.amount_kop)}</div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="text-base">{DICT.accountOps}</CardTitle>
        </CardHeader>
        <CardContent>
          {operations.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Операций пока нет. Пополните счёт, чтобы публиковать события.
            </p>
          ) : (
            <div className="divide-y">
              {operations.map((op) => {
                const incoming = op.direction === "in";
                return (
                  <div key={op.ledger_entry_uuid} className="flex items-center gap-3 py-3">
                    <div
                      className={cn(
                        "flex size-8 items-center justify-center rounded-full",
                        incoming
                          ? "bg-brand-soft text-brand-strong"
                          : "bg-secondary text-muted-foreground",
                      )}
                    >
                      {incoming ? (
                        <ArrowDownLeft className="size-4" />
                      ) : (
                        <ArrowUpRight className="size-4" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {OP_LABEL[op.kind] ?? op.kind}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {formatDateTime(op.created_at)}
                      </div>
                    </div>
                    <div
                      className={cn(
                        "font-mono text-sm font-semibold",
                        incoming ? "text-brand-strong" : "text-foreground",
                      )}
                    >
                      {incoming ? "+" : "−"}
                      {kopToRub(op.amount_kop)}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
