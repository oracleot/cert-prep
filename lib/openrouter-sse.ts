// SSE encoding/decoding helpers for the OpenRouter streaming client.
// Converts upstream OpenRouter chunks into the discriminated SseEvent union
// and wraps error/stream results as Response objects the route handlers return.

import type { OpenRouterError, SseEvent } from "./openrouter-types";

function encodeEvent(event: SseEvent): Uint8Array {
  return new TextEncoder().encode(`data: ${JSON.stringify(event)}\n\n`);
}

function extractToken(payload: string): string {
  try {
    const parsed = JSON.parse(payload) as {
      choices?: Array<{
        delta?: {
          content?: string | Array<{ type?: string; text?: string }>;
        };
      }>;
    };

    const content = parsed.choices?.[0]?.delta?.content;
    if (typeof content === "string") {
      return content;
    }

    if (Array.isArray(content)) {
      return content
        .filter((part) => typeof part?.text === "string")
        .map((part) => part.text)
        .join("");
    }

    return "";
  } catch {
    return "";
  }
}

export function toSseStream(
  upstreamBody: ReadableStream<Uint8Array>,
): ReadableStream<Uint8Array> {
  const decoder = new TextDecoder();
  const reader = upstreamBody.getReader();

  return new ReadableStream<Uint8Array>({
    async start(controller) {
      let buffer = "";

      const flush = () => {
        // Emit any data left in the buffer when the stream closes without [DONE].
        const remaining = buffer.trim();
        if (remaining.startsWith("data:")) {
          const token = extractToken(remaining.slice(5).trim());
          if (token) controller.enqueue(encodeEvent({ type: "token", token }));
        }
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            flush();
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line || !line.startsWith("data:")) continue;

            const payload = line.slice(5).trim();
            if (payload === "[DONE]") {
              controller.enqueue(encodeEvent({ type: "done" }));
              controller.close();
              // Cancel the upstream so buffered bytes are released immediately.
              reader.cancel().catch(() => undefined);
              return;
            }

            const token = extractToken(payload);
            if (token) {
              controller.enqueue(encodeEvent({ type: "token", token }));
            }
          }
        }

        controller.enqueue(encodeEvent({ type: "done" }));
        controller.close();
      } catch (error) {
        // Use the same SseEvent shape as openRouterErrorToSseResponse.
        const streamError: OpenRouterError = {
          code: "STREAM_ERROR",
          message:
            error instanceof Error
              ? error.message
              : "Unknown stream parsing error",
        };
        controller.enqueue(encodeEvent({ type: "error", error: streamError }));
        controller.close();
      } finally {
        reader.releaseLock();
      }
    },
  });
}

export function openRouterErrorToSseResponse(error: OpenRouterError): Response {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encodeEvent({ type: "error", error }));
      controller.close();
    },
  });

  return new Response(stream, {
    status: error.status ?? 500,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}

export function sseResponseFromStream(
  stream: ReadableStream<Uint8Array>,
): Response {
  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}