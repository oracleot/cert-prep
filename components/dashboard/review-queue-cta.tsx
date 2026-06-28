"use client";

import Link from "next/link";

type Props = {
  count: number;
  loading?: boolean;
  error?: boolean;
};

// CTA tile surfaced on the dashboard when the spaced-repetition queue has
// items due. Renders a skeleton while loading and hides entirely on error so
// the dashboard never breaks because the queue endpoint is unavailable.
export function ReviewQueueCta({ count, loading = false, error = false }: Props) {
  if (error) return null;
  if (loading) {
    return (
      <div className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="h-5 w-40 animate-pulse rounded-full bg-zinc-200 dark:bg-zinc-800" />
      </div>
    );
  }
  if (count <= 0) return null;
  return (
    <Link
      href="/review"
      className="inline-flex min-h-11 items-center rounded-full border border-amber-300 bg-amber-300/10 px-5 text-sm font-black text-amber-800 hover:border-amber-500 dark:bg-amber-300/15 dark:text-amber-200"
      aria-label={`Review Queue: ${count} concepts due for review`}
    >
      📚 Review Queue ({count} due)
    </Link>
  );
}
