"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getAnonymousUserId } from "@/lib/anonymous-user";

export default function Home() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let active = true;
    async function checkCurriculum() {
      try {
        const userId = getAnonymousUserId();
        const res = await fetch("/api/onboarding/state", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: userId }),
        });
        if (!active) return;
        if (res.ok) {
          const data = await res.json();
          if (data?.curriculum) {
            router.replace("/dashboard");
            return;
          }
        }
      } finally {
        if (active) setChecking(false);
      }
    }
    void checkCurriculum();
    return () => {
      active = false;
    };
  }, [router]);

  if (checking) {
    return <main className="min-h-screen bg-black" />;
  }

  return (
    <main className="min-h-screen bg-black text-zinc-50">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">
          Gauntlet
        </p>
        <h1 className="text-5xl font-black tracking-tight">Certification prep with teeth.</h1>
        <p className="text-base leading-7 text-zinc-400">
          Build a DVA-C02 curriculum, watch the agents assemble it, then let Rex find
          every gap Sage needs to close.
        </p>
        <Link
          href="/onboarding"
          className="inline-flex min-h-11 w-fit items-center rounded-full bg-amber-300 px-5 text-sm font-black text-zinc-950 hover:bg-amber-200"
        >
          Start onboarding →
        </Link>
      </div>
    </main>
  );
}
