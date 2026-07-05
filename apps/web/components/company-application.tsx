"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { toast } from "sonner";
import { Clock3, Loader2, XCircle } from "lucide-react";
import {
  createCompanyApiV1CompaniesPost,
  type MyCompanyOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { MapPoint } from "@/components/map-picker";
import { isValidInn, isValidOgrn } from "@/lib/requisites";
import { useOrg } from "@/lib/org-context";

// maplibre трогает window — на сервере не рендерим
const MapPicker = dynamic(() => import("@/components/map-picker").then((m) => m.MapPicker), {
  ssr: false,
  loading: () => <div className="h-64 animate-pulse rounded-xl border bg-secondary" />,
});

export function CompanyApplicationForm() {
  const { reload } = useOrg();
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
  const [busy, setBusy] = useState(false);

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
    const { error } = await createCompanyApiV1CompaniesPost({
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
    setBusy(false);
    if (error) {
      toast.error(String((error as { detail?: string }).detail ?? "Не удалось отправить заявку"));
      return;
    }
    toast.success("Заявка отправлена на проверку");
    await reload();
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8">
      <Card>
        <CardContent className="pt-6">
          <h1 className="text-lg font-semibold">Заявка на регистрацию организации</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Администратор проверит реквизиты и подтвердит кабинет. До подтверждения публикация
            смен недоступна.
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

export function CompanyApplicationStatus({ membership }: { membership: MyCompanyOut }) {
  const company = membership.company;
  const rejected = company.status === "rejected";

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-4">
      <Card>
        <CardContent className="pt-6 text-center">
          {rejected ? (
            <XCircle className="mx-auto size-10 text-destructive" />
          ) : (
            <Clock3 className="mx-auto size-10 text-amber-600" />
          )}
          <h1 className="mt-3 text-lg font-semibold">
            {rejected ? "Заявка отклонена" : "Заявка на проверке"}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {rejected
              ? company.reject_reason ?? "Администратор отклонил заявку."
              : `Мы проверяем реквизиты «${company.name}». Кабинет откроется после подтверждения администратором.`}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
