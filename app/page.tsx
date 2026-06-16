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
    return <main className="min-h-screen bg-background" />;
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.18),transparent_30%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.12),transparent_32%)] dark:bg-[radial-gradient(circle_at_20%_10%,rgba(251,191,36,0.22),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.16),transparent_30%)]" />
      <div className="relative mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
        <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
          Gauntlet
        </p>
        <h1 className="text-5xl font-black tracking-tight">Certification prep with teeth.</h1>
        <p className="text-base leading-7 text-muted-foreground">
          Build a certification curriculum, watch the agents assemble it, then let Rex find
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
