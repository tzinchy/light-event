"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BadgeCheck, Loader2, Mail } from "lucide-react";
import {
  confirmEmailApiV1UsersMeEmailConfirmPost,
  requestEmailCodeApiV1UsersMeEmailPost,
  updateMeApiV1UsersMePatch,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OtpInput, OTP_LENGTH } from "@/components/otp-input";
import { SiteHeader } from "@/components/site-header";
import { useAuth } from "@/lib/auth-context";

function EmailBlock() {
  const { me, refreshMe } = useAuth();
  const [email, setEmail] = useState(me?.email ?? "");
  const [stage, setStage] = useState<"idle" | "code">("idle");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  const verified = Boolean(me?.email_verified_at) && email === me?.email;
  const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  async function requestCode() {
    setBusy(true);
    const { error } = await requestEmailCodeApiV1UsersMeEmailPost({ body: { email } });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось отправить код"));
      return;
    }
    toast.success("Код отправлен на почту");
    setCode("");
    setStage("code");
  }

  async function confirm() {
    setBusy(true);
    const { error } = await confirmEmailApiV1UsersMeEmailConfirmPost({ body: { code } });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Неверный код"));
      return;
    }
    toast.success("Почта подтверждена");
    setStage("idle");
    await refreshMe();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Mail className="size-4" />
          Почта
          {verified && (
            <span className="ml-auto flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
              <BadgeCheck className="size-3.5" />
              Подтверждена
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Label htmlFor="profile-email">Адрес электронной почты</Label>
        <div className="mt-1.5 flex gap-2">
          <Input
            id="profile-email"
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value.trim());
              setStage("idle");
            }}
            placeholder="mail@example.ru"
          />
          <Button
            variant={verified ? "outline" : "default"}
            disabled={!emailOk || busy || verified}
            onClick={() => void requestCode()}
          >
            {busy && stage === "idle" && <Loader2 className="size-4 animate-spin" />}
            {verified ? "Подтверждена" : "Получить код"}
          </Button>
        </div>

        {stage === "code" && (
          <div className="mt-4">
            <p className="mb-2 text-sm text-muted-foreground">
              Введите код из письма — он действует 5 минут
            </p>
            <OtpInput value={code} onChange={setCode} disabled={busy} />
            <Button
              className="mt-3 w-full"
              disabled={code.length !== OTP_LENGTH || busy}
              onClick={() => void confirm()}
            >
              {busy && <Loader2 className="size-4 animate-spin" />}
              Подтвердить почту
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ProfileFields() {
  const { me, refreshMe } = useAuth();
  const [name, setName] = useState(me?.name ?? "");
  const [city, setCity] = useState(me?.city ?? "");
  const [busy, setBusy] = useState(false);

  const dirty = name !== (me?.name ?? "") || city !== (me?.city ?? "");

  async function save() {
    setBusy(true);
    const { error } = await updateMeApiV1UsersMePatch({ body: { name, city } });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось сохранить"));
      return;
    }
    toast.success("Профиль сохранён");
    await refreshMe();
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Основное</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div>
          <Label htmlFor="profile-name">Имя</Label>
          <Input
            id="profile-name"
            className="mt-1.5"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Артём Соколов"
          />
        </div>
        <div>
          <Label htmlFor="profile-city">Город</Label>
          <Input
            id="profile-city"
            className="mt-1.5"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Москва"
          />
        </div>
        <div>
          <Label>Телефон</Label>
          <Input className="mt-1.5 font-mono" value={me?.phone ?? ""} disabled />
          <p className="mt-1 text-xs text-muted-foreground">
            Телефон — ваш логин, изменить его нельзя
          </p>
        </div>
        <Button disabled={!dirty || busy} onClick={() => void save()}>
          {busy && <Loader2 className="size-4 animate-spin" />}
          Сохранить
        </Button>
      </CardContent>
    </Card>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const { me, loading } = useAuth();

  useEffect(() => {
    if (!loading && !me) router.replace("/auth");
  }, [loading, me, router]);

  if (loading || !me) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-xl space-y-4 px-4 py-8">
        <h1 className="text-xl font-bold">Профиль</h1>
        <ProfileFields />
        <EmailBlock />
      </main>
    </>
  );
}
