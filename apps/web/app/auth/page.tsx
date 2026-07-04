"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { CheckCircle2, FileUp, Loader2, Mail } from "lucide-react";
import {
  consentApiV1AuthConsentPost,
  myCompaniesApiV1CompaniesMyGet,
  requestOtpApiV1AuthOtpRequestPost,
  uploadDocumentApiV1DocumentsPost,
  verifyOtpApiV1AuthOtpVerifyPost,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OtpInput, OTP_LENGTH } from "@/components/otp-input";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

type Step = "welcome" | "email" | "otp" | "kyc";

const RESEND_SECONDS = 60;

const KYC_DOCS = [
  { kind: "passport", label: DICT.passport },
  { kind: "selfie_with_passport", label: DICT.selfieWithPassport },
  { kind: "medbook", label: DICT.medbook },
] as const;

function Stepper({ step }: { step: Step }) {
  const items = [
    { key: "email", label: DICT.stEmail },
    { key: "otp", label: DICT.stOtp },
    { key: "kyc", label: DICT.stKyc },
  ];
  const activeIdx = items.findIndex((i) => i.key === step);
  return (
    <div className="mb-8 flex items-center justify-center gap-2">
      {items.map((item, i) => (
        <div key={item.key} className="flex items-center gap-2">
          {i > 0 && <div className="h-px w-8 bg-border" />}
          <div
            className={cn(
              "flex items-center gap-1.5 text-xs font-medium",
              i <= activeIdx ? "text-foreground" : "text-muted-foreground",
            )}
          >
            <span
              className={cn(
                "flex size-5 items-center justify-center rounded-full text-[10px] font-semibold",
                i < activeIdx
                  ? "bg-brand text-white"
                  : i === activeIdx
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-muted-foreground",
              )}
            >
              {i + 1}
            </span>
            {item.label}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AuthPage() {
  const router = useRouter();
  const { me, login, refreshMe } = useAuth();
  const [step, setStep] = useState<Step>("welcome");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [resendLeft, setResendLeft] = useState(0);
  const [uploaded, setUploaded] = useState<Record<string, boolean>>({});
  const [uploading, setUploading] = useState<string | null>(null);
  const [consentChecked, setConsentChecked] = useState(false);
  const fileRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => {
    if (resendLeft <= 0) return;
    const t = setInterval(() => setResendLeft((s) => s - 1), 1000);
    return () => clearInterval(t);
  }, [resendLeft]);

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  async function goToOrgOrHome() {
    const { data } = await myCompaniesApiV1CompaniesMyGet();
    router.replace(data && data.length > 0 ? "/org" : "/");
  }

  async function sendCode() {
    setBusy(true);
    const { error } = await requestOtpApiV1AuthOtpRequestPost({
      body: { email },
    });
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось отправить код"));
      return;
    }
    setCode("");
    setResendLeft(RESEND_SECONDS);
    setStep("otp");
  }

  async function verify() {
    setBusy(true);
    const { data, error } = await verifyOtpApiV1AuthOtpVerifyPost({
      body: { email, code },
    });
    setBusy(false);
    if (error || !data) {
      toast.error(String((error as { detail?: string })?.detail ?? "Неверный код"));
      setCode("");
      return;
    }
    await login(data.access_token, data.refresh_token);
    if (data.is_new_user) {
      setStep("kyc");
    } else {
      await goToOrgOrHome();
    }
  }

  async function uploadDoc(kind: string, file: File) {
    setUploading(kind);
    const { error } = await uploadDocumentApiV1DocumentsPost({
      // openapi-ts типизирует binary как string; SDK шлёт multipart и принимает File
      body: { kind: kind as (typeof KYC_DOCS)[number]["kind"], file: file as unknown as string },
    });
    setUploading(null);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось загрузить файл"));
      return;
    }
    setUploaded((u) => ({ ...u, [kind]: true }));
  }

  async function finishKyc() {
    setBusy(true);
    const { error } = await consentApiV1AuthConsentPost();
    setBusy(false);
    if (error) {
      toast.error("Не удалось сохранить согласие, попробуйте ещё раз");
      return;
    }
    await refreshMe();
    toast.success("Верификация отправлена на проверку");
    await goToOrgOrHome();
  }

  const kycReady = KYC_DOCS.every((d) => uploaded[d.kind]) && consentChecked;

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-4 py-12">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 font-semibold">
          <span className="flex size-7 items-center justify-center rounded-lg bg-brand text-xs font-bold text-white">
            le
          </span>
          light-event
        </Link>

        {step !== "welcome" && <Stepper step={step} />}

        <Card>
          <CardContent className="pt-6">
            {step === "welcome" && (
              <div className="text-center">
                <h1 className="text-xl font-semibold">{DICT.welcomeTitle}</h1>
                <p className="mt-2 text-sm text-muted-foreground">{DICT.welcomeSub}</p>
                <Button className="mt-6 w-full" onClick={() => setStep("email")}>
                  <Mail className="size-4" />
                  {DICT.loginByEmail}
                </Button>
                <div className="my-4 flex items-center gap-3 text-xs text-muted-foreground">
                  <div className="h-px flex-1 bg-border" />
                  {DICT.orWith}
                  <div className="h-px flex-1 bg-border" />
                </div>
                {/* OAuthProvider появится позже — кнопка-заглушка из референса */}
                <Button variant="outline" className="w-full" disabled>
                  {DICT.yandexLogin}
                </Button>
              </div>
            )}

            {step === "email" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (emailValid) void sendCode();
                }}
              >
                <Label htmlFor="email">{DICT.emailLabel}</Label>
                <Input
                  id="email"
                  type="email"
                  autoFocus
                  autoComplete="email"
                  inputMode="email"
                  className="mt-2"
                  value={email}
                  onChange={(e) => setEmail(e.target.value.trim())}
                  placeholder="you@example.com"
                />
                <Button type="submit" className="mt-4 w-full" disabled={!emailValid || busy}>
                  {busy && <Loader2 className="size-4 animate-spin" />}
                  {DICT.getCode}
                </Button>
                <p className="mt-4 text-center text-xs text-muted-foreground">{DICT.legalNote}</p>
              </form>
            )}

            {step === "otp" && (
              <div>
                <p className="mb-4 text-center text-sm text-muted-foreground">
                  {DICT.otpSentTo} <span className="font-medium text-foreground">{email}</span>
                </p>
                <OtpInput value={code} onChange={setCode} disabled={busy} />
                <Button
                  className="mt-5 w-full"
                  disabled={code.replace(/\s/g, "").length !== OTP_LENGTH || busy}
                  onClick={() => void verify()}
                >
                  {busy && <Loader2 className="size-4 animate-spin" />}
                  {DICT.verify}
                </Button>
                <div className="mt-4 text-center text-xs text-muted-foreground">
                  {resendLeft > 0 ? (
                    <>
                      {DICT.resendIn} <span className="font-mono">{resendLeft} с</span>
                    </>
                  ) : (
                    <button className="underline" onClick={() => void sendCode()} disabled={busy}>
                      {DICT.resend}
                    </button>
                  )}
                </div>
              </div>
            )}

            {step === "kyc" && (
              <div>
                <h2 className="font-semibold">{DICT.kycDocs}</h2>
                <p className="mt-1 text-xs text-muted-foreground">{DICT.kycNote}</p>
                <div className="mt-4 space-y-2">
                  {KYC_DOCS.map((doc) => (
                    <button
                      key={doc.kind}
                      type="button"
                      className={cn(
                        "flex w-full items-center justify-between rounded-xl border p-3 text-left text-sm",
                        uploaded[doc.kind]
                          ? "border-brand-border bg-brand-soft"
                          : "hover:bg-secondary",
                      )}
                      disabled={uploading !== null}
                      onClick={() => fileRefs.current[doc.kind]?.click()}
                    >
                      <span className="font-medium">{doc.label}</span>
                      {uploading === doc.kind ? (
                        <Loader2 className="size-4 animate-spin text-muted-foreground" />
                      ) : uploaded[doc.kind] ? (
                        <CheckCircle2 className="size-4 text-brand" />
                      ) : (
                        <FileUp className="size-4 text-muted-foreground" />
                      )}
                      <input
                        ref={(el) => {
                          fileRefs.current[doc.kind] = el;
                        }}
                        type="file"
                        accept="image/*,.pdf"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) void uploadDoc(doc.kind, f);
                          e.target.value = "";
                        }}
                      />
                    </button>
                  ))}
                </div>
                <label className="mt-4 flex items-start gap-2 text-xs text-muted-foreground">
                  <Checkbox
                    checked={consentChecked}
                    onCheckedChange={(v) => setConsentChecked(v === true)}
                    className="mt-0.5"
                  />
                  <span>
                    Я подтверждаю{" "}
                    <Link
                      href="/legal/personal-data"
                      target="_blank"
                      className="text-primary underline underline-offset-2"
                    >
                      согласие на обработку персональных данных
                    </Link>
                    , включая паспортные данные, для верификации (152-ФЗ).
                  </span>
                </label>
                <Button className="mt-4 w-full" disabled={!kycReady || busy} onClick={() => void finishKyc()}>
                  {busy && <Loader2 className="size-4 animate-spin" />}
                  {DICT.finishKyc}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {me && step === "welcome" && (
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Вы уже вошли.{" "}
            <Link href="/org" className="underline">
              {DICT.openOrgConsole}
            </Link>
          </p>
        )}

        <Link href="/" className="mt-6 text-center text-sm text-muted-foreground underline">
          {DICT.backHome}
        </Link>
      </div>
    </div>
  );
}
