"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { cn } from "@/lib/utils";

const OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
] as const;

type ThemeValue = (typeof OPTIONS)[number]["value"];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const current: ThemeValue = (theme as ThemeValue) ?? "system";

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="inline-flex items-center gap-0.5 rounded-full border border-zinc-200 bg-white/60 p-0.5 text-zinc-700 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/60 dark:text-zinc-300"
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const isActive = current === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={isActive}
            aria-label={label}
            title={label}
            onClick={() => setTheme(value)}
            className={cn(
              "inline-flex h-8 w-8 items-center justify-center rounded-full transition-colors",
              isActive
                ? "bg-amber-300 text-zinc-950 shadow-sm"
                : "hover:bg-zinc-100 dark:hover:bg-zinc-800",
            )}
          >
            <Icon
              aria-hidden
              className={cn(
                "size-4",
                isActive ? "text-zinc-950" : "text-current",
              )}
            />
          </button>
        );
      })}
    </div>
  );
}
