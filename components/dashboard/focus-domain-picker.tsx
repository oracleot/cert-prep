"use client";

import type { DomainPlan } from "@/lib/types";

type Props = {
  domains: DomainPlan[];
  value: string;
  disabled: boolean;
  onChange: (domain: string) => void;
};

function pillClasses(isSelected: boolean, disabled: boolean) {
  const base = "min-h-9 rounded-full border px-3 text-xs font-black transition";
  if (disabled) return `${base} cursor-not-allowed border-zinc-900/10 text-zinc-950/40`;
  if (isSelected) return `${base} border-zinc-950 bg-zinc-950 text-zinc-50`;
  return `${base} border-zinc-950/20 text-zinc-950 hover:border-zinc-950`;
}

export function FocusDomainPicker({ domains, value, disabled, onChange }: Props) {
  const options = [{ name: "", label: "Recommended" }, ...domains.map((domain) => ({ name: domain.name, label: domain.name }))];
  return (
    <div className="mt-6">
      <p className="text-xs font-black uppercase tracking-[0.25em] opacity-70">Focus domain</p>
      <div className="mt-3 flex flex-wrap gap-2" role="radiogroup" aria-label="Focus domain">
        {options.map((option) => {
          const selected = value === option.name;
          return (
            <button
              key={option.label}
              type="button"
              role="radio"
              aria-checked={selected}
              disabled={disabled}
              onClick={() => onChange(option.name)}
              className={pillClasses(selected, disabled)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {disabled ? (
        <p className="mt-3 text-xs font-semibold opacity-70">
          Finish or resume your current session to choose a new focus.
        </p>
      ) : null}
    </div>
  );
}
