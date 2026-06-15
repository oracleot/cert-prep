import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-16">
        <h1 className="text-4xl font-semibold tracking-tight">Gauntlet</h1>
        <p className="text-base text-muted-foreground">
          DVA-C02 certification prep. Rex challenges. Sage teaches.
        </p>
        <Link
          href="/session"
          className="inline-flex w-fit items-center rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          Start session →
        </Link>
      </div>
    </main>
  );
}
