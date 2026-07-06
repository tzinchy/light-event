"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { Loader2, MessageSquareText } from "lucide-react";
import { openThreadApiV1ChatThreadsPost } from "@light-event/shared-types";
import { Button } from "@/components/ui/button";

/** Открыть (или создать) чат-тред по заявке и перейти в переписку — общий для обеих сторон. */
export function ChatButton({
  applicationUuid,
  size = "sm",
  variant = "outline",
  label = "Чат",
}: {
  applicationUuid: string;
  size?: "sm" | "default";
  variant?: "outline" | "default" | "ghost";
  label?: string;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function open() {
    setBusy(true);
    const { data, error } = await openThreadApiV1ChatThreadsPost({
      body: { application_uuid: applicationUuid },
    });
    setBusy(false);
    if (error || !data) {
      toast.error(String((error as { detail?: string })?.detail ?? "Не удалось открыть чат"));
      return;
    }
    router.push(`/chat/${(data as { chat_thread_uuid: string }).chat_thread_uuid}`);
  }

  return (
    <Button size={size} variant={variant} disabled={busy} onClick={() => void open()}>
      {busy ? <Loader2 className="size-4 animate-spin" /> : <MessageSquareText className="size-4" />}
      {label}
    </Button>
  );
}
