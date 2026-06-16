import type { ExamOption } from "@/lib/types";

type Props = {
  examName: string;
  examOptions: ExamOption[];
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
  error: string;
};

export function ExamStep({ examName, examOptions, onChange, onBack, onContinue, error }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-200 bg-white/90 p-7 sm:p-10 dark:border-zinc-800 dark:bg-zinc-950/85">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-sky-600 dark:text-sky-300">
        Exam signal
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-950 sm:text-5xl dark:text-zinc-50">
        Which exam are we hunting?
      </h1>
      <label className="mt-8 block text-sm font-semibold text-zinc-700 dark:text-zinc-200" htmlFor="exam">
        Certification code
      </label>
      <input
        id="exam"
        value={examName}
        onChange={(event) => onChange(event.target.value)}
        list="exam-options"
        className="mt-3 min-h-12 w-full rounded-2xl border border-zinc-300 bg-white px-4 text-lg font-semibold text-zinc-950 outline-none transition focus:border-amber-300 dark:border-zinc-700 dark:bg-black dark:text-zinc-50"
        placeholder="Certification code or name"
      />
      <datalist id="exam-options">
        {examOptions.flatMap((exam) => [
          <option key={`${exam.exam_code}-code`} value={exam.exam_code.toUpperCase()} />,
          <option key={`${exam.exam_code}-name`} value={exam.canonical_name} />,
        ])}
      </datalist>
      {error ? <p className="mt-3 text-sm text-amber-600 dark:text-amber-200">{error}</p> : null}
      <div className="mt-8 flex flex-wrap gap-3">
        <button onClick={onBack} className="min-h-11 rounded-full border border-zinc-300 px-5 text-sm font-bold text-zinc-700 dark:border-zinc-700 dark:text-zinc-200">
          Back
        </button>
        <button onClick={onContinue} className="min-h-11 rounded-full bg-zinc-950 px-5 text-sm font-black text-zinc-50 dark:bg-zinc-50 dark:text-zinc-950">
          Continue
        </button>
      </div>
    </section>
  );
}
