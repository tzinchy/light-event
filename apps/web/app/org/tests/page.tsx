"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { ClipboardList, Loader2, Plus, Trash2 } from "lucide-react";
import {
  companyTestsApiV1CompaniesCompanyUuidTestsGet,
  createCompanyTestApiV1CompaniesCompanyUuidTestsPost,
  type CompanyTestItemOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { DICT } from "@/lib/dict";
import { useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";

const TEST_STATUS: Record<string, { label: string; className: string }> = {
  pending_moderation: {
    label: DICT.evPending,
    className: "border-status-warn-border bg-status-warn-bg text-status-warn",
  },
  published: {
    label: DICT.testPublished,
    className: "border-brand-border bg-brand-soft text-brand-strong",
  },
  rejected: {
    label: DICT.evRejected,
    className: "border-status-danger-border bg-status-danger-bg text-status-danger",
  },
};

type QuestionDraft = {
  text: string;
  multi: boolean;
  options: string[];
  correct: number[];
};

const emptyQuestion = (): QuestionDraft => ({ text: "", multi: false, options: ["", ""], correct: [] });

function questionValid(q: QuestionDraft): boolean {
  return (
    q.text.trim().length >= 5 &&
    q.options.length >= 2 &&
    q.options.every((o) => o.trim().length > 0) &&
    q.correct.length >= 1 &&
    (q.multi || q.correct.length === 1)
  );
}

function CreateTestForm({
  companyUuid,
  onCreated,
  onCancel,
}: {
  companyUuid: string;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [minCorrect, setMinCorrect] = useState(1);
  const [questions, setQuestions] = useState<QuestionDraft[]>([emptyQuestion()]);
  const [busy, setBusy] = useState(false);

  const patchQuestion = (qi: number, patch: Partial<QuestionDraft>) =>
    setQuestions(questions.map((q, i) => (i === qi ? { ...q, ...patch } : q)));

  const valid =
    title.trim().length >= 2 &&
    topic.trim().length >= 2 &&
    minCorrect >= 1 &&
    minCorrect <= questions.length &&
    questions.every(questionValid);

  async function submit() {
    setBusy(true);
    const { data, error, response } = await createCompanyTestApiV1CompaniesCompanyUuidTestsPost({
      path: { company_uuid: companyUuid },
      body: {
        title: title.trim(),
        topic: topic.trim(),
        min_correct: minCorrect,
        questions: questions.map((q) => ({
          text: q.text.trim(),
          multi: q.multi,
          options: q.options.map((o) => o.trim()),
          correct_indices: q.correct,
        })),
      },
    });
    setBusy(false);
    if (data) {
      toast.success(DICT.testSentToModeration);
      onCreated();
    } else {
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      toast.error(typeof detail === "string" ? detail : `Ошибка (${response.status})`);
    }
  }

  return (
    <Card className="mt-4">
      <CardHeader>
        <CardTitle>
          {DICT.createTest} — {DICT.testCost}
        </CardTitle>
        <p className="text-sm text-muted-foreground">{DICT.feeNote}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="test-title">Название</Label>
            <Input
              id="test-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Стандарты сервиса"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="test-topic">Тема</Label>
            <Input
              id="test-topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Официант"
            />
          </div>
        </div>

        {questions.map((q, qi) => (
          <Card key={qi} className="bg-secondary/30">
            <CardContent className="space-y-3 pt-6">
              <div className="flex items-center justify-between gap-2">
                <Label htmlFor={`q-${qi}`}>
                  {DICT.testQ} {qi + 1}
                </Label>
                {questions.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-status-danger"
                    onClick={() => {
                      setQuestions(questions.filter((_, i) => i !== qi));
                      setMinCorrect((m) => Math.min(m, questions.length - 1));
                    }}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                )}
              </div>
              <Input
                id={`q-${qi}`}
                value={q.text}
                onChange={(e) => patchQuestion(qi, { text: e.target.value })}
                placeholder={DICT.questionText}
              />
              <div className="flex items-center gap-2">
                <Switch
                  id={`multi-${qi}`}
                  checked={q.multi}
                  onCheckedChange={(multi) =>
                    patchQuestion(qi, { multi, correct: q.correct.slice(0, multi ? undefined : 1) })
                  }
                />
                <Label htmlFor={`multi-${qi}`} className="font-normal">
                  {DICT.multiToggle}
                </Label>
              </div>
              <p className="text-xs text-muted-foreground">{DICT.markCorrectHint}</p>
              {q.options.map((option, oi) => (
                <div key={oi} className="flex items-center gap-2">
                  <Checkbox
                    checked={q.correct.includes(oi)}
                    onCheckedChange={(on) =>
                      patchQuestion(qi, {
                        correct: on
                          ? q.multi
                            ? [...q.correct, oi].sort((a, b) => a - b)
                            : [oi]
                          : q.correct.filter((i) => i !== oi),
                      })
                    }
                  />
                  <Input
                    value={option}
                    onChange={(e) =>
                      patchQuestion(qi, {
                        options: q.options.map((o, i) => (i === oi ? e.target.value : o)),
                      })
                    }
                    placeholder={`Вариант ${oi + 1}`}
                  />
                  {q.options.length > 2 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        patchQuestion(qi, {
                          options: q.options.filter((_, i) => i !== oi),
                          correct: q.correct
                            .filter((i) => i !== oi)
                            .map((i) => (i > oi ? i - 1 : i)),
                        })
                      }
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  )}
                </div>
              ))}
              {q.options.length < 8 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => patchQuestion(qi, { options: [...q.options, ""] })}
                >
                  <Plus className="size-4" />
                  {DICT.addOption}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}

        <div className="flex flex-wrap items-end justify-between gap-4">
          <Button
            variant="outline"
            disabled={questions.length >= 50}
            onClick={() => setQuestions([...questions, emptyQuestion()])}
          >
            <Plus className="size-4" />
            {DICT.addQuestion}
          </Button>
          <div className="space-y-1.5">
            <Label htmlFor="min-correct">{DICT.minCorrectLabel}</Label>
            <Input
              id="min-correct"
              type="number"
              min={1}
              max={questions.length}
              value={minCorrect}
              onChange={(e) => setMinCorrect(Number(e.target.value))}
              className="w-24"
            />
          </div>
        </div>

        <div className="flex gap-2 border-t pt-4">
          <Button disabled={!valid || busy} onClick={() => void submit()}>
            {busy && <Loader2 className="size-4 animate-spin" />}
            {DICT.payAndPublish} · {DICT.testCost}
          </Button>
          <Button variant="ghost" onClick={onCancel}>
            Отмена
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function OrgTestsPage() {
  const { current, loading } = useOrg();
  const [tests, setTests] = useState<CompanyTestItemOut[] | null>(null);
  const [creating, setCreating] = useState(false);

  const reload = useCallback(async () => {
    if (!current) return;
    const { data } = await companyTestsApiV1CompaniesCompanyUuidTestsGet({
      path: { company_uuid: current.company.company_uuid },
    });
    setTests(data ?? []);
  }, [current]);

  useEffect(() => {
    void reload();
  }, [reload]);

  if (loading || (current && tests === null)) {
    return (
      <div className="flex justify-center py-16 text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  if (!current) return null;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">{DICT.orgTestsTitle}</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">{DICT.orgTestsSub}</p>
        </div>
        {!creating && (
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" />
            {DICT.createTest} — {DICT.testCost}
          </Button>
        )}
      </div>

      {creating && (
        <CreateTestForm
          companyUuid={current.company.company_uuid}
          onCreated={() => {
            setCreating(false);
            void reload();
          }}
          onCancel={() => setCreating(false)}
        />
      )}

      {tests !== null && tests.length === 0 && !creating ? (
        <div className="mt-16 flex flex-col items-center text-center text-muted-foreground">
          <ClipboardList className="size-8" />
          <p className="mt-3 max-w-sm text-sm">{DICT.noOrgTests}</p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {(tests ?? []).map((test) => {
            const status = TEST_STATUS[test.status] ?? { label: test.status, className: "" };
            return (
              <Card key={test.test_uuid}>
                <CardContent className="flex flex-wrap items-center gap-3 pt-6">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{test.title}</span>
                      <span className={cn("status-badge", status.className)}>{status.label}</span>
                    </div>
                    <div className="mt-0.5 text-sm text-muted-foreground">
                      {test.topic} · {test.questions_count} {DICT.questionsShort}
                    </div>
                    {test.status === "rejected" && test.reject_reason && (
                      <div className="mt-1 text-sm text-status-danger">{test.reject_reason}</div>
                    )}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {test.passed_count > 0
                      ? `${test.passed_count} ${DICT.passedCountWord}`
                      : DICT.noTakenYet}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
