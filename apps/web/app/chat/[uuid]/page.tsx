"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft, Loader2, Pencil, SendHorizonal, Trash2, X } from "lucide-react";
import {
  deleteMessageApiV1ChatMessagesChatMessageUuidDelete,
  editMessageApiV1ChatMessagesChatMessageUuidPatch,
  markReadApiV1ChatThreadsChatThreadUuidReadPost,
  myThreadsApiV1ChatThreadsGet,
  sendMessageApiV1ChatThreadsChatThreadUuidMessagesPost,
  threadMessagesApiV1ChatThreadsChatThreadUuidMessagesGet,
  type MessageOut,
  type ThreadOut,
} from "@light-event/shared-types";
import { Button } from "@/components/ui/button";
import { SiteHeader } from "@/components/site-header";
import { getTokens } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

function timeOf(iso: string): string {
  return new Date(iso).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

export default function ChatThreadPage() {
  const { uuid } = useParams<{ uuid: string }>();
  const { me } = useAuth();
  const [thread, setThread] = useState<ThreadOut | null>(null);
  const [messages, setMessages] = useState<MessageOut[] | null>(null);
  const [online, setOnline] = useState(false);
  const [text, setText] = useState("");
  const [editing, setEditing] = useState<MessageOut | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const load = useCallback(async () => {
    const [msgs, threads] = await Promise.all([
      threadMessagesApiV1ChatThreadsChatThreadUuidMessagesGet({ path: { chat_thread_uuid: uuid } }),
      myThreadsApiV1ChatThreadsGet(),
    ]);
    setMessages(msgs.data ?? []);
    setThread((threads.data ?? []).find((t) => t.chat_thread_uuid === uuid) ?? null);
    void markReadApiV1ChatThreadsChatThreadUuidReadPost({ path: { chat_thread_uuid: uuid } });
  }, [uuid]);

  useEffect(() => {
    void load();
  }, [load]);

  // realtime: WebSocket — доставка, правки, удаления, онлайн-статус (переподключение при обрыве)
  useEffect(() => {
    const tokens = getTokens();
    if (!tokens || !me) return;
    let closedByUs = false;
    let ws: WebSocket;

    const applyUpdate = (updated: MessageOut) =>
      setMessages((prev) =>
        prev?.map((m) => (m.chat_message_uuid === updated.chat_message_uuid ? updated : m)) ?? prev,
      );

    const connect = () => {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/ws/chat?token=${tokens.access}`);
      wsRef.current = ws;
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data) as
          | ({ type: "message" | "message_edited" | "message_deleted" } & MessageOut)
          | { type: "presence"; user_uuid: string; online: boolean }
          | { type: "read"; chat_thread_uuid: string; reader_uuid: string };
        if (data.type === "message" && data.chat_thread_uuid === uuid) {
          setMessages((prev) =>
            prev?.some((m) => m.chat_message_uuid === data.chat_message_uuid)
              ? prev
              : [...(prev ?? []), data],
          );
          if (data.sender_uuid !== me.user_uuid) {
            ws.send(JSON.stringify({ type: "read", chat_thread_uuid: uuid }));
          }
        } else if (
          (data.type === "message_edited" || data.type === "message_deleted") &&
          data.chat_thread_uuid === uuid
        ) {
          applyUpdate(data);
        } else if (data.type === "presence" && data.user_uuid !== me.user_uuid) {
          setOnline(data.online);
        }
      };
      ws.onclose = () => {
        if (!closedByUs) setTimeout(connect, 2000);
      };
    };
    connect();

    return () => {
      closedByUs = true;
      wsRef.current?.close();
    };
  }, [uuid, me]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages?.length]);

  async function send() {
    const body = text.trim();
    if (!body) return;
    if (editing) {
      const { data } = await editMessageApiV1ChatMessagesChatMessageUuidPatch({
        path: { chat_message_uuid: editing.chat_message_uuid },
        body: { text: body },
      });
      if (data) {
        setMessages((prev) =>
          prev?.map((m) => (m.chat_message_uuid === data.chat_message_uuid ? data : m)) ?? prev,
        );
      }
      setEditing(null);
      setText("");
      return;
    }
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "send", chat_thread_uuid: uuid, text: body }));
      setText("");
    } else {
      const { error } = await sendMessageApiV1ChatThreadsChatThreadUuidMessagesPost({
        path: { chat_thread_uuid: uuid },
        body: { text: body },
      });
      if (!error) {
        setText("");
        await load();
      }
    }
  }

  async function remove(message: MessageOut) {
    const { data } = await deleteMessageApiV1ChatMessagesChatMessageUuidDelete({
      path: { chat_message_uuid: message.chat_message_uuid },
    });
    if (data) {
      setMessages((prev) =>
        prev?.map((m) => (m.chat_message_uuid === data.chat_message_uuid ? data : m)) ?? prev,
      );
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col px-4 py-4">
        <div className="flex items-center gap-3 border-b pb-3">
          <Link href="/chat" className="text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-5" />
          </Link>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate font-semibold">{thread?.counterpart_name ?? "Чат"}</span>
              {online && (
                <span className="flex items-center gap-1 text-xs text-brand">
                  <span className="size-1.5 rounded-full bg-brand" />
                  онлайн
                </span>
              )}
            </div>
            {thread && (
              <Link
                href={`/shift/${thread.vacancy_uuid}`}
                className="block truncate text-xs text-muted-foreground hover:text-foreground hover:underline"
              >
                Событие: {thread.event_title} · {thread.role_name} →
              </Link>
            )}
          </div>
        </div>

        <div className="flex-1 space-y-2 overflow-y-auto py-4">
          {messages === null ? (
            <div className="mt-16 flex justify-center text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <p className="mt-16 text-center text-sm text-muted-foreground">
              Сообщений пока нет — напишите первым.
            </p>
          ) : (
            messages.map((message) => {
              const mine = message.sender_uuid === me?.user_uuid;
              const deleted = message.deleted_at != null;
              return (
                <div key={message.chat_message_uuid} className={cn("group flex", mine && "justify-end")}>
                  <div className={cn("flex max-w-[80%] items-end gap-1.5", mine && "flex-row-reverse")}>
                    <div
                      className={cn(
                        "rounded-2xl px-3.5 py-2 text-sm",
                        mine
                          ? "rounded-br-md bg-primary text-primary-foreground"
                          : "rounded-bl-md bg-secondary",
                        deleted && "italic opacity-60",
                      )}
                    >
                      {deleted ? "Сообщение удалено" : message.text}
                      <div
                        className={cn(
                          "mt-0.5 text-right text-[10px]",
                          mine ? "text-primary-foreground/70" : "text-muted-foreground",
                        )}
                      >
                        {timeOf(message.sent_at)}
                        {message.edited_at && !deleted && (
                          <span title={`Изменено в ${timeOf(message.edited_at)}`}> · изменено</span>
                        )}
                      </div>
                    </div>
                    {mine && !deleted && (
                      <div className="mb-1 hidden shrink-0 gap-1 group-hover:flex">
                        <button
                          className="text-muted-foreground hover:text-foreground"
                          title="Изменить"
                          onClick={() => {
                            setEditing(message);
                            setText(message.text);
                          }}
                        >
                          <Pencil className="size-3.5" />
                        </button>
                        <button
                          className="text-muted-foreground hover:text-status-danger"
                          title="Удалить"
                          onClick={() => void remove(message)}
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
          <div ref={bottomRef} />
        </div>

        {editing && (
          <div className="flex items-center justify-between rounded-t-lg border border-b-0 bg-secondary/50 px-3 py-1.5 text-xs">
            <span className="text-muted-foreground">Редактирование сообщения</span>
            <button
              className="text-muted-foreground hover:text-foreground"
              onClick={() => {
                setEditing(null);
                setText("");
              }}
            >
              <X className="size-3.5" />
            </button>
          </div>
        )}
        <form
          className={cn("flex gap-2 pt-3", editing ? "border-t-0" : "border-t")}
          onSubmit={(e) => {
            e.preventDefault();
            void send();
          }}
        >
          <input
            className="h-10 flex-1 rounded-full border bg-transparent px-4 text-sm outline-none focus:border-ring focus:ring-2 focus:ring-ring/30"
            placeholder={editing ? "Новый текст сообщения" : "Сообщение"}
            aria-label="Сообщение"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <Button type="submit" size="icon" className="size-10 rounded-full" disabled={!text.trim()}>
            <SendHorizonal className="size-4" />
          </Button>
        </form>
      </main>
    </div>
  );
}
