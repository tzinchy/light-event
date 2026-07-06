"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import {
  userReviewsApiV1UsersUserUuidReviewsGet,
  workerPublicProfileApiV1UsersUserUuidPublicGet,
  type ReviewListOut,
  type WorkerPublicOut,
} from "@light-event/shared-types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { ReviewList } from "@/components/review-list";
import { EDUCATION_LABEL, ENGLISH_LABEL, EXPERIENCE_LABEL } from "@/lib/experience";

export default function WorkerProfilePage() {
  const { uuid } = useParams<{ uuid: string }>();
  const [worker, setWorker] = useState<WorkerPublicOut | null>(null);
  const [reviews, setReviews] = useState<ReviewListOut | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    void (async () => {
      const [w, r] = await Promise.all([
        workerPublicProfileApiV1UsersUserUuidPublicGet({ path: { user_uuid: uuid } }),
        userReviewsApiV1UsersUserUuidReviewsGet({ path: { user_uuid: uuid } }),
      ]);
      if (!w.data) setNotFound(true);
      else setWorker(w.data);
      setReviews(r.data ?? null);
    })();
  }, [uuid]);

  if (notFound) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-16 text-center text-muted-foreground">
          Профиль не найден
        </main>
      </div>
    );
  }

  if (!worker || !reviews) {
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
          <div className="flex size-14 shrink-0 items-center justify-center rounded-full bg-secondary text-lg font-semibold uppercase">
            {(worker.name ?? "?").slice(0, 2)}
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-xl font-bold">{worker.name ?? "Соискатель"}</h1>
            <div className="mt-0.5 text-sm text-muted-foreground">
              {worker.city ?? "Город не указан"}
              {worker.experience ? ` · Опыт: ${EXPERIENCE_LABEL[worker.experience] ?? worker.experience}` : ""}
            </div>
          </div>
        </div>

        {worker.about && (
          <Card className="mt-5">
            <CardContent className="pt-5">
              <div className="text-sm font-medium">О себе</div>
              <p className="mt-1 whitespace-pre-line text-sm text-muted-foreground">{worker.about}</p>
            </CardContent>
          </Card>
        )}

        {(worker.english_level || worker.education) && (
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            {worker.english_level && (
              <div>
                <span className="text-muted-foreground">Английский: </span>
                {ENGLISH_LABEL[worker.english_level] ?? worker.english_level}
              </div>
            )}
            {worker.education && (
              <div>
                <span className="text-muted-foreground">Образование: </span>
                {EDUCATION_LABEL[worker.education] ?? worker.education}
              </div>
            )}
          </div>
        )}

        {worker.desired_roles.length > 0 && (
          <div className="mt-5">
            <div className="text-sm font-medium">Желаемые роли</div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {worker.desired_roles.map((role) => (
                <Badge key={role} variant="secondary" className="font-normal">
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <section className="mt-8">
          <h2 className="mb-3 font-semibold">Отзывы</h2>
          <ReviewList data={reviews} emptyText="Пока нет отзывов" />
        </section>

        <p className="mt-8 text-xs text-muted-foreground">
          Связь с соискателем — только через платформу (чат по заявке). Контактные данные не раскрываются.
        </p>
      </main>
    </div>
  );
}
