"use client";

import { HistoryListItem } from "./history-list-item";
import type { SessionHistoryItem } from "@/lib/types";

type Props = {
  items: SessionHistoryItem[];
  selectedId: string | null;
  deletePromptId: string | null;
  deletingId: string | null;
  onSelect: (id: string) => void;
  onDeletePrompt: (id: string) => void;
  onDeleteCancel: () => void;
  onDeleteConfirm: (id: string) => void;
};

export function HistoryList({
  items,
  selectedId,
  deletePromptId,
  deletingId,
  onSelect,
  onDeletePrompt,
  onDeleteCancel,
  onDeleteConfirm,
}: Props) {
  return (
    <div className="grid gap-2">
      {items.map((item) => (
        <HistoryListItem
          key={item.id}
          item={item}
          isSelected={selectedId === item.id}
          isDeletePrompt={deletePromptId === item.id}
          isDeleting={deletingId === item.id}
          onSelect={onSelect}
          onDeletePrompt={onDeletePrompt}
          onDeleteCancel={onDeleteCancel}
          onDeleteConfirm={onDeleteConfirm}
        />
      ))}
    </div>
  );
}
