import type { AgentFeedEvent } from "@/lib/types";

type Props = {
  events: AgentFeedEvent[];
};

const AGENTS = ["Onboarding Agent", "Blueprint Scout", "Curriculum Builder"];

export function AgentFeed({ events }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-800 bg-zinc-950/85 p-7 sm:p-10">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">
        Non-skippable build feed
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-50 sm:text-5xl">
        Agents are assembling your route.
      </h1>
      <div className="mt-8 space-y-3">
        {AGENTS.map((agent) => {
          const event = [...events].reverse().find((item) => item.agent === agent);
          const status = event?.status || "running";
          return (
            <div key={agent} className="rounded-3xl border border-zinc-800 bg-black/60 p-5">
              <div className="flex items-center justify-between gap-3">
                <p className="font-black text-zinc-100">{agent}</p>
                <span className="rounded-full bg-zinc-800 px-3 py-1 text-xs font-bold uppercase text-zinc-200">
                  {status}
                </span>
              </div>
              <p className="mt-2 text-sm leading-6 text-zinc-400">
                {event?.message || "Waiting for signal..."}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
