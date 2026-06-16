import { readSseStream } from "@/lib/sse-reader";
import type { SseEvent } from "@/lib/openrouter";
import type { Citation, EvaluationResult } from "@/lib/types";

type SessionSseEvent = SseEvent | { type: "evaluation"; data: string } | { type: "citations"; data: Citation[] };

type StreamHandlers = {
  onEvaluation: (evaluation: EvaluationResult) => void;
  onCitations: (citations: Citation[]) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (message: string) => void;
};

export async function readSessionStream(
  body: ReadableStream<Uint8Array>,
  handlers: StreamHandlers,
) {
  await readSseStream(body, (event) => {
    const sessionEvent = event as SessionSseEvent;

    if (sessionEvent.type === "evaluation") {
      handlers.onEvaluation(JSON.parse(sessionEvent.data) as EvaluationResult);
      return;
    }

    if (sessionEvent.type === "citations") {
      handlers.onCitations(sessionEvent.data);
      return;
    }

    if (sessionEvent.type === "token") {
      handlers.onToken(sessionEvent.token);
      return;
    }

    if (sessionEvent.type === "done") {
      handlers.onDone();
      return;
    }

    handlers.onError(sessionEvent.error?.message || "Unknown error");
  });
}
