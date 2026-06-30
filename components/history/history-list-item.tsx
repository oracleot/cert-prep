"use client";

import { Button } from "@/components/ui/button";
import type { SessionHistoryItem } from "@/lib/types";

type Props = {
  item: SessionHistoryItem;
  isSelected: boolean;
  isDeletePrompt: boolean;
  isDeleting: boolean;
  onSelect: (id: string) => void;
  onDeletePrompt: (id: string) => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: (id: string) => void;
};

export function HistoryListItem({
  item,
  isSelected,
  isDeletePrompt,
  isDeleting,
  onSelect,
  onDeletePrompt,
  onDeleteCancel,
  onDeleteConfirm,
}: Props) {
  return (
    <div
      className={
        isSelected
          ? "rounded-3xl border border-zinc-900 bg-zinc-950 p-4 text-zinc-50 dark:border-amber-300 dark:bg-amber-300 dark:text-zinc-950"
          : "rounded-3xl border border-transparent p-4 hover:bg-zinc-100 dark:hover:bg-zinc-900"
      }
    >
      <div className="flex items-start gap-3">
        <button type="button" onClick={() => onSelect(item.id)} className="min-w-0 flex-1 text-left" aria-pressed={isSelected}>
          <p
            className={
              isSelected
                ? "text-xs font-semibold uppercase tracking-[0.25em] opacity-70"
                : "text-xs font-semibold uppercase tracking-[0.25em] text-zinc-500 dark:text-zinc-400"
            }
          >
            {item.started_at ? new Date(item.started_at).toLocaleString() : "Unknown date"}
          </p>
          <h2 className="mt-2 truncate text-base font-black">{item.domain}</h2>
          <p
            className={
              isSelected
                ? "mt-1 line-clamp-2 text-sm opacity-80"
                : "mt-1 line-clamp-2 text-sm text-zinc-500 dark:text-zinc-400"
            }
          >
            {item.topic}
          </p>
        </button>
        {item.ended_at ? (
          isDeletePrompt ? (
            <div className="flex shrink-0 flex-col gap-2">
              <Button type="button" size="xs" variant="outline" onClick={onDeleteCancel} disabled={isDeleting}>
                Cancel
              </Button>
              <Button type="button" size="xs" variant="destructive" onClick={() => onDeleteConfirm(item.id)} disabled={isDeleting}>
                {isDeleting ? "Deleting..." : "Confirm"}
              </Button>
            </div>
          ) : (
            <Button type="button" size="xs" variant="ghost" onClick={() => onDeletePrompt(item.id)}>
              Delete
            </Button>
          )
        ) : null}
      </div>
    </div>
  );
}
