"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BadgeCheck, Loader2, Mail } from "lucide-react";
import {
  confirmEmailApiV1UsersMeEmailConfirmPost,
  requestEmailCodeApiV1UsersMeEmailPost,
  updateMeApiV1UsersMePatch,
  userReviewsApiV1UsersUserUuidReviewsGet,
  type ReviewListOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ReviewList } from "@/components/review-list";
import { EDUCATION_OPTIONS, ENGLISH_OPTIONS, EXPERIENCE_OPTIONS, GENDER_OPTIONS } from "@/lib/experience";
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
        <Label htmlFor="profile-email">Почта — ваш логин</Label>
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
  const [experience, setExperience] = useState(me?.experience ?? "");
  const [about, setAbout] = useState(me?.about ?? "");
  const [english, setEnglish] = useState(me?.english_level ?? "");
  const [education, setEducation] = useState(me?.education ?? "");
  const [telegram, setTelegram] = useState(me?.telegram ?? "");
  const [birthDate, setBirthDate] = useState(me?.birth_date ?? "");
  const [citizenship, setCitizenship] = useState(me?.citizenship ?? "");
  const [gender, setGender] = useState(me?.gender ?? "");
  const [busy, setBusy] = useState(false);

  const dirty =
    name !== (me?.name ?? "") ||
    city !== (me?.city ?? "") ||
    experience !== (me?.experience ?? "") ||
    about !== (me?.about ?? "") ||
    english !== (me?.english_level ?? "") ||
    education !== (me?.education ?? "") ||
    telegram !== (me?.telegram ?? "") ||
    birthDate !== (me?.birth_date ?? "") ||
    citizenship !== (me?.citizenship ?? "") ||
    gender !== (me?.gender ?? "");

  async function save() {
    setBusy(true);
    const { error } = await updateMeApiV1UsersMePatch({
      body: {
        name,
        city,
        experience: experience || null,
        about: about || null,
        english_level: english || null,
        education: education || null,
        telegram,
        birth_date: birthDate || null,
        citizenship: citizenship || null,
        gender: gender || null,
      },
    });
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
          <Label htmlFor="profile-exp">Опыт работы</Label>
          <select
            id="profile-exp"
            className="mt-1.5 h-9 w-full rounded-lg border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
          >
            <option value="">Не указан</option>
            {EXPERIENCE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="profile-english">Английский язык</Label>
            <select
              id="profile-english"
              className="mt-1.5 h-9 w-full rounded-lg border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
              value={english}
              onChange={(e) => setEnglish(e.target.value)}
            >
              <option value="">Не указан</option>
              {ENGLISH_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="profile-education">Образование</Label>
            <select
              id="profile-education"
              className="mt-1.5 h-9 w-full rounded-lg border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
              value={education}
              onChange={(e) => setEducation(e.target.value)}
            >
              <option value="">Не указано</option>
              {EDUCATION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="profile-birth">Дата рождения</Label>
            <Input
              id="profile-birth"
              type="date"
              className="mt-1.5"
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="profile-gender">Пол</Label>
            <select
              id="profile-gender"
              className="mt-1.5 h-9 w-full rounded-lg border bg-transparent px-3 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
              value={gender}
              onChange={(e) => setGender(e.target.value)}
            >
              <option value="">Не указан</option>
              {GENDER_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <Label htmlFor="profile-citizenship">Гражданство</Label>
            <Input
              id="profile-citizenship"
              className="mt-1.5"
              value={citizenship}
              onChange={(e) => setCitizenship(e.target.value)}
              placeholder="РФ"
            />
          </div>
          <div>
            <Label htmlFor="profile-telegram">Телеграм</Label>
            <Input
              id="profile-telegram"
              className="mt-1.5 font-mono"
              value={telegram}
              onChange={(e) => setTelegram(e.target.value.trim())}
              placeholder="@username"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Виден только вам и платформе — организациям не показывается.
            </p>
          </div>
        </div>
        <div>
          <Label htmlFor="profile-about">О себе</Label>
          <textarea
            id="profile-about"
            className="mt-1.5 min-h-24 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
            value={about}
            onChange={(e) => setAbout(e.target.value)}
            placeholder="Кратко о вашем опыте, сильных сторонах, любимых форматах смен"
            maxLength={2000}
          />
        </div>
        <Button disabled={!dirty || busy} onClick={() => void save()}>
          {busy && <Loader2 className="size-4 animate-spin" />}
          Сохранить
        </Button>
      </CardContent>
    </Card>
  );
}

function MyReviewsBlock() {
  const { me } = useAuth();
  const [reviews, setReviews] = useState<ReviewListOut | null>(null);

  useEffect(() => {
    if (!me) return;
    void (async () => {
      const { data } = await userReviewsApiV1UsersUserUuidReviewsGet({
        path: { user_uuid: me.user_uuid },
      });
      setReviews(data ?? null);
    })();
  }, [me]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Отзывы обо мне</CardTitle>
      </CardHeader>
      <CardContent>
        {reviews === null ? (
          <div className="flex justify-center py-6 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
          </div>
        ) : (
          <ReviewList data={reviews} emptyText="Пока нет отзывов — они появятся после первых смен" />
        )}
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
        <MyReviewsBlock />
      </main>
    </>
  );
}
