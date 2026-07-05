"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Loader2, MessagesSquare } from "lucide-react";
import { myThreadsApiV1ChatThreadsGet, type ThreadOut } from "@light-event/shared-types";
import { Card, CardContent } from "@/components/ui/card";
import { SiteHeader } from "@/components/site-header";
import { formatDateTime } from "@/lib/format";

export default function ChatListPage() {
  const [threads, setThreads] = useState<ThreadOut[] | null>(null);

  useEffect(() => {
    void (async () => {
      const { data } = await myThreadsApiV1ChatThreadsGet();
      setThreads(data ?? []);
    })();
  }, []);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl flex-1 px-4 py-8">
        <h1 className="text-xl font-semibold">Чаты</h1>

        <div className="mt-5 space-y-2">
          {threads === null ? (
            <div className="mt-16 flex justify-center text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
            </div>
          ) : threads.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <MessagesSquare className="size-8 text-muted-foreground" />
                <p className="mt-3 text-sm text-muted-foreground">
                  Нет диалогов. Чат открывается из карточки заявки.
                </p>
              </CardContent>
            </Card>
          ) : (
            threads.map((thread) => (
              <Link key={thread.chat_thread_uuid} href={`/chat/${thread.chat_thread_uuid}`}>
                <Card className="transition-colors hover:bg-secondary">
                  <CardContent className="flex items-center gap-3 py-4">
                    <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-semibold text-brand-strong">
                      {(thread.counterpart_name ?? "?").slice(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate font-medium">{thread.counterpart_name}</span>
                        {thread.last_message && (
                          <span className="shrink-0 text-xs text-muted-foreground">
                            {formatDateTime(thread.last_message.sent_at)}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm text-muted-foreground">
                          {thread.last_message?.text ?? `${thread.role_name} · ${thread.event_title}`}
                        </span>
                        {thread.unread_count > 0 && (
                          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-brand text-[10px] font-bold text-white">
                            {thread.unread_count}
                          </span>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          )}
        </div>
      </main>
    </div>
  );
}
