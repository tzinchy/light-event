"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { CheckCircle2, Loader2, Upload } from "lucide-react";
import { submitApplicationApiV1CompanyApplicationsPost } from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { MapPoint } from "@/components/map-picker";
import { isValidInn, isValidOgrn } from "@/lib/requisites";

// maplibre трогает window — на сервере не рендерим
const MapPicker = dynamic(() => import("@/components/map-picker").then((m) => m.MapPicker), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse rounded-xl border bg-secondary" />,
});

async function uploadProof(applicationUuid: string, token: string, file: File): Promise<boolean> {
  const form = new FormData();
  form.append("token", token);
  form.append("file", file);
  const resp = await fetch(`/api/v1/company-applications/${applicationUuid}/document`, {
    method: "POST",
    body: form,
  });
  return resp.ok;
}

export default function ApplyPage() {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [inn, setInn] = useState("");
  const [ogrn, setOgrn] = useState("");
  const [address, setAddress] = useState("");
  const [contactPhone, setContactPhone] = useState("+7");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactPosition, setContactPosition] = useState("");
  const [point, setPoint] = useState<MapPoint | null>(null);
  const [proof, setProof] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  const innError = inn.length > 0 && !isValidInn(inn);
  const ogrnError = ogrn.length > 0 && !isValidOgrn(ogrn);
  const emailError = contactEmail.length > 0 && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactEmail);
  const ready =
    name.trim().length >= 2 &&
    isValidInn(inn) &&
    isValidOgrn(ogrn) &&
    address.trim().length >= 5 &&
    /^\+\d{10,15}$/.test(contactPhone) &&
    contactName.trim().length >= 2 &&
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contactEmail) &&
    contactPosition.trim().length >= 2 &&
    point !== null;

  async function submit() {
    if (!point) return;
    setBusy(true);
    const { data, error } = await submitApplicationApiV1CompanyApplicationsPost({
      body: {
        name: name.trim(),
        description: description.trim() || null,
        inn,
        ogrn,
        address: address.trim(),
        lat: point.lat,
        lon: point.lon,
        contact_phone: contactPhone,
        contact_name: contactName.trim(),
        contact_email: contactEmail.trim(),
        contact_position: contactPosition.trim(),
      },
    });
    if (error || !data) {
      setBusy(false);
      toast.error(String((error as { detail?: string })?.detail ?? "Не удалось отправить заявку"));
      return;
    }
    if (proof) {
      const ok = await uploadProof(data.company_application_uuid, data.upload_token, proof);
      if (!ok) toast.error("Заявка принята, но документ не загрузился — приложите его позже по запросу админа");
    }
    setBusy(false);
    setDone(true);
  }

  if (done) {
    return (
      <div className="mx-auto flex min-h-[80dvh] w-full max-w-md flex-col justify-center px-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <CheckCircle2 className="mx-auto size-10 text-brand" />
            <h1 className="mt-3 text-lg font-semibold">Заявка отправлена</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Администратор проверит данные и документ. После подтверждения на почту{" "}
              <span className="font-medium">{contactEmail}</span> придёт код для входа в кабинет.
            </p>
            <Button asChild variant="outline" className="mt-4">
              <Link href="/">На главную</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8">
      <Card>
        <CardContent className="pt-6">
          <h1 className="text-lg font-semibold">Заявка на подключение отеля</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Учётная запись не нужна — заполните данные и приложите документ, подтверждающий вашу
            должность. Кабинет заведём после проверки.
          </p>

          <div className="mt-5 grid gap-4">
            <div>
              <Label htmlFor="ca-name">Название организации</Label>
              <Input
                id="ca-name"
                className="mt-1.5"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Гранд Холл «Метрополь»"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="ca-inn">ИНН</Label>
                <Input
                  id="ca-inn"
                  className="mt-1.5 font-mono"
                  inputMode="numeric"
                  value={inn}
                  onChange={(e) => setInn(e.target.value.replace(/\D/g, "").slice(0, 12))}
                  placeholder="7707083893"
                  aria-invalid={innError}
                />
                {innError && (
                  <p className="mt-1 text-xs text-destructive">Проверьте ИНН — контрольная цифра не сходится</p>
                )}
              </div>
              <div>
                <Label htmlFor="ca-ogrn">ОГРН</Label>
                <Input
                  id="ca-ogrn"
                  className="mt-1.5 font-mono"
                  inputMode="numeric"
                  value={ogrn}
                  onChange={(e) => setOgrn(e.target.value.replace(/\D/g, "").slice(0, 15))}
                  placeholder="1027700132195"
                  aria-invalid={ogrnError}
                />
                {ogrnError && (
                  <p className="mt-1 text-xs text-destructive">Проверьте ОГРН — контрольная цифра не сходится</p>
                )}
              </div>
            </div>
            <div>
              <Label htmlFor="ca-desc">Описание (необязательно)</Label>
              <Input
                id="ca-desc"
                className="mt-1.5"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Банкетный зал в центре Москвы"
              />
            </div>
            <div>
              <Label htmlFor="ca-phone">Контактный телефон</Label>
              <Input
                id="ca-phone"
                className="mt-1.5 font-mono"
                inputMode="tel"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value.replace(/[^+\d]/g, ""))}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="ca-contact-name">ФИО заявителя</Label>
                <Input
                  id="ca-contact-name"
                  className="mt-1.5"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  placeholder="Марина Кузнецова"
                />
              </div>
              <div>
                <Label htmlFor="ca-contact-position">Должность</Label>
                <Input
                  id="ca-contact-position"
                  className="mt-1.5"
                  value={contactPosition}
                  onChange={(e) => setContactPosition(e.target.value)}
                  placeholder="Управляющий"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="ca-contact-email">Почта заявителя</Label>
              <Input
                id="ca-contact-email"
                type="email"
                className="mt-1.5"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value.trim())}
                placeholder="manager@example.com"
                aria-invalid={emailError}
              />
              {emailError && <p className="mt-1 text-xs text-destructive">Проверьте адрес почты</p>}
              <p className="mt-1 text-xs text-muted-foreground">На эту почту придёт код для входа после одобрения.</p>
            </div>

            <div>
              <Label htmlFor="ca-address">Адрес</Label>
              <Input
                id="ca-address"
                className="mt-1.5"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="Москва, Тверская, 1"
              />
            </div>
            <div>
              <Label>Точка на карте</Label>
              <p className="mb-1.5 mt-0.5 text-xs text-muted-foreground">
                Нажмите на карту, чтобы отметить, где находится организация
              </p>
              <MapPicker value={point} onChange={setPoint} className="h-64" />
              {point && (
                <p className="mt-1 font-mono text-xs text-muted-foreground">
                  {point.lat.toFixed(5)}, {point.lon.toFixed(5)}
                </p>
              )}
            </div>

            <div>
              <Label>Документ, подтверждающий должность</Label>
              <p className="mb-1.5 mt-0.5 text-xs text-muted-foreground">
                Приказ о назначении, доверенность или письмо на бланке (JPEG/PNG/PDF).
              </p>
              <input
                ref={fileInput}
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf"
                className="hidden"
                onChange={(e) => setProof(e.target.files?.[0] ?? null)}
              />
              <Button type="button" variant="outline" onClick={() => fileInput.current?.click()}>
                <Upload className="size-4" />
                {proof ? proof.name : "Приложить документ"}
              </Button>
            </div>

            <Button disabled={!ready || busy} onClick={() => void submit()}>
              {busy && <Loader2 className="size-4 animate-spin" />}
              Отправить заявку
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
