import Link from "next/link";

import type { DomainPlan, TopicPlan } from "@/lib/types";

type Props = {
  domains: DomainPlan[];
};

function topicName(topic: string | TopicPlan | undefined) {
  return typeof topic === "string" ? topic : topic?.name;
}

export function PlanReveal({ domains }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-200 bg-white/90 p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950/85">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        Plan reveal
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-950 sm:text-5xl dark:text-zinc-50">
        DVA-C02 route loaded.
      </h1>
      <div className="mt-8 grid gap-3 sm:grid-cols-2">
        {domains.map((domain) => (
          <div key={domain.name} className="rounded-3xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-black/60">
            <div className="flex items-start justify-between gap-4">
              <h2 className="text-xl font-black text-zinc-950 dark:text-zinc-50">{domain.name}</h2>
              <span className="rounded-full bg-amber-300 px-3 py-1 text-xs font-black text-zinc-950">
                {domain.weight}%
              </span>
            </div>
            <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
              Order {domain.study_order}. {domain.topics.length} official topics. First: {topicName(domain.topics?.[0]) || "calibration"}
            </p>
          </div>
        ))}
      </div>
      <Link
        href="/dashboard"
        className="mt-8 inline-flex min-h-11 items-center rounded-full bg-amber-300 px-6 text-sm font-black text-zinc-950 hover:bg-amber-200"
      >
        Let&apos;s go
      </Link>
    </section>
  );
}
