import type { LearningStyle } from "@/lib/types";

const STYLES: Array<{ value: LearningStyle; title: string; body: string }> = [
  {
    value: "pressure_drills",
    title: "Pressure drills",
    body: "Lead with hard scenarios and let Sage patch the gaps after the hit.",
  },
  {
    value: "guided_explanations",
    title: "Guided explanations",
    body: "Start with concepts that unlock the rest of the blueprint faster.",
  },
  {
    value: "mixed_review",
    title: "Mixed review",
    body: "Balance exam weighting with variety so the route stays sharp.",
  },
];

type Props = {
  value: LearningStyle;
  onChange: (value: LearningStyle) => void;
  onBack: () => void;
  onStart: () => void;
  isLoading: boolean;
};

export function StyleStep({ value, onChange, onBack, onStart, isLoading }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-800 bg-zinc-950/85 p-7 sm:p-10">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-emerald-300">
        Learning style
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-50 sm:text-5xl">
        Pick your training bias.
      </h1>
      <div className="mt-7 grid gap-3">
        {STYLES.map((style) => (
          <button
            key={style.value}
            onClick={() => onChange(style.value)}
            className={`min-h-24 rounded-3xl border p-5 text-left transition ${
              value === style.value
                ? "border-amber-300 bg-amber-300 text-zinc-950"
                : "border-zinc-800 bg-black/60 text-zinc-200 hover:border-zinc-500"
            }`}
          >
            <span className="block text-lg font-black">{style.title}</span>
            <span className="mt-1 block text-sm opacity-80">{style.body}</span>
          </button>
        ))}
      </div>
      <div className="mt-8 flex flex-wrap gap-3">
        <button onClick={onBack} className="min-h-11 rounded-full border border-zinc-700 px-5 text-sm font-bold text-zinc-200">
          Back
        </button>
        <button
          onClick={onStart}
          disabled={isLoading}
          className="min-h-11 rounded-full bg-amber-300 px-5 text-sm font-black text-zinc-950 disabled:opacity-60"
        >
          {isLoading ? "Dispatching..." : "Build my plan"}
        </button>
      </div>
    </section>
  );
}
