"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Minus, Plus } from "lucide-react";
import {
  createFilialApiV1CompaniesCompanyUuidFilialsPost,
  createVacancyApiV1CompaniesCompanyUuidVacanciesPost,
  listFilialsApiV1CompaniesCompanyUuidFilialsGet,
  publishVacancyApiV1VacanciesVacancyUuidPublishPost,
  type FilialOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { DICT } from "@/lib/dict";
import { useOrg } from "@/lib/org-context";
import { kopToRub, rubInputToKop } from "@/lib/format";
import { cn } from "@/lib/utils";

const ROLES = ["Официант", "Бариста", "Хостес", "Бармен", "Повар", "Ресепшн", "Гардероб", "Промоутер"];

function AddFilialDialog({
  companyUuid,
  onCreated,
}: {
  companyUuid: string;
  onCreated: (filial: FilialOut) => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);

  async function create() {
    setBusy(true);
    const { data, error } = await createFilialApiV1CompaniesCompanyUuidFilialsPost({
      path: { company_uuid: companyUuid },
      body: { name, address },
    });
    setBusy(false);
    if (error || !data) {
      toast.error(String((error as { detail?: string })?.detail ?? "Не удалось создать филиал"));
      return;
    }
    onCreated(data);
    setOpen(false);
    setName("");
    setAddress("");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Plus className="size-3.5" />
          Новый филиал
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Новый филиал</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div>
            <Label htmlFor="filial-name">Название</Label>
            <Input
              id="filial-name"
              className="mt-1.5"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Гранд Холл — Тверская"
            />
          </div>
          <div>
            <Label htmlFor="filial-address">Адрес</Label>
            <Input
              id="filial-address"
              className="mt-1.5"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Тверская, 9"
            />
          </div>
          <Button
            className="w-full"
            disabled={name.trim().length < 2 || address.trim().length < 2 || busy}
            onClick={() => void create()}
          >
            {busy && <Loader2 className="size-4 animate-spin" />}
            Создать
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function CreateEventPage() {
  const router = useRouter();
  const { current } = useOrg();
  const [filials, setFilials] = useState<FilialOut[]>([]);
  const [filialUuid, setFilialUuid] = useState<string>("");
  const [role, setRole] = useState<string>(ROLES[0]);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [timeFrom, setTimeFrom] = useState("16:00");
  const [timeTo, setTimeTo] = useState("23:00");
  const [slots, setSlots] = useState(1);
  const [rate, setRate] = useState("450");
  const [tags, setTags] = useState("");
  const [requirements, setRequirements] = useState("");
  const [busy, setBusy] = useState<"draft" | "publish" | null>(null);

  const companyUuid = current?.company.company_uuid;

  const loadFilials = useCallback(async () => {
    if (!companyUuid) return;
    const { data } = await listFilialsApiV1CompaniesCompanyUuidFilialsGet({
      path: { company_uuid: companyUuid },
    });
    setFilials(data ?? []);
    if (data?.length && !filialUuid) setFilialUuid(data[0].filial_uuid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [companyUuid]);

  useEffect(() => {
    void loadFilials();
  }, [loadFilials]);

  if (!companyUuid) return null;

  const rateKop = rubInputToKop(rate);
  const hours = (() => {
    if (!timeFrom || !timeTo) return 0;
    const [fh, fm] = timeFrom.split(":").map(Number);
    const [th, tm] = timeTo.split(":").map(Number);
    const diff = th * 60 + tm - (fh * 60 + fm);
    return diff > 0 ? diff / 60 : 0;
  })();
  const totalKop = rateKop && hours ? Math.round(rateKop * hours) : null;

  const filial = filials.find((f) => f.filial_uuid === filialUuid);
  const valid =
    filialUuid && title.trim().length >= 2 && date && hours > 0 && rateKop && slots >= 1;

  async function submit(mode: "draft" | "publish") {
    if (!valid || !filial) return;
    setBusy(mode);
    const { data, error } = await createVacancyApiV1CompaniesCompanyUuidVacanciesPost({
      path: { company_uuid: companyUuid! },
      body: {
        filial_uuid: filialUuid,
        role_name: role,
        event_title: title.trim(),
        starts_at: `${date}T${timeFrom}:00+03:00`,
        ends_at: `${date}T${timeTo}:00+03:00`,
        venue_address: filial.address,
        lat: filial.lat,
        lon: filial.lon,
        pay_hour_kop: rateKop!,
        slots,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        requirements: requirements.split("\n").map((r) => r.trim()).filter(Boolean),
      },
    });
    if (error || !data) {
      setBusy(null);
      toast.error(String((error as { detail?: string })?.detail ?? "Не удалось создать событие"));
      return;
    }
    if (mode === "publish") {
      const pub = await publishVacancyApiV1VacanciesVacancyUuidPublishPost({
        path: { vacancy_uuid: data.vacancy_uuid },
      });
      setBusy(null);
      if (pub.error) {
        toast.error(
          String((pub.error as { detail?: string }).detail ?? "Оплата не прошла — событие сохранено черновиком"),
        );
        router.push("/org/events");
        return;
      }
      toast.success(DICT.publishedPaid);
    } else {
      setBusy(null);
      toast.success("Черновик сохранён");
    }
    router.push("/org/events");
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-semibold">{DICT.createEvent}</h1>

      <Card className="mt-6">
        <CardContent className="space-y-5 pt-6">
          <div>
            <Label>Роль</Label>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {ROLES.map((r) => (
                <button
                  key={r}
                  type="button"
                  className={cn(
                    "rounded-full border px-3 py-1 text-sm font-medium",
                    role === r
                      ? "border-primary bg-primary text-primary-foreground"
                      : "hover:bg-secondary",
                  )}
                  onClick={() => setRole(r)}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          <div>
            <Label htmlFor="event-title">Название события</Label>
            <Input
              id="event-title"
              className="mt-1.5"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Свадебный банкет"
            />
          </div>

          <div>
            <Label>Филиал</Label>
            <div className="mt-1.5 flex gap-2">
              <Select value={filialUuid} onValueChange={setFilialUuid}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Выберите филиал" />
                </SelectTrigger>
                <SelectContent>
                  {filials.map((f) => (
                    <SelectItem key={f.filial_uuid} value={f.filial_uuid}>
                      {f.name} · {f.address}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <AddFilialDialog
                companyUuid={companyUuid}
                onCreated={(f) => {
                  setFilials((prev) => [...prev, f]);
                  setFilialUuid(f.filial_uuid);
                }}
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <Label htmlFor="event-date">Дата</Label>
              <Input
                id="event-date"
                type="date"
                className="mt-1.5"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="time-from">Начало</Label>
              <Input
                id="time-from"
                type="time"
                className="mt-1.5"
                value={timeFrom}
                onChange={(e) => setTimeFrom(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="time-to">Конец</Label>
              <Input
                id="time-to"
                type="time"
                className="mt-1.5"
                value={timeTo}
                onChange={(e) => setTimeTo(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label>Мест</Label>
              <div className="mt-1.5 flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setSlots((s) => Math.max(1, s - 1))}
                >
                  <Minus className="size-4" />
                </Button>
                <span className="w-10 text-center font-mono font-semibold">{slots}</span>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => setSlots((s) => Math.min(500, s + 1))}
                >
                  <Plus className="size-4" />
                </Button>
              </div>
            </div>
            <div>
              <Label htmlFor="rate">Ставка, ₽{DICT.perHour}</Label>
              <Input
                id="rate"
                className="mt-1.5 font-mono"
                inputMode="decimal"
                value={rate}
                onChange={(e) => setRate(e.target.value)}
              />
              {totalKop !== null && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Итог за смену: <span className="font-mono">{kopToRub(totalKop)}</span> ({hours} ч)
                </p>
              )}
            </div>
          </div>

          <div>
            <Label htmlFor="tags">Теги (через запятую)</Label>
            <Input
              id="tags"
              className="mt-1.5"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="Банкет, Свадьба"
            />
          </div>

          <div>
            <Label htmlFor="reqs">Требования (по строке)</Label>
            <textarea
              id="reqs"
              className="mt-1.5 min-h-20 w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder={"Опыт от 6 мес\nЧёрный верх / низ\nМедкнижка"}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-base">{DICT.publishCost}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">{DICT.feeNote}</span>
            <span className="font-mono text-lg font-semibold">{DICT.vacancyCost}</span>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">{DICT.publishNote}</p>
          <div className="mt-4 flex gap-2">
            <Button
              variant="outline"
              className="flex-1"
              disabled={!valid || busy !== null}
              onClick={() => void submit("draft")}
            >
              {busy === "draft" && <Loader2 className="size-4 animate-spin" />}
              {DICT.saveDraft}
            </Button>
            <Button
              className="flex-1"
              disabled={!valid || busy !== null}
              onClick={() => void submit("publish")}
            >
              {busy === "publish" && <Loader2 className="size-4 animate-spin" />}
              {DICT.payAndPublish}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
