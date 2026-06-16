type Props = {
  examName: string;
  onChange: (value: string) => void;
  onBack: () => void;
  onContinue: () => void;
  error: string;
};

export function ExamStep({ examName, onChange, onBack, onContinue, error }: Props) {
  return (
    <section className="rounded-[2rem] border border-zinc-800 bg-zinc-950/85 p-7 sm:p-10">
      <p className="text-xs font-semibold uppercase tracking-[0.4em] text-sky-300">
        Exam signal
      </p>
      <h1 className="mt-4 text-3xl font-black text-zinc-50 sm:text-5xl">
        Which exam are we hunting?
      </h1>
      <label className="mt-8 block text-sm font-semibold text-zinc-200" htmlFor="exam">
        Certification code
      </label>
      <input
        id="exam"
        value={examName}
        onChange={(event) => onChange(event.target.value)}
        list="exam-options"
        className="mt-3 min-h-12 w-full rounded-2xl border border-zinc-700 bg-black px-4 text-lg font-semibold text-zinc-50 outline-none transition focus:border-amber-300"
        placeholder="DVA-C02"
      />
      <datalist id="exam-options">
        <option value="DVA-C02" />
        <option value="AWS Certified Developer - Associate (DVA-C02)" />
      </datalist>
      {error ? <p className="mt-3 text-sm text-amber-200">{error}</p> : null}
      <div className="mt-8 flex flex-wrap gap-3">
        <button onClick={onBack} className="min-h-11 rounded-full border border-zinc-700 px-5 text-sm font-bold text-zinc-200">
          Back
        </button>
        <button onClick={onContinue} className="min-h-11 rounded-full bg-zinc-50 px-5 text-sm font-black text-zinc-950">
          Continue
        </button>
      </div>
    </section>
  );
}
