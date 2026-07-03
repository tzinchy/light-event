"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ClipboardList, Loader2 } from "lucide-react";
import {
  listTestsApiV1TestsGet,
  type TestListItemOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";
import { formatCooldownLeft } from "@/lib/attempt";
import { cn } from "@/lib/utils";

function TestRow({ test }: { test: TestListItemOut }) {
  const router = useRouter();
  // тикаем раз в секунду, пока идёт cooldown («Повтор через 14:59»)
  const [cooldownLeft, setCooldownLeft] = useState<string | null>(
    test.cooldown_until ? formatCooldownLeft(test.cooldown_until) : null,
  );

  useEffect(() => {
    if (!test.cooldown_until) return;
    const id = setInterval(
      () => setCooldownLeft(formatCooldownLeft(test.cooldown_until!)),
      1000,
    );
    return () => clearInterval(id);
  }, [test.cooldown_until]);

  const result = test.my_result;
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">{test.title}</span>
          {test.kind === "company" && (
            <span className="status-badge border-status-violet-border bg-status-violet-bg text-status-violet">
              {DICT.companyTest}
            </span>
          )}
        </div>
        <div className="mt-0.5 text-sm text-muted-foreground">
          {test.topic}
          {test.company_name ? ` · ${test.company_name}` : ""} · {test.questions_count}{" "}
          {DICT.questionsShort}
        </div>
        {result && (
          <div
            className={cn(
              "mt-2 text-sm font-semibold",
              result.passed ? "text-brand-strong" : "text-status-danger",
            )}
          >
            {result.passed ? DICT.testPassed : DICT.testNotPassed} · {result.score_pct}%
          </div>
        )}
        <Button
          className="mt-3 w-full"
          variant={result?.passed ? "outline" : "default"}
          disabled={cooldownLeft !== null}
          onClick={() => router.push(`/tests/${test.test_uuid}`)}
        >
          {cooldownLeft !== null
            ? `${DICT.retryIn} ${cooldownLeft}`
            : result
              ? DICT.retakeTest
              : DICT.startTest}
        </Button>
      </CardContent>
    </Card>
  );
}

export default function TestsPage() {
  const router = useRouter();
  const { me, loading } = useAuth();
  const [tests, setTests] = useState<TestListItemOut[] | null>(null);

  useEffect(() => {
    if (!loading && !me) router.replace("/auth");
  }, [loading, me, router]);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await listTestsApiV1TestsGet();
      setTests(data ?? []);
    })();
  }, [me]);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <h1 className="text-xl font-semibold">{DICT.testsTab}</h1>

        {tests === null ? (
          <div className="mt-16 flex justify-center text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
          </div>
        ) : tests.length === 0 ? (
          <div className="mt-16 flex flex-col items-center text-center text-muted-foreground">
            <ClipboardList className="size-8" />
            <p className="mt-3 text-sm">{DICT.noTests}</p>
          </div>
        ) : (
          <div className="mt-4 space-y-3">
            {tests.map((test) => (
              <TestRow key={test.test_uuid} test={test} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
