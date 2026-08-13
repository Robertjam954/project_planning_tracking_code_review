import type { ReactNode } from "react";
import { BotIcon, UserIcon } from "./icons";

interface BubbleProps {
  children: ReactNode;
}

function Avatar({ variant }: { variant: "human" | "ai" }) {
  return (
    <div
      className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center bg-surface-tertiary border border-border ${
        variant === "ai" ? "text-primary" : ""
      }`}
    >
      {variant === "human" ? <UserIcon /> : <BotIcon />}
    </div>
  );
}

const CHAT_TURN_TEST_ID = "sdk-preview-chat-turn" as const;

export function HumanBubble({ children }: BubbleProps) {
  return (
    <div className="flex justify-end items-end gap-2" data-testid={CHAT_TURN_TEST_ID}>
      <div className="max-w-[80%] rounded-xl rounded-br-sm bg-primary-dark text-white px-4 py-3 text-sm leading-relaxed">
        {children}
      </div>
      <Avatar variant="human" />
    </div>
  );
}

export function AIBubble({ children }: BubbleProps) {
  return (
    <div className="flex justify-start items-end gap-2" data-testid={CHAT_TURN_TEST_ID}>
      <Avatar variant="ai" />
      <div className="max-w-[80%] rounded-xl rounded-bl-sm bg-surface-secondary border border-border text-text px-4 py-3 text-sm leading-relaxed">
        {children}
      </div>
    </div>
  );
}
