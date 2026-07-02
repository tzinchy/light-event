"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Archive, CalendarDays, Loader2, Send } from "lucide-react";
import {
  archiveVacancyApiV1VacanciesVacancyUuidArchivePost,
  companyVacanciesApiV1CompaniesCompanyUuidVacanciesGet,
  listFilialsApiV1CompaniesCompanyUuidFilialsGet,
  publishVacancyApiV1VacanciesVacancyUuidPublishPost,
  type FilialOut,
  type VacancyOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/status-badge";
import { DICT } from "@/lib/dict";
import { useOrg } from "@/lib/org-context";
import { formatShiftWindow, kopToRub } from "@/lib/format";
import { cn } from "@/lib/utils";

const FILTERS = [
  { key: "all", label: DICT.filterAll },
  { key: "active", label: DICT.filterActive },
  { key: "draft", label: DICT.filterDraft },
] as const;

export default function OrgEventsPage() {
  const { current } = useOrg();
  const [vacancies, setVacancies] = useState<VacancyOut[] | null>(null);
  const [filials, setFilials] = useState<FilialOut[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]["key"]>("all");
  const [filialFilter, setFilialFilter] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const companyUuid = current?.company.company_uuid;

  const load = useCallback(async () => {
    if (!companyUuid) return;
    const [vacs, fils] = await Promise.all([
      companyVacanciesApiV1CompaniesCompanyUuidVacanciesGet({ path: { company_uuid: companyUuid } }),
      listFilialsApiV1CompaniesCompanyUuidFilialsGet({ path: { company_uuid: companyUuid } }),
    ]);
    setVacancies(vacs.data ?? []);
    setFilials(fils.data ?? []);
  }, [companyUuid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!companyUuid) return null;

  const filialName = (uuid: string) => filials.find((f) => f.filial_uuid === uuid)?.name ?? "—";

  const visible = (vacancies ?? []).filter((v) => {
    if (filialFilter && v.filial_uuid !== filialFilter) return false;
    if (filter === "active") return v.status === "active" && !v.archived_at;
    if (filter === "draft") return v.status === "draft";
    return true;
  });

  async function publish(vacancyUuid: string) {
    setBusy(vacancyUuid);
    const { error } = await publishVacancyApiV1VacanciesVacancyUuidPublishPost({
      path: { vacancy_uuid: vacancyUuid },
    });
    setBusy(null);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось опубликовать"));
      return;
    }
    toast.success(DICT.publishedPaid);
    await load();
  }

  async function archive(vacancyUuid: string) {
    setBusy(vacancyUuid);
    const { error } = await archiveVacancyApiV1VacanciesVacancyUuidArchivePost({
      path: { vacancy_uuid: vacancyUuid },
    });
    setBusy(null);
    if (error) {
      toast.error("Не удалось архивировать");
      return;
    }
    await load();
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold">{DICT.eventsTitle}</h1>
        <Button asChild size="sm">
          <Link href="/org/create">Создать событие</Link>
        </Button>
      </div>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            className={cn(
              "rounded-full border px-3 py-1 text-sm font-medium",
              filter === f.key
                ? "border-primary bg-primary text-primary-foreground"
                : "hover:bg-secondary",
            )}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
        {filials.length > 1 && (
          <>
            <div className="mx-1 w-px bg-border" />
            <button
              className={cn(
                "rounded-full border px-3 py-1 text-sm font-medium",
                filialFilter === null
                  ? "border-primary bg-primary text-primary-foreground"
                  : "hover:bg-secondary",
              )}
              onClick={() => setFilialFilter(null)}
            >
              Все филиалы
            </button>
            {filials.map((f) => (
              <button
                key={f.filial_uuid}
                className={cn(
                  "rounded-full border px-3 py-1 text-sm font-medium",
                  filialFilter === f.filial_uuid
                    ? "border-primary bg-primary text-primary-foreground"
                    : "hover:bg-secondary",
                )}
                onClick={() => setFilialFilter(f.filial_uuid)}
              >
                {f.name}
              </button>
            ))}
          </>
        )}
      </div>

      {vacancies === null ? (
        <div className="mt-12 flex justify-center text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      ) : visible.length === 0 ? (
        <div className="mt-12 flex flex-col items-center text-center text-muted-foreground">
          <CalendarDays className="size-8" />
          <p className="mt-3 text-sm">{DICT.noEvents}</p>
        </div>
      ) : (
        <div className="mt-4 space-y-3">
          {visible.map((v) => (
            <Card key={v.vacancy_uuid}>
              <CardContent className="pt-6">
                <div className="flex flex-wrap items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{v.event_title}</span>
                      <StatusBadge status={v.archived_at ? "archived" : v.status} />
                    </div>
                    <div className="mt-1 text-sm text-muted-foreground">
                      {filialName(v.filial_uuid)} · {formatShiftWindow(v.starts_at, v.ends_at)} ·{" "}
                      {v.role_name} ×{v.slots}
                    </div>
                    {v.status === "rejected" && v.reject_reason && (
                      <div className="mt-1 text-sm text-status-danger">
                        Причина: {v.reject_reason}
                      </div>
                    )}
                  </div>
                  <div className="font-mono text-sm font-semibold">
                    {kopToRub(v.pay_total_kop)}
                    <span className="font-normal text-muted-foreground"> ×{v.slots}</span>
                  </div>
                  {v.status === "draft" && (
                    <Button
                      size="sm"
                      disabled={busy === v.vacancy_uuid}
                      onClick={() => void publish(v.vacancy_uuid)}
                    >
                      {busy === v.vacancy_uuid ? (
                        <Loader2 className="size-3.5 animate-spin" />
                      ) : (
                        <Send className="size-3.5" />
                      )}
                      {DICT.payAndPublish}
                    </Button>
                  )}
                  {!v.archived_at && v.status !== "draft" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={busy === v.vacancy_uuid}
                      onClick={() => void archive(v.vacancy_uuid)}
                      title="В архив"
                    >
                      <Archive className="size-4" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
