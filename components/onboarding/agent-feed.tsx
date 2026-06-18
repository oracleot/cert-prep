import type { AgentFeedEvent } from "@/lib/types";
import { FEED_AGENTS, latestAgentEvent } from "@/lib/onboarding-feed";

type Props = {
  events: AgentFeedEvent[];
  issue: { message: string; action: "build" | "plan" } | null;
  onRetryBuild: () => void;
  onRetryPlan: () => void;
  onBack: () => void;
};

export function AgentFeed({ events, issue, onRetryBuild, onRetryPlan, onBack }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-200 bg-white/90 p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950/85">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        Non-skippable build feed
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-950 sm:text-5xl dark:text-zinc-50">
        Agents are assembling your route.
      </h1>
      {issue ? (
        <div className="mt-6 rounded-3xl border border-red-200 bg-red-50 p-5 text-sm text-red-900 dark:border-red-900/70 dark:bg-red-950/30 dark:text-red-100">
          <p className="font-black">Build needs attention</p>
          <p className="mt-2 leading-6">{issue.message}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={issue.action === "plan" ? onRetryPlan : onRetryBuild}
              className="min-h-11 rounded-full bg-red-600 px-5 text-sm font-black text-white hover:bg-red-500"
            >
              Try again
            </button>
            <button
              type="button"
              onClick={onBack}
              className="min-h-11 rounded-full border border-red-200 px-5 text-sm font-black text-red-900 hover:bg-white dark:border-red-800 dark:text-red-100 dark:hover:bg-red-950/50"
            >
              Change choices
            </button>
          </div>
        </div>
      ) : null}
      <div className="mt-8 space-y-3">
        {FEED_AGENTS.map(({ label }) => {
          const event = latestAgentEvent(events, label);
          const status = event?.status || (event?.message ? "running" : "waiting");
          return (
            <div key={label} className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-black/60">
              <div className="flex items-center justify-between gap-3">
                <p className="font-black text-zinc-950 dark:text-zinc-100">{label}</p>
                <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-bold uppercase text-zinc-700 dark:bg-zinc-800 dark:text-zinc-200">
                  {status}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-zinc-500 dark:text-zinc-400">
                {event?.message || "Waiting for signal..."}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
