"use client";

import { useCallback, useEffect, useState } from "react";

import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getBrowserTimezone } from "@/lib/browser-timezone";
import type { RexRecord } from "@/lib/types";
import { useActiveExamId } from "./session-scope";

const EMPTY_RECORD = { user_wins: 0, rex_wins: 0 };

/**
 * Reads Rex's win/loss record from the dashboard summary endpoint, scoped to
 * the active curriculum via `exam_id`. The active exam is re-read at refresh
 * time (not at hook-render time) so a curriculum swap in Settings immediately
 * causes the next refresh to query the right exam.
 *
 * Only reads from server-side state — no client-side persistence keyed by
 * `thread_id`, so no composite key work is needed here.
 */
export function useRexRecord() {
  const [rexRecord, setRexRecord] = useState<RexRecord>(EMPTY_RECORD);
  const examId = useActiveExamId();

  const refreshRexRecord = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: getAnonymousUserId(),
          timezone: getBrowserTimezone(),
          ...(examId ? { exam_id: examId } : {}),
        }),
      });
      if (!res.ok) return;
      const summary = await res.json();
      setRexRecord(summary.rex_record ?? EMPTY_RECORD);
    } catch {
      // Keep the session usable if the dashboard summary endpoint is offline.
    }
  }, [examId]);

  useEffect(() => {
    queueMicrotask(() => void refreshRexRecord());
  }, [refreshRexRecord]);

  return { rexRecord, refreshRexRecord };
}
