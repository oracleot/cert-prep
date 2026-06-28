"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useActiveCurriculum } from "@/lib/active-curriculum";
import { getExamName } from "@/lib/exam-names";
import { useHydrated } from "@/lib/use-hydrated";

import { ThemeToggle } from "./theme-toggle";

export function AppNav() {
  const pathname = usePathname();
  const isDashboard = pathname === "/dashboard";
  const isHistory = pathname === "/history";
  const isLessons = pathname.startsWith("/lessons");
  const isProgress = pathname === "/progress";
  const isReview = pathname === "/review";
  const isSettings = pathname === "/settings";
  const hydrated = useHydrated();
  const { active } = useActiveCurriculum();
  const showExamBadge = hydrated && active !== null;
  const badgeLabel = showExamBadge ? getExamName(active.exam_id) : "";

  return (
    <nav className="flex flex-wrap items-center justify-between gap-3 text-sm">
      <Link
        href="/dashboard"
        className="font-black uppercase tracking-[0.25em] text-zinc-950 dark:text-zinc-100"
      >
        Gauntlet
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        {showExamBadge ? (
          <Link
            href="/settings"
            aria-label={`Active exam: ${badgeLabel}. Open settings to switch.`}
            className="rounded-full border border-zinc-200 px-3 py-2 text-xs text-zinc-500 dark:border-zinc-800 dark:text-zinc-400"
          >
            <span className="font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">Exam</span>
            <span className="ml-2 font-black text-zinc-700 dark:text-zinc-200">{badgeLabel}</span>
          </Link>
        ) : null}
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
        {!isLessons ? (
          <Link
            href="/lessons"
            className="rounded-full border border-zinc-200 px-4 py-2 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            Lessons
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
        {!isReview ? (
          <Link
            href="/review"
            className="rounded-full border border-zinc-200 px-4 py-2 text-zinc-700 dark:border-zinc-800 dark:text-zinc-300"
          >
            Review
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
