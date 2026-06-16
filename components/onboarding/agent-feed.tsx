import type { AgentFeedEvent } from "@/lib/types";

type Props = {
  events: AgentFeedEvent[];
};

const AGENTS = ["Onboarding Agent", "Blueprint Scout", "Curriculum Builder"];

export function AgentFeed({ events }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-200 bg-white/90 p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950/85">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        Non-skippable build feed
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-950 sm:text-5xl dark:text-zinc-50">
        Agents are assembling your route.
      </h1>
      <div className="mt-8 space-y-3">
        {AGENTS.map((agent) => {
          const event = [...events].reverse().find((item) => item.agent === agent);
          const status = event?.status || "running";
          return (
            <div key={agent} className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-black/60">
              <div className="flex items-center justify-between gap-3">
                <p className="font-black text-zinc-950 dark:text-zinc-100">{agent}</p>
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
