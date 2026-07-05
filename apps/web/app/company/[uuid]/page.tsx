"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { CalendarDays, Heart, Loader2, MapPin } from "lucide-react";
import {
  companyReviewsApiV1CompaniesCompanyUuidReviewsGet,
  feedApiV1VacanciesGet,
  followApiV1CompaniesCompanyUuidFavoritePost,
  getCompanyApiV1CompaniesCompanyUuidGet,
  myFavoritesApiV1FavoritesCompaniesGet,
  unfollowApiV1CompaniesCompanyUuidFavoriteDelete,
  type CompanyOut,
  type FeedItemOut,
  type ReviewListOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { RatingStars, ReviewList } from "@/components/review-list";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { formatDateTime, kopToRub } from "@/lib/format";

export default function CompanyProfilePage() {
  const { uuid } = useParams<{ uuid: string }>();
  const { me } = useAuth();
  const [company, setCompany] = useState<CompanyOut | null>(null);
  const [events, setEvents] = useState<FeedItemOut[] | null>(null);
  const [reviews, setReviews] = useState<ReviewListOut | null>(null);
  const [isFav, setIsFav] = useState(false);

  useEffect(() => {
    void (async () => {
      const [c, ev, rv] = await Promise.all([
        getCompanyApiV1CompaniesCompanyUuidGet({ path: { company_uuid: uuid } }),
        feedApiV1VacanciesGet({ query: { company_uuid: uuid } }),
        companyReviewsApiV1CompaniesCompanyUuidReviewsGet({ path: { company_uuid: uuid } }),
      ]);
      setCompany(c.data ?? null);
      setEvents(ev.data ?? []);
      setReviews(rv.data ?? null);
    })();
  }, [uuid]);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await myFavoritesApiV1FavoritesCompaniesGet();
      setIsFav((data ?? []).some((c) => c.company_uuid === uuid));
    })();
  }, [me, uuid]);

  async function toggleFav() {
    const next = !isFav;
    setIsFav(next);
    if (next) {
      await followApiV1CompaniesCompanyUuidFavoritePost({ path: { company_uuid: uuid } });
    } else {
      await unfollowApiV1CompaniesCompanyUuidFavoriteDelete({ path: { company_uuid: uuid } });
    }
  }

  if (!company || events === null || !reviews) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <div className="flex items-center gap-4">
          <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-primary text-lg font-bold text-primary-foreground">
            {company.name.slice(0, 2).toUpperCase()}
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-xl font-bold">{company.name}</h1>
            <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
              {reviews.count > 0 ? (
                <>
                  <RatingStars value={reviews.avg_rating ?? 0} />
                  <span>{reviews.avg_rating?.toFixed(1)} · {reviews.count} отз.</span>
                </>
              ) : (
                <span>Пока без отзывов</span>
              )}
            </div>
            <div className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
              <MapPin className="size-3.5" />
              {company.address}
            </div>
          </div>
          {me && (
            <Button
              variant={isFav ? "default" : "outline"}
              size="sm"
              className="ml-auto shrink-0"
              onClick={() => void toggleFav()}
            >
              <Heart className={cn("size-4", isFav && "fill-current")} />
              {isFav ? "В избранном" : "В избранное"}
            </Button>
          )}
        </div>
        {me && (
          <p className="mt-2 text-xs text-muted-foreground">
            Избранные компании присылают уведомление о каждой новой смене.
          </p>
        )}

        {company.description && <p className="mt-5 text-sm text-muted-foreground">{company.description}</p>}

        <section className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 font-semibold">
            <CalendarDays className="size-4" />
            Активные события
          </h2>
          {events.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">Сейчас нет открытых смен</p>
          ) : (
            <div className="space-y-2">
              {events.map((v) => (
                <Link key={v.vacancy_uuid} href={`/shift/${v.vacancy_uuid}`}>
                  <Card className="transition-colors hover:bg-secondary">
                    <CardContent className="flex items-center justify-between gap-3 py-4">
                      <div className="min-w-0">
                        <div className="truncate font-medium">{v.event_title}</div>
                        <div className="truncate text-sm text-muted-foreground">
                          {v.role_name} · {formatDateTime(v.starts_at)}
                        </div>
                      </div>
                      <div className="shrink-0 text-sm font-semibold">{kopToRub(v.pay_hour_kop)}/ч</div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </section>

        <section className="mt-8">
          <h2 className="mb-3 font-semibold">Отзывы</h2>
          <ReviewList data={reviews} emptyText="Отзывов пока нет" />
        </section>
      </main>
    </div>
  );
}
