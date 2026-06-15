// Client-side SSE stream reader utility

import type { SseEvent } from "./openrouter";

type SseCallback = (event: SseEvent) => void;

/**
 * Reads a ReadableStream of SSE-encoded SseEvent objects and invokes
 * the callback for each parsed event. Used on the client to consume
 * Sage streaming responses from /api/sage.
 */
export async function readSseStream(
  body: ReadableStream<Uint8Array>,
  onEvent: SseCallback,
): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        try {
          const event = JSON.parse(payload) as SseEvent;
          onEvent(event);
        } catch {
          // Skip malformed SSE events
        }
      }
    }

    // Drain remaining buffer
    if (buffer.trim().startsWith("data:")) {
      const payload = buffer.trim().slice(5).trim();
      try {
        const event = JSON.parse(payload) as SseEvent;
        onEvent(event);
      } catch {
        // ignore
      }
    }
  } finally {
    reader.releaseLock();
  }
}
