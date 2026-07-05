import { Star } from "lucide-react";
import type { ReviewListOut } from "@light-event/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { formatDateTime } from "@/lib/format";

export function RatingStars({ value, className }: { value: number; className?: string }) {
  return (
    <span className={className}>
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          className={`inline size-4 ${n <= Math.round(value) ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30"}`}
        />
      ))}
    </span>
  );
}

/** Список отзывов с средним рейтингом — общий для профиля компании и исполнителя. */
export function ReviewList({ data, emptyText }: { data: ReviewListOut; emptyText: string }) {
  if (data.count === 0) {
    return <p className="py-8 text-center text-sm text-muted-foreground">{emptyText}</p>;
  }
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold">{data.avg_rating?.toFixed(1)}</span>
        <RatingStars value={data.avg_rating ?? 0} />
        <span className="text-sm text-muted-foreground">· {data.count} отз.</span>
      </div>
      {data.items.map((r) => (
        <Card key={r.review_uuid}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <RatingStars value={r.rating} />
              <span className="text-xs text-muted-foreground">{formatDateTime(r.created_at)}</span>
            </div>
            {r.text && <p className="mt-2 text-sm">{r.text}</p>}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
