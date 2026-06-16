import Link from "next/link";

export function AppNav() {
  return (
    <nav className="flex flex-wrap items-center justify-between gap-3 text-sm">
      <Link href="/dashboard" className="font-black uppercase tracking-[0.25em] text-zinc-100">
        Gauntlet
      </Link>
      <div className="flex gap-2">
        <Link href="/progress" className="rounded-full border border-zinc-800 px-4 py-2 text-zinc-300">
          Progress
        </Link>
        <Link href="/session" className="rounded-full bg-amber-300 px-4 py-2 font-black text-zinc-950">
          Start session
        </Link>
      </div>
    </nav>
  );
}
