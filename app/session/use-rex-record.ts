"use client";

import { useCallback, useEffect, useState } from "react";

import { getAnonymousUserId } from "@/lib/anonymous-user";
import { getBrowserTimezone } from "@/lib/browser-timezone";
import type { RexRecord } from "@/lib/types";

const EMPTY_RECORD = { user_wins: 0, rex_wins: 0 };

export function useRexRecord() {
  const [rexRecord, setRexRecord] = useState<RexRecord>(EMPTY_RECORD);

  const refreshRexRecord = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard/summary", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: getAnonymousUserId(),
          timezone: getBrowserTimezone(),
        }),
      });
      if (!res.ok) return;
      const summary = await res.json();
      setRexRecord(summary.rex_record ?? EMPTY_RECORD);
    } catch {
      // Keep the session usable if the dashboard summary endpoint is offline.
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => void refreshRexRecord());
  }, [refreshRexRecord]);

  return { rexRecord, refreshRexRecord };
}
