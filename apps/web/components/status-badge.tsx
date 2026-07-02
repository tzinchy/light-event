import { DICT } from "@/lib/dict";
import { cn } from "@/lib/utils";

const STATUS: Record<string, { label: string; className: string }> = {
  draft: {
    label: DICT.evDraft,
    className: "border-status-warn-border bg-status-warn-bg text-status-warn",
  },
  pending_moderation: {
    label: DICT.evPending,
    className: "border-status-warn-border bg-status-warn-bg text-status-warn",
  },
  active: {
    label: DICT.evActive,
    className: "border-brand-border bg-brand-soft text-brand-strong",
  },
  rejected: {
    label: DICT.evRejected,
    className: "border-status-danger-border bg-status-danger-bg text-status-danger",
  },
  done: {
    label: DICT.evDone,
    className: "border-border bg-secondary text-muted-foreground",
  },
  archived: {
    label: DICT.evArchived,
    className: "border-border bg-secondary text-muted-foreground",
  },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: status, className: "border-border bg-secondary" };
  return <span className={cn("status-badge", s.className)}>{s.label}</span>;
}
