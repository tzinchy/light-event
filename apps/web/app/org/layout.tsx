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
  { href: "/org", label: "Аналитика", icon: BarChart3, ready: false },
  { href: "/org/events", label: "События", icon: CalendarDays, ready: true },
  { href: "/org/create", label: "Создать событие", icon: PlusCircle, ready: true },
  { href: "/org/candidates", label: "Отклики", icon: UsersRound, ready: true },
  { href: "/org/tests", label: "Тесты", icon: MessageSquareText, ready: true },
  { href: "/org/team", label: "Команда", icon: Users, ready: true },
  { href: "/org/balance", label: "Баланс", icon: Wallet, ready: true },
  { href: "/org/reviews", label: "Отзывы", icon: Star, ready: false },
];

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

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-14 items-center gap-2 border-b px-4 font-semibold">
          <span className="flex size-7 items-center justify-center rounded-lg bg-brand text-xs font-bold text-white">
            le
          </span>
          <span className="truncate text-sm">{current.company.name}</span>
        </div>
        <nav className="flex-1 space-y-0.5 p-2">
          {NAV.map((item) =>
            item.ready ? (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium",
                  pathname === item.href
                    ? "bg-primary text-primary-foreground"
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
        <div className="border-t p-2">
          <button
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground"
            onClick={() => {
              logout();
              router.replace("/");
            }}
          >
            <LogOut className="size-4" />
            Выйти
          </button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 bg-background">
        <div className="mx-auto w-full max-w-4xl px-4 py-8">{children}</div>
      </main>
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
