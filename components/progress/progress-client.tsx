"use client";

import { useEffect, useState } from "react";
import { Lock } from "lucide-react";

import { AppNav } from "@/components/navigation/app-nav";
import { getAnonymousUserId } from "@/lib/anonymous-user";
import type { DomainPlan } from "@/lib/types";

export function ProgressClient() {
  const [domains, setDomains] = useState<DomainPlan[]>([]);

  useEffect(() => {
    async function load() {
      const userId = getAnonymousUserId();
      const res = await fetch("/api/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });
      if (res.ok) {
        const data = await res.json();
        setDomains(data.domains || []);
      }
    }

    void load();
  }, []);

  return (
    <main className="min-h-screen bg-black px-4 py-6 text-zinc-50 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <AppNav />
        <section className="mt-10 rounded-[2rem] border border-zinc-800 bg-zinc-950 p-7 sm:p-10">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">
            Progress map
          </p>
          <h1 className="mt-4 text-4xl font-black tracking-tight sm:text-6xl">
            Four domains. No hiding.
          </h1>
          <div className="mt-8 grid gap-4">
            {domains.map((domain) => {
              const completion = domain.completion_percent || 0;
              return (
                <div key={domain.name} className="rounded-3xl border border-zinc-800 bg-black/60 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-xl font-black">{domain.name}</h2>
                      <p className="mt-1 text-sm text-zinc-400">Weight {domain.weight}%</p>
                    </div>
                    <span className="rounded-full bg-zinc-900 px-3 py-1 text-sm font-black text-zinc-300">
                      {completion === 0 ? (
                        <span className="inline-flex items-center gap-1">
                          <Lock aria-hidden="true" className="size-3" /> locked
                        </span>
                      ) : `${completion}%`}
                    </span>
                  </div>
                  <div className="mt-5 h-3 overflow-hidden rounded-full bg-zinc-800">
                    <div className="h-full bg-amber-300" style={{ width: `${completion}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
}
