// Shared types and discriminated unions for the OpenRouter SSE client.
// Kept type-only so this module is safe to import from both server and client code.

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