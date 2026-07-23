"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Bell, LogOut } from "lucide-react";
import {
  listNotificationsApiV1NotificationsGet,
  myCompaniesApiV1CompaniesMyGet,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";

export function SiteHeader() {
  const { me, loading, logout } = useAuth();
  const router = useRouter();
  // кнопка кабинета — только у участников компании; обычному пользователю её не показываем
  const [isMember, setIsMember] = useState(false);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!me) {
      setIsMember(false);
      setUnread(0);
      return;
    }
    let active = true;
    void (async () => {
      const [companies, notifs] = await Promise.all([
        myCompaniesApiV1CompaniesMyGet(),
        listNotificationsApiV1NotificationsGet(),
      ]);
      if (!active) return;
      setIsMember((companies.data ?? []).length > 0);
      setUnread(notifs.data?.unread ?? 0);
    })();
    return () => {
      active = false;
    };
  }, [me]);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-6xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="flex size-7 items-center justify-center rounded-lg bg-brand text-xs font-bold text-white">
            le
          </span>
          light-event
        </Link>
        {!loading && (
          <nav className="flex items-center gap-2">
            {me ? (
              <>
                {/* на <md текстовые пункты заменяет нижний таб-бар */}
                <div className="hidden items-center gap-2 md:flex">
                  <Button asChild variant="ghost" size="sm">
                    <Link href="/feed">Лента</Link>
                  </Button>
                  <Button asChild variant="ghost" size="sm">
                    <Link href="/apps">{DICT.myApps}</Link>
                  </Button>
                  <Button asChild variant="ghost" size="sm">
                    <Link href="/chat">Чаты</Link>
                  </Button>
                  <Button asChild variant="ghost" size="sm">
                    <Link href="/tests">{DICT.testsTab}</Link>
                  </Button>
                  <Button asChild variant="ghost" size="sm">
                    <Link href="/profile">Профиль</Link>
                  </Button>
                </div>
                <Button asChild variant="ghost" size="icon" className="relative">
                  <Link href="/notifications" aria-label="Уведомления">
                    <Bell className="size-4" />
                    {unread > 0 && (
                      <span className="absolute -right-0.5 -top-0.5 flex min-w-4 items-center justify-center rounded-full bg-brand px-1 text-[10px] font-bold text-white">
                        {unread}
                      </span>
                    )}
                  </Link>
                </Button>
                {me.platform_role === "admin" && (
                  <Button asChild size="sm">
                    <Link href="/admin">Админка</Link>
                  </Button>
                )}
                {isMember && (
                  <Button asChild size="sm">
                    <Link href="/org">{DICT.openOrgConsole}</Link>
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Выйти"
                  title="Выйти"
                  onClick={() => {
                    logout();
                    router.replace("/");
                  }}
                >
                  <LogOut className="size-4" />
                </Button>
              </>
            ) : (
              <>
                <Button asChild variant="ghost" size="sm">
                  <Link href="/auth">{DICT.signIn}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link href="/auth">{DICT.signUpFree}</Link>
                </Button>
              </>
            )}
          </nav>
        )}
      </div>
    </header>
  );
}
