"use client";

import { useState } from "react";

import { clearThreadId } from "@/app/session/session-persistence";
import { AppNav } from "@/components/navigation/app-nav";
import { ResetProgressDialog } from "@/components/settings/reset-progress-dialog";
import { Button } from "@/components/ui/button";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import { DEFAULT_MODELS, DEFAULT_SETTINGS, loadSettings, saveSettings, type AgentModelKey, type AppSettings } from "@/lib/settings";
import type { LearningStyle } from "@/lib/types";
import { useHydrated } from "@/lib/use-hydrated";

const MODEL_OPTIONS = [
  "anthropic/claude-sonnet-4.6",
  "anthropic/claude-haiku-4.5",
  "openai/gpt-4.1",
  "deepseek/deepseek-v4-flash",
  "deepseek/deepseek-v4-pro",
  "meta-llama/llama-3.3-70b-instruct",
];

const LEARNING_STYLES: Array<{ value: LearningStyle; label: string }> = [
  { value: "pressure_drills", label: "Pressure drills" },
  { value: "guided_explanations", label: "Guided explanations" },
  { value: "mixed_review", label: "Mixed review" },
];

function modelLabel(key: AgentModelKey) { return key === "rex" ? "Rex" : key === "sage" ? "Sage" : "Evaluator"; }

export function SettingsClient() {
  const hydrated = useHydrated();
  const initialSettings = hydrated ? loadSettings() : DEFAULT_SETTINGS;
  return <SettingsForm key={hydrated ? "hydrated" : "server"} initialSettings={initialSettings} />;
}

type FormProps = { initialSettings: AppSettings };

function SettingsForm({ initialSettings }: FormProps) {
  const [settings, setSettings] = useState(initialSettings);
  const [savedSettings, setSavedSettings] = useState(initialSettings);
  const [saveState, setSaveState] = useState("Saved locally");
  const [resetOpen, setResetOpen] = useState(false);
  const [resetReady, setResetReady] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const hasUnsavedChanges = JSON.stringify(settings) !== JSON.stringify(savedSettings);

  function persistSettings(nextSettings: AppSettings) {
    saveSettings(nextSettings);
    setSettings(nextSettings);
    setSavedSettings(nextSettings);
    setSaveState("Saved locally");
    return nextSettings;
  }

  function updateSetting(next: Partial<AppSettings>) {
    setSettings((current) => ({ ...current, ...next }));
    setSaveState("Unsaved changes");
  }

  function updateModel(key: AgentModelKey, value: string) {
    setSettings((current) => ({ ...current, models: { ...current.models, [key]: value } }));
    setSaveState("Unsaved changes");
  }

  function openResetDialog() {
    setResetReady(false);
    setResetOpen(true);
    window.setTimeout(() => setResetReady(true), 3000);
  }

  async function rebuildCurriculum() {
    const nextSettings = hasUnsavedChanges ? persistSettings(settings) : settings;
    setIsRebuilding(true);
    const res = await fetch("/api/settings/learning-style", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: getAnonymousUserId(), learning_style: nextSettings.learningStyle }),
    });
    setIsRebuilding(false);
    setSaveState(res.ok ? "Curriculum rebuild queued" : "Rebuild failed");
  }

  async function resetProgress() {
    setIsResetting(true);
    const res = await fetch("/api/settings/reset-progress", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: getAnonymousUserId() }),
    });
    clearThreadId();
    setIsResetting(false);
    setResetOpen(false);
    setSaveState(res.ok ? "Progress reset" : "Reset failed");
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <AppNav />
        <section className="mt-8 rounded-[2rem] border border-zinc-200 bg-zinc-950 p-7 text-zinc-50 dark:border-zinc-800">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">Settings</p>
              <h1 className="mt-4 max-w-3xl text-4xl font-black tracking-tight sm:text-6xl">Tune the gauntlet without sanding off the edge.</h1>
              <p className="mt-4 text-sm font-semibold text-zinc-400">{saveState}</p>
            </div>
            <Button onClick={() => persistSettings(settings)} disabled={!hasUnsavedChanges} className="bg-amber-300 text-zinc-950 hover:bg-amber-200">
              {hasUnsavedChanges ? "Save changes" : "All changes saved"}
            </Button>
          </div>
        </section>

        <section className="mt-5 grid gap-5 lg:grid-cols-2">
          <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-xl font-black">Session loop</h2>
            <label className="mt-5 block text-sm font-bold" htmlFor="session-cycles">Cycles per session</label>
            <input id="session-cycles" type="number" min="1" max="5" value={settings.sessionCycles} onChange={(event) => updateSetting({ sessionCycles: Number(event.target.value) })} className="mt-2 h-12 w-28 rounded-xl border border-zinc-300 bg-transparent px-3 font-black dark:border-zinc-700" />
            <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">Default is 2. Higher values make Rex stay in the ring longer.</p>
          </div>

          <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-xl font-black">Learning style</h2>
            <select value={settings.learningStyle} onChange={(event) => updateSetting({ learningStyle: event.target.value as LearningStyle })} className="mt-5 h-12 w-full rounded-xl border border-zinc-300 bg-transparent px-3 font-bold dark:border-zinc-700">
              {LEARNING_STYLES.map((style) => <option key={style.value} value={style.value}>{style.label}</option>)}
            </select>
            <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">Changing this rebuilds your curriculum. Progress history is kept.</p>
            <Button onClick={rebuildCurriculum} disabled={isRebuilding} className="mt-5 bg-amber-300 text-zinc-950 hover:bg-amber-200">
              {isRebuilding ? "Queueing..." : "Rebuild curriculum"}
            </Button>
          </div>

          <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950 lg:col-span-2">
            <h2 className="text-xl font-black">Agent models</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-3">
              {(Object.keys(DEFAULT_MODELS) as AgentModelKey[]).map((key) => (
                <label key={key} className="block text-sm font-bold">
                  {modelLabel(key)}
                  <select value={settings.models[key]} onChange={(event) => updateModel(key, event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-zinc-300 bg-transparent px-3 dark:border-zinc-700">
                    {MODEL_OPTIONS.map((model) => <option key={model} value={model}>{model}</option>)}
                  </select>
                </label>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-xl font-black">Bring your own key</h2>
            <label className="mt-5 flex items-center gap-3 text-sm font-bold">
              <input type="checkbox" checked={settings.byokEnabled} onChange={(event) => updateSetting({ byokEnabled: event.target.checked })} />
              Use my OpenRouter key for agent calls
            </label>
            <input type="password" value={settings.openRouterKey} onChange={(event) => updateSetting({ openRouterKey: event.target.value })} placeholder="sk-or-v1-..." className="mt-4 h-12 w-full rounded-xl border border-zinc-300 bg-transparent px-3 dark:border-zinc-700" />
            <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">Stored only in this browser and sent with agent requests. Not stored server-side.</p>
          </div>

          <div className="rounded-[2rem] border border-rose-300 bg-rose-50 p-6 dark:border-rose-900 dark:bg-rose-950/30">
            <h2 className="text-xl font-black text-rose-900 dark:text-rose-100">Reset exam progress</h2>
            <p className="mt-3 text-sm text-rose-800 dark:text-rose-200">This permanently deletes your DVA-C02 progress. This cannot be undone.</p>
            <Button onClick={openResetDialog} variant="destructive" className="mt-5">Reset progress</Button>
          </div>
        </section>
      </div>
      <ResetProgressDialog isOpen={resetOpen} isReady={resetReady} isResetting={isResetting} onClose={() => { setResetOpen(false); setResetReady(false); }} onConfirm={resetProgress} />
    </main>
  );
}
