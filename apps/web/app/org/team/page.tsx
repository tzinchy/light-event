"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Check, Copy, Link2, Loader2, Lock, Trash2 } from "lucide-react";
import {
  createInviteApiV1CompaniesCompanyUuidInvitesPost,
  listInvitesApiV1CompaniesCompanyUuidInvitesGet,
  listTeamApiV1CompaniesCompanyUuidTeamGet,
  removeMemberApiV1TeamMembersTeamMemberUuidDelete,
  revokeInviteApiV1InvitesInviteLinkUuidRevokePost,
  updatePermissionsApiV1TeamMembersTeamMemberUuidPermissionsPatch,
  type InviteOut,
  type TeamMemberOut,
} from "@light-event/shared-types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";
import { useOrg } from "@/lib/org-context";
import { formatDateTime } from "@/lib/format";

const ROLE_LABEL: Record<string, string> = {
  main_manager: DICT.roleHead,
  manager: DICT.roleManager,
  coordinator: DICT.roleCoord,
  staff: DICT.roleStaff,
};

const PERMS = [
  { key: "perm_create", label: DICT.permCreate },
  { key: "perm_hire", label: DICT.permHire },
  { key: "perm_finance", label: DICT.permFinance },
  { key: "perm_invite", label: DICT.permInvite },
] as const;

const EXPIRES = [
  { value: "24h", label: DICT.exp24 },
  { value: "7d", label: DICT.exp7 },
  { value: "30d", label: DICT.exp30 },
] as const;

const INVITE_ROLES = [
  { value: "manager", label: DICT.roleManager },
  { value: "coordinator", label: DICT.roleCoord },
  { value: "staff", label: DICT.roleStaff },
] as const;

function MemberRow({
  member,
  isSelf,
  canManage,
  onChanged,
}: {
  member: TeamMemberOut;
  isSelf: boolean;
  canManage: boolean;
  onChanged: () => void;
}) {
  const [busyPerm, setBusyPerm] = useState<string | null>(null);
  const isHead = member.company_role === "main_manager";

  async function togglePerm(key: (typeof PERMS)[number]["key"], value: boolean) {
    setBusyPerm(key);
    const { error } = await updatePermissionsApiV1TeamMembersTeamMemberUuidPermissionsPatch({
      path: { team_member_uuid: member.team_member_uuid },
      body: { [key]: value },
    });
    setBusyPerm(null);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось изменить права"));
      return;
    }
    onChanged();
  }

  async function remove() {
    const { error } = await removeMemberApiV1TeamMembersTeamMemberUuidDelete({
      path: { team_member_uuid: member.team_member_uuid },
    });
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось удалить участника"));
      return;
    }
    toast.success("Участник удалён из команды");
    onChanged();
  }

  return (
    <Card>
      <CardContent className="pt-6">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex size-10 items-center justify-center rounded-full bg-secondary font-mono text-xs font-semibold uppercase">
          {member.user_uuid.slice(0, 2)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate font-medium">
              {member.email ?? `${member.user_uuid.slice(0, 8)}…`}
            </span>
            {isSelf && <span className="text-xs text-muted-foreground">(вы)</span>}
          </div>
          <Badge
            variant="outline"
            className={
              isHead
                ? "mt-1 border-brand-border bg-brand-soft text-brand-strong"
                : "mt-1"
            }
          >
            {ROLE_LABEL[member.company_role] ?? member.company_role}
          </Badge>
        </div>
        {canManage && !isHead && (
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Удалить из команды">
                <Trash2 className="size-4 text-status-danger" />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Удалить участника?</DialogTitle>
                <DialogDescription>
                  Доступ к кабинету компании будет отозван сразу.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="destructive" onClick={() => void remove()}>
                  Удалить
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {isHead ? (
          <div className="col-span-full flex items-center gap-2 text-sm text-muted-foreground">
            <Lock className="size-3.5" />
            {DICT.fullAccess} — права главного менеджера изменить нельзя
          </div>
        ) : (
          PERMS.map((perm) => (
            <label
              key={perm.key}
              className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm"
            >
              {perm.label}
              <Switch
                checked={member[perm.key]}
                disabled={!canManage || busyPerm !== null}
                onCheckedChange={(v) => void togglePerm(perm.key, v)}
                aria-label={perm.label}
              />
            </label>
          ))
        )}
      </div>
      </CardContent>
    </Card>
  );
}

function InviteBlock({ companyUuid }: { companyUuid: string }) {
  const [invites, setInvites] = useState<InviteOut[] | null>(null);
  const [role, setRole] = useState<string>("manager");
  const [expiresIn, setExpiresIn] = useState<string>("7d");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const load = useCallback(async () => {
    const { data, error } = await listInvitesApiV1CompaniesCompanyUuidInvitesGet({
      path: { company_uuid: companyUuid },
    });
    // 403 = нет права invite — блок просто не показываем
    setInvites(error ? null : (data ?? []));
  }, [companyUuid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (invites === null) return null;

  async function create() {
    setBusy(true);
    const { error } = await createInviteApiV1CompaniesCompanyUuidInvitesPost({
      path: { company_uuid: companyUuid },
      body: {
        role: role as (typeof INVITE_ROLES)[number]["value"],
        expires_in: expiresIn as (typeof EXPIRES)[number]["value"],
        max_uses: 5,
      },
    });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось создать ссылку"));
      return;
    }
    toast.success("Ссылка готова — скопируйте и отправьте");
    await load();
  }

  async function revoke(uuid: string) {
    const { error } = await revokeInviteApiV1InvitesInviteLinkUuidRevokePost({
      path: { invite_link_uuid: uuid },
    });
    if (error) {
      toast.error("Не удалось отозвать ссылку");
      return;
    }
    await load();
  }

  async function copy(invite: InviteOut) {
    await navigator.clipboard.writeText(`${window.location.origin}/join/${invite.code}`);
    setCopied(invite.invite_link_uuid);
    setTimeout(() => setCopied(null), 2000);
  }

  return (
    <Card className="mt-6">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Link2 className="size-4" />
          {DICT.inviteTitle}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap items-end gap-2">
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">{DICT.linkRole}</div>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {INVITE_ROLES.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <div className="mb-1.5 text-xs font-medium text-muted-foreground">{DICT.linkValid}</div>
            <Select value={expiresIn} onValueChange={setExpiresIn}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPIRES.map((e) => (
                  <SelectItem key={e.value} value={e.value}>
                    {e.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={() => void create()} disabled={busy}>
            {busy && <Loader2 className="size-4 animate-spin" />}
            {DICT.generateLink}
          </Button>
        </div>

        {invites.length === 0 ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Пока нет пригласительных ссылок.
          </p>
        ) : (
          <div className="mt-4 space-y-2">
            {invites.map((invite) => (
              <div
                key={invite.invite_link_uuid}
                className="flex flex-wrap items-center gap-2 rounded-lg border p-3 text-sm"
              >
                <code className="rounded bg-secondary px-2 py-0.5 font-mono text-xs">
                  join/{invite.code}
                </code>
                <Badge variant="secondary">{ROLE_LABEL[invite.role] ?? invite.role}</Badge>
                <span className="text-xs text-muted-foreground">
                  {DICT.uses} {invite.uses_count} / {invite.max_uses}
                </span>
                <span className="ml-auto text-xs text-muted-foreground">
                  {invite.active
                    ? `истекает ${formatDateTime(invite.expires_at)}`
                    : DICT.expired}
                </span>
                {invite.active && (
                  <>
                    <Button variant="outline" size="sm" onClick={() => void copy(invite)}>
                      {copied === invite.invite_link_uuid ? (
                        <>
                          <Check className="size-3.5" /> {DICT.copied}
                        </>
                      ) : (
                        <>
                          <Copy className="size-3.5" /> {DICT.copy}
                        </>
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void revoke(invite.invite_link_uuid)}
                    >
                      {DICT.revoke}
                    </Button>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function TeamPage() {
  const { me } = useAuth();
  const { current } = useOrg();
  const [team, setTeam] = useState<TeamMemberOut[]>([]);
  const [loading, setLoading] = useState(true);

  const companyUuid = current?.company.company_uuid;

  const load = useCallback(async () => {
    if (!companyUuid) return;
    const { data } = await listTeamApiV1CompaniesCompanyUuidTeamGet({
      path: { company_uuid: companyUuid },
    });
    setTeam(data ?? []);
    setLoading(false);
  }, [companyUuid]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!companyUuid) return null;

  const isHead = current.company_role === "main_manager";

  return (
    <div>
      <h1 className="text-xl font-semibold">{DICT.teamTitle}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{DICT.teamSub}</p>

      {loading ? (
        <div className="mt-8 flex justify-center text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {team.map((member) => (
            <MemberRow
              key={member.team_member_uuid}
              member={member}
              isSelf={member.user_uuid === me?.user_uuid}
              canManage={isHead}
              onChanged={() => void load()}
            />
          ))}
        </div>
      )}

      <InviteBlock companyUuid={companyUuid} />
    </div>
  );
}
