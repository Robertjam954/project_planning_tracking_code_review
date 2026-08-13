import { useState, type FormEvent } from "react";

interface ChatInputProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
  placeholder?: string;
  onNewThread?: () => void;
}

export function ChatInput({
  onSubmit,
  disabled = false,
  placeholder = "Ask about the portfolio, plan a project, recall a session...",
  onNewThread,
}: ChatInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSubmit(trimmed);
    setText("");
  };

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={disabled || !text.trim()}
          className="rounded-lg bg-primary-dark px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
        >
          Send
        </button>
      </form>
      {onNewThread && (
        <button
          type="button"
          onClick={onNewThread}
          className="rounded-lg border border-border bg-surface-secondary px-3 py-1.5 text-xs text-text-secondary hover:border-primary hover:text-primary transition-colors cursor-pointer"
        >
          + New session
        </button>
      )}
    </div>
  );
}
