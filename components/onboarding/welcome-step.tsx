type Props = {
  onContinue: () => void;
};

export function WelcomeStep({ onContinue }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-200 bg-white/85 p-7 shadow-2xl shadow-black/5 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950/80 dark:shadow-black/30">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-600 dark:text-amber-300">
        Calibration bay
      </p>
      <h1 className="mt-5 max-w-2xl text-4xl font-black tracking-tight text-zinc-950 sm:text-6xl dark:text-zinc-50">
        Build the exam route before Rex starts swinging.
      </h1>
      <p className="mt-5 max-w-xl text-base leading-7 text-zinc-600 dark:text-zinc-300">
        Gauntlet reads the DVA-C02 blueprint, builds your first curriculum, then drops
        you onto a dashboard with today&apos;s target ready.
      </p>
      <button
        onClick={onContinue}
        className="mt-8 min-h-11 rounded-full bg-amber-300 px-6 text-sm font-black text-zinc-950 transition hover:bg-amber-200"
      >
        Start calibration
      </button>
    </section>
  );
}
