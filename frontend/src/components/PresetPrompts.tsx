interface PresetPromptsProps {
  prompts: string[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

export function PresetPrompts({ prompts, onSelect, disabled = false }: PresetPromptsProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-3">
      <div className="text-xs text-text-secondary font-medium">Try these prompts:</div>
      {prompts.map((prompt) => (
        <button
          key={prompt}
          type="button"
          onClick={() => onSelect(prompt)}
          disabled={disabled}
          className="rounded-lg border border-border bg-surface-secondary px-3 py-1.5 text-xs text-text-secondary hover:border-primary hover:text-primary disabled:opacity-40 transition-colors cursor-pointer"
        >
          {prompt}
        </button>
      ))}
    </div>
  );
}
