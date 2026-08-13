import { useRef, useEffect, type ReactNode } from "react";

interface ChatContainerProps {
  children: ReactNode;
  input: ReactNode;
  header?: ReactNode;
  className?: string;
}

export function ChatContainer({ children, input, header, className = "" }: ChatContainerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  });

  return (
    <div className={`flex flex-col bg-surface h-screen ${className}`}>
      {header && (
        <div className="shrink-0 border-b border-border px-4 py-3">{header}</div>
      )}
      <div
        ref={scrollRef}
        data-testid="sdk-preview-messages"
        className="min-h-0 flex-1 overflow-y-auto px-4 py-4 space-y-4"
      >
        {children}
      </div>
      {input && <div className="shrink-0 border-t border-border px-4 py-3">{input}</div>}
    </div>
  );
}
