import Link from "next/link";
import {
  BadgeCheck,
  CalendarClock,
  MessagesSquare,
  ShieldCheck,
  Star,
  Zap,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FeedPreview } from "@/components/feed-preview";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";

const workerSteps = [
  {
    icon: BadgeCheck,
    title: "Создайте профиль",
    text: "Телефон, паспорт и медкнижка — верификация онлайн за несколько минут.",
  },
  {
    icon: CalendarClock,
    title: "Выбирайте смены",
    text: "Лента смен рядом с вами: ставка в час, требования и адрес сразу в карточке.",
  },
  {
    icon: Zap,
    title: "Работайте и получайте выплаты",
    text: "Подтверждение в чате, честный расчёт после смены и рейтинг за каждую работу.",
  },
];

const features = [
  {
    icon: Zap,
    title: "Отклик в один тап",
    text: "Никаких резюме и собеседований — рейтинг и подтверждённые документы говорят сами за себя.",
  },
  {
    icon: ShieldCheck,
    title: "Проверенные профили",
    text: "Паспорт и медкнижка каждого сотрудника проходят модерацию платформы.",
  },
  {
    icon: Star,
    title: "Рейтинг и отзывы",
    text: "Обе стороны оценивают друг друга после каждой смены — качество видно сразу.",
  },
  {
    icon: MessagesSquare,
    title: "Чат по заявке",
    text: "Детали смены, форма одежды и вход для персонала — всё в одном треде.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />

      <main className="flex-1">
        {/* hero */}
        <section className="mx-auto w-full max-w-6xl px-4 pb-16 pt-20 text-center">
          <Badge
            variant="outline"
            className="mb-6 border-brand-border bg-brand-soft text-brand-strong"
          >
            <span className="mr-1 inline-block size-1.5 animate-pulse rounded-full bg-brand" />
            {DICT.heroBadge}
          </Badge>
          <h1 className="mx-auto max-w-3xl text-balance text-4xl font-bold tracking-tight sm:text-5xl">
            {DICT.heroH1}
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-pretty text-muted-foreground">
            {DICT.heroSub}
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/auth">{DICT.ctaWorker}</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/auth">{DICT.ctaOrg}</Link>
            </Button>
          </div>
        </section>

        <FeedPreview />

        {/* как это работает */}
        <section className="border-t bg-card">
          <div className="mx-auto w-full max-w-6xl px-4 py-16">
            <h2 className="text-center text-2xl font-semibold">{DICT.howItWorks}</h2>
            <div className="mt-10 grid gap-4 sm:grid-cols-3">
              {workerSteps.map((step, i) => (
                <Card key={step.title}>
                  <CardContent className="pt-6">
                    <div className="mb-4 flex size-10 items-center justify-center rounded-xl bg-brand-soft text-brand-strong">
                      <step.icon className="size-5" />
                    </div>
                    <div className="text-sm font-medium text-muted-foreground">
                      Шаг {i + 1}
                    </div>
                    <h3 className="mt-1 font-semibold">{step.title}</h3>
                    <p className="mt-2 text-sm text-muted-foreground">{step.text}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* сотрудникам / организациям */}
        <section className="mx-auto w-full max-w-6xl px-4 py-16">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardContent className="pt-6">
                <Badge variant="secondary" className="mb-3">
                  {DICT.forWorkers}
                </Badge>
                <h3 className="text-xl font-semibold">{DICT.workerPitch}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{DICT.workerPitchSub}</p>
                <Button asChild className="mt-6" variant="outline">
                  <Link href="/auth">{DICT.ctaWorker}</Link>
                </Button>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <Badge variant="secondary" className="mb-3">
                  {DICT.forOrg}
                </Badge>
                <h3 className="text-xl font-semibold">{DICT.orgPitch}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{DICT.orgPitchSub}</p>
                <Button asChild className="mt-6" variant="outline">
                  <Link href="/auth">{DICT.openOrgConsole}</Link>
                </Button>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* фичи */}
        <section className="border-t bg-card">
          <div className="mx-auto w-full max-w-6xl px-4 py-16">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((f) => (
                <div key={f.title}>
                  <div className="mb-3 flex size-9 items-center justify-center rounded-lg bg-secondary">
                    <f.icon className="size-4" />
                  </div>
                  <h3 className="text-sm font-semibold">{f.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{f.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA-band */}
        <section className="mx-auto w-full max-w-6xl px-4 py-16">
          <div className="rounded-2xl bg-primary px-6 py-12 text-center text-primary-foreground">
            <h2 className="text-2xl font-semibold">{DICT.ctaBandTitle}</h2>
            <p className="mx-auto mt-2 max-w-xl text-sm opacity-80">{DICT.ctaBandSub}</p>
            <Button asChild size="lg" variant="secondary" className="mt-6">
              <Link href="/auth">{DICT.signUpFree}</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-6 text-sm text-muted-foreground">
          <span>light-event</span>
          <span>{DICT.footNote}</span>
        </div>
      </footer>
    </div>
  );
}
