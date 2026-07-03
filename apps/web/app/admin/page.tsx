"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BadgeCheck, Building2, Loader2, MapPin, Phone, XCircle } from "lucide-react";
import {
  listCompaniesApiV1AdminCompaniesGet,
  rejectCompanyApiV1AdminCompaniesCompanyUuidRejectPost,
  verifyCompanyApiV1AdminCompaniesCompanyUuidVerifyPost,
  type CompanyModerationOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/lib/auth-context";

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
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось подтвердить"));
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
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось отклонить"));
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

export default function AdminPage() {
  const router = useRouter();
  const { me, loading: authLoading } = useAuth();
  const [companies, setCompanies] = useState<CompanyModerationOut[] | null>(null);

  const isAdmin = me?.platform_role === "admin";

  const reload = useCallback(async () => {
    const { data } = await listCompaniesApiV1AdminCompaniesGet({
      query: { status: "pending" },
    });
    setCompanies(data ?? []);
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

  if (authLoading || !isAdmin || companies === null) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8">
      <h1 className="text-xl font-bold">Модерация организаций</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Заявки на регистрацию: проверьте реквизиты и подтвердите или отклоните с причиной.
      </p>

      <div className="mt-5 space-y-3">
        {companies.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              Пока нет заявок на проверку
            </CardContent>
          </Card>
        ) : (
          companies.map((c) => (
            <ApplicationCard key={c.company_uuid} company={c} onDone={() => void reload()} />
          ))
        )}
      </div>
    </div>
  );
}
