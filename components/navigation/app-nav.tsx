"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ThemeToggle } from "./theme-toggle";

export function AppNav() {
  const pathname = usePathname();
  const isDashboard = pathname === "/dashboard";
  const isHistory = pathname === "/history";
  const isProgress = pathname === "/progress";
  const isSettings = pathname === "/settings";

  return (
    <nav className="flex flex-wrap items-center justify-between gap-3 text-sm">
      <Link
        href="/dashboard"
        className="font-black uppercase tracking-[0.25em] text-zinc-950 dark:text-zinc-100"
      >
        Gauntlet
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        <ThemeToggle />
        {!isDashboard ? (
          <Link
            href="/dashboard"
            className="rounded-full border border-zinc-200 px-4 py-2 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            Dashboard
          </Link>
        ) : null}
        {!isHistory ? (
          <Link
            href="/history"
            className="rounded-full border border-zinc-200 px-4 py-2 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            History
          </Link>
        ) : null}
        {!isProgress ? (
          <Link
            href="/progress"
            className="rounded-full border border-zinc-200 px-4 py-2 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            Progress
          </Link>
        ) : null}
        {!isSettings ? (
          <Link
            href="/settings"
            className="rounded-full border border-zinc-200 px-3 py-2 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400"
          >
            Settings
          </Link>
        ) : null}
        {!isDashboard ? (
          <Link
            href="/session"
            className="rounded-full bg-amber-300 px-4 py-2 font-black text-zinc-950"
          >
            Start session
          </Link>
        ) : null}
      </div>
    </nav>
  );
}
