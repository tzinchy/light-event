"use client";

import { useEffect, useState } from "react";
import { Loader2, Star } from "lucide-react";
import {
  companyReviewsApiV1CompaniesCompanyUuidReviewsGet,
  type ReviewListOut,
} from "@light-event/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { useOrg } from "@/lib/org-context";
import { formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

const KIND_LABEL: Record<string, string> = {
  about_org: "Об организации",
  about_event: "О событии",
};

function Stars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`Оценка ${rating} из 5`}>
      {[1, 2, 3, 4, 5].map((value) => (
        <Star
          key={value}
          className={cn(
            "size-4",
            value <= rating ? "fill-amber-400 text-amber-400" : "text-muted-foreground/30",
          )}
        />
      ))}
    </div>
  );
}

export default function OrgReviewsPage() {
  const { current } = useOrg();
  const [data, setData] = useState<ReviewListOut | null>(null);

  const companyUuid = current?.company.company_uuid;

  useEffect(() => {
    if (!companyUuid) return;
    void (async () => {
      const resp = await companyReviewsApiV1CompaniesCompanyUuidReviewsGet({
        path: { company_uuid: companyUuid },
      });
      setData(resp.data ?? { avg_rating: null, count: 0, items: [] });
    })();
  }, [companyUuid]);

  if (!companyUuid) return null;

  if (data === null) {
    return (
      <div className="mt-16 flex justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Отзывы</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Что соискатели пишут о вашей организации и событиях.
          </p>
        </div>
        {data.avg_rating !== null && (
          <div className="flex items-center gap-2">
            <Stars rating={Math.round(data.avg_rating)} />
            <span className="font-mono text-lg font-semibold">{data.avg_rating.toFixed(1)}</span>
            <span className="text-sm text-muted-foreground">· {data.count}</span>
          </div>
        )}
      </div>

      <div className="mt-6 space-y-3">
        {data.items.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              Пока нет отзывов: они появляются после выплат соискателям.
            </CardContent>
          </Card>
        ) : (
          data.items.map((review) => (
            <Card key={review.review_uuid}>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between gap-3">
                  <Stars rating={review.rating} />
                  <span className="text-xs text-muted-foreground">
                    {KIND_LABEL[review.kind] ?? review.kind} · {formatDate(review.created_at)}
                  </span>
                </div>
                {review.text && <p className="mt-2 text-sm">{review.text}</p>}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
