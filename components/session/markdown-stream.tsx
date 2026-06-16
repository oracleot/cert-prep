"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

type Props = {
  text: string;
  className?: string;
};

export function MarkdownStream({ text, className }: Props) {
  return (
    <div className={className}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="mt-3 text-lg font-black tracking-tight text-zinc-950 first:mt-0 dark:text-zinc-50">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="mt-3 text-base font-black tracking-tight text-zinc-950 first:mt-0 dark:text-zinc-50">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="mt-2 text-sm font-black uppercase tracking-wider text-zinc-950 first:mt-0 dark:text-zinc-50">
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p className="my-1.5 text-sm leading-relaxed text-zinc-700 first:mt-0 last:mb-0 dark:text-zinc-100">
              {children}
            </p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-zinc-950 dark:text-zinc-50">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-zinc-950 dark:text-zinc-50">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="my-1.5 list-disc space-y-1 pl-5 text-sm leading-relaxed text-zinc-700 dark:text-zinc-100">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-1.5 list-decimal space-y-1 pl-5 text-sm leading-relaxed text-zinc-700 dark:text-zinc-100">
              {children}
            </ol>
          ),
          li: ({ children }) => <li className="pl-1">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="my-2 border-l-2 border-amber-400/70 pl-3 text-sm italic text-zinc-600 dark:border-amber-300/70 dark:text-zinc-300">
              {children}
            </blockquote>
          ),
          code: ({ className: codeClass, children }) => {
            const isBlock = codeClass?.includes("language-");
            if (isBlock) {
              return (
                <code className="block whitespace-pre overflow-x-auto rounded-md bg-zinc-100 px-3 py-2 font-mono text-xs leading-relaxed text-zinc-800 dark:bg-zinc-800/80 dark:text-zinc-100">
                  {children}
                </code>
              );
            }
            return (
              <code className="rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-[0.85em] text-zinc-800 dark:bg-zinc-800/80 dark:text-zinc-100">
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="my-2 overflow-x-auto rounded-md bg-zinc-100 p-3 font-mono text-xs leading-relaxed text-zinc-800 dark:bg-zinc-800/80 dark:text-zinc-100">
              {children}
            </pre>
          ),
          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noreferrer"
              className="text-amber-700 underline underline-offset-2 hover:text-amber-600 dark:text-amber-300 dark:hover:text-amber-200"
            >
              {children}
            </a>
          ),
          hr: () => <hr className="my-3 border-border" />,
        }}
      >
        {text}
      </Markdown>
    </div>
  );
}
