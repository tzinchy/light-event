"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import {
  BarChart3,
  CalendarDays,
  Loader2,
  LogOut,
  MessageSquareText,
  PlusCircle,
  Star,
  Users,
  UsersRound,
  Wallet,
} from "lucide-react";
import {
  CompanyApplicationForm,
  CompanyApplicationStatus,
} from "@/components/company-application";
import { useAuth } from "@/lib/auth-context";
import { OrgProvider, useOrg } from "@/lib/org-context";
import { cn } from "@/lib/utils";

// пункты будущих модулей показываем выключенными — честно, без мёртвых экранов
const NAV = [
  { href: "/org", label: "Аналитика", icon: BarChart3, ready: true },
  { href: "/org/events", label: "События", icon: CalendarDays, ready: true },
  { href: "/org/create", label: "Создать событие", icon: PlusCircle, ready: true },
  { href: "/org/candidates", label: "Отклики", icon: UsersRound, ready: true },
  { href: "/org/tests", label: "Тесты", icon: MessageSquareText, ready: true },
  { href: "/org/team", label: "Команда", icon: Users, ready: true },
  { href: "/org/balance", label: "Баланс", icon: Wallet, ready: true },
  { href: "/org/reviews", label: "Отзывы", icon: Star, ready: true },
];

const ROLE_LABEL: Record<string, string> = {
  main_manager: "Главный менеджер",
  manager: "Менеджер",
  coordinator: "Координатор",
  staff: "Сотрудник",
};

function initials(text: string | null | undefined): string {
  const src = (text ?? "").trim();
  if (!src) return "—";
  const parts = src.split(/\s+/).filter(Boolean);
  const raw = parts.length >= 2 ? parts[0][0] + parts[1][0] : src.slice(0, 2);
  return raw.toUpperCase();
}

function OrgShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { me, loading: authLoading, logout } = useAuth();
  const { loading, current } = useOrg();

  useEffect(() => {
    if (!authLoading && !me) router.replace("/auth");
  }, [authLoading, me, router]);

  if (authLoading || loading || !me) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted-foreground">
        <Loader2 className="size-5 animate-spin" />
      </div>
    );
  }

  if (!current) return <CompanyApplicationForm />;
  if (current.company.status !== "verified") return <CompanyApplicationStatus membership={current} />;

  const roleLabel = ROLE_LABEL[current.company_role] ?? current.company_role;

  return (
    <div className="min-h-screen bg-[#fafafa]">
      <div className="mx-auto max-w-[1280px] px-4 py-6">
        <div className="flex min-h-[calc(100vh-3rem)] overflow-hidden rounded-2xl border bg-card shadow-sm">
          <aside className="hidden w-64 shrink-0 flex-col border-r md:flex">
            <div className="flex items-center gap-3 border-b px-4 py-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary text-sm font-bold text-primary-foreground">
                {initials(current.company.name)}
              </div>
              <div className="min-w-0">
                <div className="truncate font-semibold">{current.company.name}</div>
                <div className="truncate text-xs text-muted-foreground">Кабинет организации</div>
              </div>
            </div>

            <nav className="flex-1 space-y-0.5 p-3">
              {NAV.map((item) =>
                item.ready ? (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium",
                      pathname === item.href
                        ? "bg-secondary text-foreground"
                        : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                    )}
                  >
                    <item.icon className="size-4" />
                    {item.label}
                  </Link>
                ) : (
                  <div
                    key={item.href}
                    className="flex cursor-not-allowed items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground/50"
                    title="Скоро"
                  >
                    <item.icon className="size-4" />
                    {item.label}
                    <span className="ml-auto text-[10px] uppercase">скоро</span>
                  </div>
                ),
              )}
            </nav>

            <div className="border-t p-3">
              <div className="flex items-center gap-3 rounded-xl border px-3 py-2.5">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">
                  {initials(me.name ?? me.email)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">{me.name ?? me.email ?? "Профиль"}</div>
                  <div className="truncate text-xs text-muted-foreground">{roleLabel}</div>
                </div>
                <button
                  className="shrink-0 text-muted-foreground hover:text-foreground"
                  title="Выйти"
                  onClick={() => {
                    logout();
                    router.replace("/");
                  }}
                >
                  <LogOut className="size-4" />
                </button>
              </div>
            </div>
          </aside>

          <main className="min-w-0 flex-1">
            {/* на <md сайдбар скрыт — навигация кабинета лентой чипсов */}
            <nav className="sticky top-0 z-10 flex gap-1.5 overflow-x-auto border-b bg-card px-3 py-2 md:hidden">
              {NAV.filter((item) => item.ready).map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium",
                    pathname === item.href
                      ? "border-primary bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                >
                  <item.icon className="size-3.5" />
                  {item.label}
                </Link>
              ))}
              <button
                className="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium text-muted-foreground"
                onClick={() => {
                  logout();
                  router.replace("/");
                }}
              >
                <LogOut className="size-3.5" />
                Выйти
              </button>
            </nav>
            <div className="px-6 py-8 md:px-10">{children}</div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function OrgLayout({ children }: { children: ReactNode }) {
  return (
    <OrgProvider>
      <OrgShell>{children}</OrgShell>
    </OrgProvider>
  );
}
