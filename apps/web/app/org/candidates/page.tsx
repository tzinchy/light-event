"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Check, Loader2, UserX, UsersRound } from "lucide-react";
import {
  changeStatusApiV1ApplicationsApplicationUuidStatusPost,
  companyApplicationsApiV1CompaniesCompanyUuidApplicationsGet,
  deleteCandidateApiV1CompaniesCompanyUuidCandidatesUserUuidDelete,
  listCandidatesApiV1CompaniesCompanyUuidCandidatesGet,
  putCandidateApiV1CompaniesCompanyUuidCandidatesUserUuidPut,
  type CandidateEntryOut,
  type CompanyApplicationOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ChatButton } from "@/components/chat-button";
import { DICT } from "@/lib/dict";
import { useOrg } from "@/lib/org-context";
import { formatShiftWindow } from "@/lib/format";
import { cn } from "@/lib/utils";

const APP_STATUS: Record<string, { label: string; className: string }> = {
  review: { label: DICT.stReview, className: "border-status-warn-border bg-status-warn-bg text-status-warn" },
  confirmed: { label: DICT.hired, className: "border-brand-border bg-brand-soft text-brand-strong" },
  reserve: { label: DICT.reserveTeam, className: "border-status-info-border bg-status-info-bg text-status-info" },
};

type Tab = "all" | "shortlist" | "reserve" | "blacklist";

export default function CandidatesPage() {
  const { current } = useOrg();
  const [apps, setApps] = useState<CompanyApplicationOut[] | null>(null);
  const [entries, setEntries] = useState<CandidateEntryOut[]>([]);
  const [tab, setTab] = useState<Tab>("all");
  const [busy, setBusy] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const companyUuid = current?.company.company_uuid;

  const load = useCallback(async () => {
    if (!companyUuid) return;
    const [a, e] = await Promise.all([
      companyApplicationsApiV1CompaniesCompanyUuidApplicationsGet({
        path: { company_uuid: companyUuid },
      }),
      listCandidatesApiV1CompaniesCompanyUuidCandidatesGet({ path: { company_uuid: companyUuid } }),
    ]);
    if (a.error) {
      setForbidden(true);
      return;
    }
    setApps(a.data ?? []);
    setEntries(e.data ?? []);
  }, [companyUuid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!companyUuid) return null;

  if (forbidden) {
    return (
      <div className="flex flex-col items-center py-24 text-center">
        <UserX className="size-8 text-muted-foreground" />
        <h1 className="mt-3 font-semibold">Недостаточно прав</h1>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Раздел «Отклики» доступен участникам с правом «{DICT.permHire}».
        </p>
      </div>
    );
  }

  const listOf = (userUuid: string) => entries.find((e) => e.user_uuid === userUuid)?.list ?? null;

  const counts: Record<Tab, number> = {
    all: apps?.length ?? 0,
    shortlist: entries.filter((e) => e.list === "shortlist").length,
    reserve: entries.filter((e) => e.list === "reserve").length,
    blacklist: entries.filter((e) => e.list === "blacklist").length,
  };

  const TABS: { key: Tab; label: string }[] = [
    { key: "all", label: DICT.allApplicants },
    { key: "shortlist", label: DICT.best },
    { key: "reserve", label: DICT.reserveTeam },
    { key: "blacklist", label: DICT.blacklistTab },
  ];

  const visibleApps =
    tab === "all"
      ? (apps ?? [])
      : (apps ?? []).filter((a) => listOf(a.user_uuid) === tab);
  // ЧС-кандидаты скрыты из откликов backend'ом — вкладка ЧС показывает записи списка
  const blacklisted = entries.filter((e) => e.list === "blacklist");

  async function setStatus(applicationUuid: string, action: "confirm" | "reserve") {
    setBusy(applicationUuid);
    const { error } = await changeStatusApiV1ApplicationsApplicationUuidStatusPost({
      path: { application_uuid: applicationUuid },
      body: { action },
    });
    setBusy(null);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось изменить статус"));
      return;
    }
    await load();
  }

  async function putList(userUuid: string, list: "shortlist" | "reserve" | "blacklist") {
    setBusy(userUuid);
    const { error } = await putCandidateApiV1CompaniesCompanyUuidCandidatesUserUuidPut({
      path: { company_uuid: companyUuid!, user_uuid: userUuid },
      body: { list },
    });
    setBusy(null);
    if (error) {
      toast.error("Не удалось обновить список");
      return;
    }
    if (list === "blacklist") toast.success(DICT.blacklistedNote);
    await load();
  }

  async function removeFromList(userUuid: string) {
    setBusy(userUuid);
    const { error } = await deleteCandidateApiV1CompaniesCompanyUuidCandidatesUserUuidDelete({
      path: { company_uuid: companyUuid!, user_uuid: userUuid },
    });
    setBusy(null);
    if (error) {
      toast.error("Не удалось убрать из списка");
      return;
    }
    await load();
  }

  return (
    <div>
      <h1 className="text-xl font-semibold">{DICT.candidatesTitle}</h1>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={cn(
              "rounded-full border px-3 py-1 text-sm font-medium",
              tab === t.key
                ? "border-primary bg-primary text-primary-foreground"
                : "hover:bg-secondary",
            )}
            onClick={() => setTab(t.key)}
          >
            {t.label} · {counts[t.key]}
          </button>
        ))}
      </div>

      {apps === null ? (
        <div className="mt-12 flex justify-center text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      ) : tab === "blacklist" ? (
        blacklisted.length === 0 ? (
          <p className="mt-12 text-center text-sm text-muted-foreground">Чёрный список пуст.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {blacklisted.map((entry) => (
              <Card key={entry.entry_uuid}>
                <CardContent className="flex flex-wrap items-center gap-3 pt-6">
                  <div className="min-w-0 flex-1">
                    <div className="font-mono text-sm">{entry.user_uuid.slice(0, 8)}…</div>
                    {entry.note && (
                      <div className="text-sm text-muted-foreground">{entry.note}</div>
                    )}
                    <div className="mt-1 text-xs text-status-danger">{DICT.blacklistedNote}</div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busy === entry.user_uuid}
                    onClick={() => void removeFromList(entry.user_uuid)}
                  >
                    {DICT.removeBlacklist}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )
      ) : visibleApps.length === 0 ? (
        <div className="mt-12 flex flex-col items-center text-center text-muted-foreground">
          <UsersRound className="size-8" />
          <p className="mt-3 text-sm">{DICT.noApplicants}</p>
        </div>
      ) : (
        <div className="mt-4 space-y-6">
          {[
            ...visibleApps
              .reduce((m, app) => {
                const key = `${app.vacancy.event_title}|${app.vacancy.starts_at}|${app.vacancy.role_name}`;
                const g = m.get(key) ?? { vacancy: app.vacancy, apps: [] as typeof visibleApps };
                g.apps.push(app);
                m.set(key, g);
                return m;
              }, new Map<string, { vacancy: (typeof visibleApps)[number]["vacancy"]; apps: typeof visibleApps }>())
              .values(),
          ].map((group) => (
            <div key={`${group.vacancy.event_title}|${group.vacancy.starts_at}`}>
              {/* событие → отклики на него */}
              <div className="mb-2 flex flex-wrap items-baseline gap-2 border-b pb-1.5">
                <h2 className="font-semibold">{group.vacancy.event_title}</h2>
                <span className="text-sm text-muted-foreground">
                  {group.vacancy.role_name} · {formatShiftWindow(group.vacancy.starts_at, group.vacancy.ends_at)} ·{" "}
                  {group.apps.length} откл.
                </span>
              </div>
              <div className="space-y-3">
                {group.apps.map((app) => {
                  const status = APP_STATUS[app.status] ?? { label: app.status, className: "" };
                  const list = listOf(app.user_uuid);
                  return (
              <Card key={app.application_uuid}>
                <CardContent className="pt-6">
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="flex size-10 items-center justify-center rounded-full bg-secondary text-xs font-semibold uppercase">
                      {(app.user_name ?? app.user_uuid).slice(0, 2)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          href={`/w/${app.user_uuid}`}
                          className="font-medium hover:underline"
                        >
                          {app.user_name ?? `${app.user_uuid.slice(0, 8)}…`}
                        </Link>
                        <span className={cn("status-badge", status.className)}>{status.label}</span>
                        {list === "shortlist" && (
                          <span className="status-badge border-brand-border bg-brand-soft text-brand-strong">
                            {DICT.best}
                          </span>
                        )}
                        {app.company_test_passed && (
                          <span className="status-badge border-status-violet-border bg-status-violet-bg text-status-violet">
                            {DICT.companyTestPassedBadge}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {app.status !== "confirmed" ? (
                        <Button
                          size="sm"
                          disabled={busy !== null}
                          onClick={() => void setStatus(app.application_uuid, "confirm")}
                        >
                          {DICT.hire}
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline" disabled>
                          <Check className="size-3.5" />
                          {DICT.hired}
                        </Button>
                      )}
                      {app.status === "review" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy !== null}
                          onClick={() => void setStatus(app.application_uuid, "reserve")}
                        >
                          {DICT.toReserve}
                        </Button>
                      )}
                      <ChatButton applicationUuid={app.application_uuid} />
                      {list !== "shortlist" && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy !== null}
                          onClick={() => void putList(app.user_uuid, "shortlist")}
                        >
                          {DICT.best}
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-status-danger"
                        disabled={busy !== null}
                        onClick={() => void putList(app.user_uuid, "blacklist")}
                      >
                        {DICT.toBlacklist}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
