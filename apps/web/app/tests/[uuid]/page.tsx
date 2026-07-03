"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Check, Loader2, X } from "lucide-react";
import {
  abandonAttemptApiV1AttemptsAttemptUuidAbandonPost,
  answerApiV1AttemptsAttemptUuidAnswersPost,
  finishAttemptApiV1AttemptsAttemptUuidFinishPost,
  startAttemptApiV1TestsTestUuidAttemptsPost,
  type AttemptOut,
  type AttemptWithQuestionsOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";
import { SiteHeader } from "@/components/site-header";
import { DICT } from "@/lib/dict";
import { toggleChoice } from "@/lib/attempt";
import { cn } from "@/lib/utils";

function ResultScreen({ result }: { result: AttemptOut }) {
  return (
    <div className="mt-16 flex flex-col items-center text-center">
      <h1 className="text-xl font-semibold">{DICT.testResult}</h1>
      <div
        className={cn(
          "mt-8 flex size-32 items-center justify-center rounded-full border-[6px] text-3xl font-semibold",
          result.passed
            ? "border-brand text-brand-strong"
            : "border-status-danger text-status-danger",
        )}
      >
        {result.score_pct}%
      </div>
      <div
        className={cn(
          "mt-4 text-lg font-semibold",
          result.passed ? "text-brand-strong" : "text-status-danger",
        )}
      >
        {result.passed ? DICT.testPassed : DICT.testNotPassed}
      </div>
      <p className="mt-1 text-sm text-muted-foreground">{DICT.yourScore}</p>
      <Button asChild className="mt-8 w-full max-w-xs">
        <Link href="/tests">{DICT.backToTests}</Link>
      </Button>
    </div>
  );
}

export default function TestAttemptPage() {
  const { uuid } = useParams<{ uuid: string }>();
  const router = useRouter();
  const [attempt, setAttempt] = useState<AttemptWithQuestionsOut | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const [qIndex, setQIndex] = useState(0);
  const [chosen, setChosen] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const [exitOpen, setExitOpen] = useState(false);
  const [result, setResult] = useState<AttemptOut | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // strict mode вызывает эффект дважды — попытка одна
    started.current = true;
    void (async () => {
      const { data, error, response } = await startAttemptApiV1TestsTestUuidAttemptsPost({
        path: { test_uuid: uuid },
      });
      if (data) {
        setAttempt(data);
      } else {
        const detail = (error as { detail?: unknown } | undefined)?.detail;
        setStartError(
          typeof detail === "string" ? detail : `Не удалось начать тест (${response.status})`,
        );
      }
    })();
  }, [uuid]);

  if (startError) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <main className="mx-auto w-full max-w-xl flex-1 px-4 py-16 text-center">
          <p className="text-sm text-muted-foreground">{startError}</p>
          <Button asChild variant="outline" className="mt-6">
            <Link href="/tests">{DICT.backToTests}</Link>
          </Button>
        </main>
      </div>
    );
  }

  if (!attempt) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <main className="mx-auto flex w-full max-w-xl flex-1 items-center justify-center">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </main>
      </div>
    );
  }

  if (result) {
    return (
      <div className="flex min-h-screen flex-col">
        <SiteHeader />
        <main className="mx-auto w-full max-w-xl flex-1 px-4 py-8">
          <ResultScreen result={result} />
        </main>
      </div>
    );
  }

  const questions = attempt.questions;
  const question = questions[qIndex];
  const isLast = qIndex === questions.length - 1;

  async function submitAnswer() {
    setBusy(true);
    await answerApiV1AttemptsAttemptUuidAnswersPost({
      path: { attempt_uuid: attempt!.test_attempt_uuid },
      body: { test_question_uuid: question.test_question_uuid, selected_indices: chosen },
    });
    if (isLast) {
      const { data } = await finishAttemptApiV1AttemptsAttemptUuidFinishPost({
        path: { attempt_uuid: attempt!.test_attempt_uuid },
      });
      setResult(data ?? null);
    } else {
      setQIndex(qIndex + 1);
      setChosen([]);
    }
    setBusy(false);
  }

  async function abandon() {
    await abandonAttemptApiV1AttemptsAttemptUuidAbandonPost({
      path: { attempt_uuid: attempt!.test_attempt_uuid },
    });
    router.replace("/tests");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-xl flex-1 px-4 py-8">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {DICT.testQ} {qIndex + 1} {DICT.ofWord} {questions.length}
          </span>
          <Button variant="ghost" size="sm" onClick={() => setExitOpen(true)}>
            <X className="size-4" />
          </Button>
        </div>
        <Progress className="mt-2" value={(qIndex / questions.length) * 100} />

        <Card className="mt-6">
          <CardContent className="pt-6">
            <h1 className="font-semibold">{question.text}</h1>
            {question.multi && (
              <p className="mt-1 text-xs text-muted-foreground">{DICT.multiHint}</p>
            )}
            <div className="mt-4 space-y-2">
              {question.options.map((option, i) => {
                const on = chosen.includes(i);
                return (
                  <button
                    key={i}
                    type="button"
                    className={cn(
                      "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left text-sm transition-colors",
                      on
                        ? "border-primary bg-secondary/50 font-medium"
                        : "border-border hover:bg-secondary/30",
                    )}
                    onClick={() => setChosen(toggleChoice(chosen, i, question.multi))}
                  >
                    <span
                      className={cn(
                        "flex size-5 shrink-0 items-center justify-center border text-primary-foreground",
                        question.multi ? "rounded-md" : "rounded-full",
                        on ? "border-primary bg-primary" : "border-border bg-background",
                      )}
                    >
                      {on && <Check className="size-3" />}
                    </span>
                    {option}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Button
          className="mt-6 w-full"
          size="lg"
          disabled={chosen.length === 0 || busy}
          onClick={() => void submitAnswer()}
        >
          {busy && <Loader2 className="size-4 animate-spin" />}
          {isLast ? DICT.finishTest : DICT.next}
        </Button>
      </main>

      <Dialog open={exitOpen} onOpenChange={setExitOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{DICT.exitTestConfirm}</DialogTitle>
            <DialogDescription>{DICT.cooldownNote}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExitOpen(false)}>
              {DICT.stay}
            </Button>
            <Button variant="destructive" onClick={() => void abandon()}>
              {DICT.exit}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
