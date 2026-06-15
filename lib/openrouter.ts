const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export type OpenRouterErrorCode =
  | "MISSING_API_KEY"
  | "REQUEST_FAILED"
  | "API_ERROR"
  | "INVALID_RESPONSE"
  | "STREAM_ERROR";

export type OpenRouterError = {
  code: OpenRouterErrorCode;
  message: string;
  status?: number;
  details?: string;
};

// All SSE events share this discriminated union so consumers can rely on one shape.
export type SseEvent =
  | { type: "token"; token: string }
  | { type: "done" }
  | { type: "error"; error: OpenRouterError };

export type OpenRouterStreamRequest = {
  model: string;
  systemPrompt: string;
  userMessage: string;
  temperature?: number;
  maxTokens?: number;
  signal?: AbortSignal;
};

export type OpenRouterStreamResult =
  | { ok: true; stream: ReadableStream<Uint8Array> }
  | { ok: false; error: OpenRouterError };

export async function streamOpenRouterResponse(
  request: OpenRouterStreamRequest,
): Promise<OpenRouterStreamResult> {
  const apiKey = process.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    return {
      ok: false,
      error: {
        code: "MISSING_API_KEY",
        message: "OPENROUTER_API_KEY is not set.",
      },
    };
  }

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: request.model,
        stream: true,
        temperature: request.temperature,
        max_tokens: request.maxTokens,
        messages: [
          { role: "system", content: request.systemPrompt },
          { role: "user", content: request.userMessage },
        ],
      }),
      signal: request.signal,
    });
  } catch (error) {
    return {
      ok: false,
      error: {
        code: "REQUEST_FAILED",
        message: "Failed to reach OpenRouter.",
        details: error instanceof Error ? error.message : "Unknown fetch error",
      },
    };
  }

  if (!upstreamResponse.ok) {
    const apiError = await parseApiError(upstreamResponse);
    return { ok: false, error: apiError };
  }

  if (!upstreamResponse.body) {
    return {
      ok: false,
      error: {
        code: "INVALID_RESPONSE",
        message: "OpenRouter returned no response body.",
        status: upstreamResponse.status,
      },
    };
  }

  return {
    ok: true,
    stream: toSseStream(upstreamResponse.body),
  };
}

async function parseApiError(response: Response): Promise<OpenRouterError> {
  let details = "";
  let message = `OpenRouter request failed with status ${response.status}.`;

  try {
    const payload = (await response.json()) as {
      error?: { message?: string };
      message?: string;
    };
    const parsedMessage = payload.error?.message ?? payload.message;
    if (parsedMessage) {
      message = parsedMessage;
    }
    details = JSON.stringify(payload);
  } catch {
    try {
      details = await response.text();
    } catch {
      details = "Unable to parse error response body.";
    }
  }

  return {
    code: "API_ERROR",
    message,
    status: response.status,
    details,
  };
}

function encodeEvent(event: SseEvent): Uint8Array {
  return new TextEncoder().encode(`data: ${JSON.stringify(event)}\n\n`);
}

function toSseStream(
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
