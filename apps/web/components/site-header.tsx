"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { DICT } from "@/lib/dict";
import { useAuth } from "@/lib/auth-context";

export function SiteHeader() {
  const { me, loading } = useAuth();

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
                <Button asChild variant="ghost" size="sm">
                  <Link href="/profile">Профиль</Link>
                </Button>
                <Button asChild variant="ghost" size="sm">
                  <Link href="/apps">{DICT.myApps}</Link>
                </Button>
                <Button asChild variant="ghost" size="sm">
                  <Link href="/tests">{DICT.testsTab}</Link>
                </Button>
                <Button asChild size="sm">
                  <Link href="/org">{DICT.openOrgConsole}</Link>
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
