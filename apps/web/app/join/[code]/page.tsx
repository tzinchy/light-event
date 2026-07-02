"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2, UserPlus } from "lucide-react";
import { acceptInviteApiV1InvitesCodeAcceptPost } from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { DICT } from "@/lib/dict";

export default function JoinPage() {
  const { code } = useParams<{ code: string }>();
  const router = useRouter();
  const { me, loading } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function accept() {
    setBusy(true);
    setError(null);
    const { error: apiError } = await acceptInviteApiV1InvitesCodeAcceptPost({
      path: { code },
    });
    setBusy(false);
    if (apiError) {
      setError(String((apiError as { detail?: string }).detail ?? "Ссылка недействительна"));
      return;
    }
    router.replace("/org");
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-4">
      <Card>
        <CardContent className="pt-6 text-center">
          <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-xl bg-brand-soft text-brand-strong">
            <UserPlus className="size-6" />
          </div>
          <h1 className="text-lg font-semibold">Приглашение в команду</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Вас пригласили в кабинет организации на light-event. Вступив, вы получите роль,
            указанную в приглашении.
          </p>

          {error && (
            <p className="mt-4 rounded-lg border border-status-danger-border bg-status-danger-bg px-3 py-2 text-sm text-status-danger">
              {error}
            </p>
          )}

          {loading ? (
            <Loader2 className="mx-auto mt-6 size-5 animate-spin text-muted-foreground" />
          ) : me ? (
            <Button className="mt-6 w-full" disabled={busy} onClick={() => void accept()}>
              {busy && <Loader2 className="size-4 animate-spin" />}
              Вступить в команду
            </Button>
          ) : (
            <>
              <p className="mt-4 text-sm text-muted-foreground">
                Сначала войдите — затем откройте ссылку ещё раз.
              </p>
              <Button asChild className="mt-4 w-full">
                <Link href="/auth">{DICT.signIn}</Link>
              </Button>
            </>
          )}
        </CardContent>
      </Card>
      <Link href="/" className="mt-6 text-center text-sm text-muted-foreground underline">
        {DICT.backHome}
      </Link>
    </div>
  );
}
