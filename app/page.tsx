export default function Home() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 px-6 py-16">
        <h1 className="text-4xl font-semibold tracking-tight">Gauntlet</h1>
        <p className="text-base text-muted-foreground">
          Phase 1 scaffold is ready. Next up: Rex + Sage loop implementation.
        </p>
      </div>
    </main>
  );
}
