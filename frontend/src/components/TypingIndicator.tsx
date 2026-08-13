export function TypingIndicator() {
  return (
    <div className="flex justify-start" data-testid="sdk-preview-chat-turn">
      <div className="bg-surface-secondary border border-border rounded-xl rounded-bl-sm px-4 py-3">
        <div className="flex gap-1.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-primary animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
