type Props = {
  onContinue: () => void;
};

export function WelcomeStep({ onContinue }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-800 bg-zinc-950/80 p-7 shadow-2xl shadow-black/30 sm:p-10">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-amber-300">
        Calibration bay
      </p>
      <h1 className="mt-5 max-w-2xl text-4xl font-black tracking-tight text-zinc-50 sm:text-6xl">
        Build the exam route before Rex starts swinging.
      </h1>
      <p className="mt-5 max-w-xl text-base leading-7 text-zinc-300">
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
