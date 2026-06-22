import type { LearningStyle } from "@/lib/types";

export type AgentModelKey = "rex" | "sage" | "evaluator";

export type ModelSettings = Record<AgentModelKey, string>;

export type AppSettings = {
  learningStyle: LearningStyle;
  sessionCycles: number;
  models: ModelSettings;
  byokEnabled: boolean;
  openRouterKey: string;
};

export const DEFAULT_MODELS: ModelSettings = {
  rex: "anthropic/claude-sonnet-4.6",
  sage: "anthropic/claude-sonnet-4.6",
  evaluator: "anthropic/claude-haiku-4.5",
};

export const DEFAULT_SETTINGS: AppSettings = {
  learningStyle: "mixed_review",
  sessionCycles: 2,
  models: DEFAULT_MODELS,
  byokEnabled: false,
  openRouterKey: "",
};

const SETTINGS_KEY = "gauntlet.settings.v1";
const MIN_CYCLES = 1;
const MAX_CYCLES = 5;

function clampCycles(value: unknown) {
  const parsed = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(parsed)) return DEFAULT_SETTINGS.sessionCycles;
  return Math.min(MAX_CYCLES, Math.max(MIN_CYCLES, Math.round(parsed)));
}

function coerceSettings(value: Partial<AppSettings>): AppSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...value,
    sessionCycles: clampCycles(value.sessionCycles),
    models: { ...DEFAULT_MODELS, ...(value.models || {}) },
    openRouterKey: value.openRouterKey || "",
  };
}

export function loadSettings(): AppSettings {
  if (typeof window === "undefined") return DEFAULT_SETTINGS;
  const raw = window.localStorage.getItem(SETTINGS_KEY);
  if (!raw) return DEFAULT_SETTINGS;
  try {
    return coerceSettings(JSON.parse(raw));
  } catch {
    return DEFAULT_SETTINGS;
  }
}

export function saveSettings(settings: AppSettings) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SETTINGS_KEY, JSON.stringify(coerceSettings(settings)));
}

export function sessionSettingsPayload(settings: AppSettings) {
  return {
    learning_style: settings.learningStyle,
    max_cycles: settings.sessionCycles,
    model_overrides: settings.models,
    openrouter_api_key: settings.byokEnabled ? settings.openRouterKey.trim() : "",
  };
}
