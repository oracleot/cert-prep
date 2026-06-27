// OpenRouter streaming client. Owns the HTTP request to OpenRouter and delegates
// SSE framing/encoding to lib/openrouter-sse.ts. Types live in lib/openrouter-types.ts.
// Re-exports preserve the historical public surface so existing callers continue
// to import from "@/lib/openrouter" without changes.

import { toSseStream } from "./openrouter-sse";
import type {
  OpenRouterError,
  OpenRouterStreamRequest,
  OpenRouterStreamResult,
} from "./openrouter-types";

export type {
  OpenRouterError,
  OpenRouterErrorCode,
  OpenRouterStreamRequest,
  OpenRouterStreamResult,
  SseEvent,
} from "./openrouter-types";

export {
  openRouterErrorToSseResponse,
  sseResponseFromStream,
} from "./openrouter-sse";

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

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