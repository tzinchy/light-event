"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarDays, ClipboardList, MessagesSquare, Newspaper, UserRound } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

// нижний таб-бар мобильной версии (PLAN §5): Лента / Заявки / Чат / Тесты / Профиль
const TABS = [
  { href: "/feed", label: "Лента", icon: Newspaper },
  { href: "/apps", label: "Заявки", icon: CalendarDays },
  { href: "/chat", label: "Чат", icon: MessagesSquare },
  { href: "/tests", label: "Тесты", icon: ClipboardList },
  { href: "/profile", label: "Профиль", icon: UserRound },
];

// в кабинетах организации/админа и на входе — своя навигация; в треде чата снизу композер
const HIDDEN_PREFIXES = ["/org", "/admin", "/auth", "/join"];

export function MobileTabBar() {
  const pathname = usePathname();
  const { me } = useAuth();

  const hidden =
    !me ||
    HIDDEN_PREFIXES.some((p) => pathname.startsWith(p)) ||
    /^\/chat\/.+/.test(pathname);
  if (hidden) return null;

  return (
    <>
      {/* распорка, чтобы контент не прятался за фиксированным баром */}
      <div className="h-16 md:hidden" />
      <nav
        className="fixed inset-x-0 bottom-0 z-40 border-t bg-background/95 backdrop-blur md:hidden"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        <div className="mx-auto flex max-w-md items-stretch justify-around">
          {TABS.map((tab) => {
            const active = pathname === tab.href || pathname.startsWith(tab.href + "/");
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium",
                  active ? "text-brand-strong" : "text-muted-foreground",
                )}
              >
                <tab.icon className={cn("size-5", active && "text-brand")} />
                {tab.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
