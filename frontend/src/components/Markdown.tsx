import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ComponentPropsWithoutRef } from "react";

interface MarkdownProps {
  children: string;
  className?: string;
}

export function Markdown({ children, className }: MarkdownProps) {
  return (
    <div className={`markdown-content ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: (props: ComponentPropsWithoutRef<"pre">) => (
            <pre className="overflow-x-auto rounded-md bg-primary-dark/5 p-2 text-xs" {...props} />
          ),
          code: ({ children, className: codeClass, ...rest }: ComponentPropsWithoutRef<"code">) => {
            const isInline = !codeClass;
            return isInline ? (
              <code className="rounded bg-primary-dark/8 px-1 py-0.5 text-xs" {...rest}>
                {children}
              </code>
            ) : (
              <code className={codeClass} {...rest}>
                {children}
              </code>
            );
          },
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
