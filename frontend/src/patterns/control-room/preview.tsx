import { useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";

import { AGENT_SERVER_URL, ASSISTANT_ID } from "@/agent-config";
import { ChatContainer } from "@/components/ChatContainer";
import { AIBubble, HumanBubble } from "@/components/Bubble";
import { ChatInput } from "@/components/ChatInput";
import { TypingIndicator } from "@/components/TypingIndicator";
import { PresetPrompts } from "@/components/PresetPrompts";
import { Markdown } from "@/components/Markdown";

const PRESETS = [
  "How is the portfolio doing? Which projects are stalled?",
  "Plan a new agentic app for a customer-support triage bot",
  "What are the most common code-quality issues across our repos?",
  "What did we discuss in my last session?",
];

function messageText(msg: Message): string {
  if (typeof msg.content === "string") return msg.content;
  return msg.content
    .map((part) => (typeof part === "string" ? part : "text" in part ? part.text : ""))
    .join("");
}

export default function ControlRoomChat() {
  const [threadId, setThreadId] = useState<string | null>(null);

  const stream = useStream({
    apiUrl: AGENT_SERVER_URL,
    assistantId: ASSISTANT_ID,
    threadId,
    onThreadId: setThreadId,
  });

  const handleSubmit = (text: string) => {
    stream.submit({ messages: [{ type: "human", content: text }] });
  };

  const header = (
    <div className="flex items-center justify-between">
      <div>
        <div className="text-sm font-semibold text-text">Control Room</div>
        <div className="text-xs text-text-tertiary">
          Supervisor · Planner · Tracker · Reviewer · Historian
        </div>
      </div>
    </div>
  );

  return (
    <ChatContainer
      header={header}
      input={
        <ChatInput
          onSubmit={handleSubmit}
          disabled={stream.isLoading}
          onNewThread={stream.messages.length > 0 ? () => setThreadId(null) : undefined}
        />
      }
    >
      {stream.messages.length === 0 && !stream.error && (
        <PresetPrompts prompts={PRESETS} onSelect={handleSubmit} disabled={stream.isLoading} />
      )}

      {stream.messages.map((msg) => {
        const text = messageText(msg);
        if (!text) return null;
        if (msg.type === "human") {
          return (
            <HumanBubble key={msg.id}>
              <Markdown>{text}</Markdown>
            </HumanBubble>
          );
        }
        if (msg.type === "ai") {
          return (
            <AIBubble key={msg.id}>
              <Markdown>{text}</Markdown>
            </AIBubble>
          );
        }
        return null;
      })}

      {stream.isLoading && <TypingIndicator />}

      {stream.error != null && (
        <div className="rounded-lg border border-error/40 bg-error/5 px-4 py-3 text-sm text-error">
          <div className="font-medium">Something went wrong.</div>
          <div className="mt-1 text-xs text-error/80">
            {stream.error instanceof Error ? stream.error.message : String(stream.error)}
          </div>
          <div className="mt-2 text-xs text-text-tertiary">
            Is the agent server running? Start it with{" "}
            <code className="rounded bg-primary-dark/8 px-1 py-0.5">langgraph dev</code> in the repo
            root, then retry.
          </div>
        </div>
      )}
    </ChatContainer>
  );
}
