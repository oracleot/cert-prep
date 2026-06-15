// Non-streaming OpenRouter client for structured JSON responses

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";

export type JsonCallRequest = {
  model: string;
  systemPrompt: string;
  userMessage: string;
  temperature?: number;
  maxTokens?: number;
};

export type JsonCallResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: string };

export async function callOpenRouterJson<T>(
  request: JsonCallRequest,
): Promise<JsonCallResult<T>> {
  const apiKey = process.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    return { ok: false, error: "OPENROUTER_API_KEY is not set." };
  }

  let response: Response;
  try {
    response = await fetch(OPENROUTER_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: request.model,
        stream: false,
        temperature: request.temperature ?? 0.7,
        max_tokens: request.maxTokens ?? 1024,
        messages: [
          { role: "system", content: request.systemPrompt },
          { role: "user", content: request.userMessage },
        ],
      }),
    });
  } catch (err) {
    return {
      ok: false,
      error: err instanceof Error ? err.message : "Network error",
    };
  }

  if (!response.ok) {
    let details = "";
    try {
      details = await response.text();
    } catch {
      details = "Unable to read error body.";
    }
    return {
      ok: false,
      error: `OpenRouter error ${response.status}: ${details}`,
    };
  }

  let content = "";
  try {
    const json = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    content = json.choices?.[0]?.message?.content ?? "";
    // Strip possible markdown code fences
    const cleaned = content.replace(/^```(?:json)?\n?|```$/gm, "").trim();
    return { ok: true, data: JSON.parse(cleaned) as T };
  } catch (err) {
    return {
      ok: false,
      error:
        err instanceof Error
          ? `JSON parse failed: ${err.message}. Raw: ${content.slice(0, 200)}`
          : "Failed to parse response",
    };
  }
}
