import Link from "next/link";
import { MapPin, Zap } from "lucide-react";
import type { FeedItemOut } from "@light-event/shared-types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { DICT } from "@/lib/dict";
import { formatShiftWindow, kopToRub } from "@/lib/format";

export function ShiftCard({ shift }: { shift: FeedItemOut }) {
  return (
    <Link href={`/shift/${shift.vacancy_uuid}`}>
      <Card className="transition-colors hover:bg-secondary/50">
        <CardContent className="pt-6">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{shift.role_name}</span>
                {shift.urgent && (
                  <span className="status-badge border-status-danger-border bg-status-danger-bg text-status-danger">
                    <Zap className="size-3" />
                    {DICT.urgent}
                  </span>
                )}
              </div>
              <div className="mt-0.5 truncate text-sm text-muted-foreground">
                {shift.company_name} · {shift.event_title}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="font-mono font-semibold">
                {kopToRub(shift.pay_hour_kop)}
                <span className="text-xs font-normal text-muted-foreground">{DICT.perHour}</span>
              </div>
              <div className="text-xs text-muted-foreground">
                {kopToRub(shift.pay_total_kop)} {DICT.total}
              </div>
            </div>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
            <span>{formatShiftWindow(shift.starts_at, shift.ends_at)}</span>
            <span className="flex items-center gap-1">
              <MapPin className="size-3.5" />
              {shift.venue_address}
            </span>
          </div>
          {shift.tags.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {shift.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="font-normal">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}
