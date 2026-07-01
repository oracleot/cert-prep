// Phase 11 — option types unit tests (frontend mirror of agents/option_types.py).
import { describe, expect, it } from "vitest";
import { OPTION_LABELS, isOptionLabel, isResponseMode, normalizeOptionLabels } from "@/lib/option-types";

describe("option-types", () => {
  it("isOptionLabel accepts only A/B/C/D", () => {
    for (const label of ["A", "B", "C", "D"]) {
      expect(isOptionLabel(label)).toBe(true);
    }
    for (const label of ["", "E", "a", "1", null, undefined, 0, []]) {
      expect(isOptionLabel(label as unknown)).toBe(false);
    }
  });

  it("isResponseMode accepts only the two canonical values", () => {
    expect(isResponseMode("single_response")).toBe(true);
    expect(isResponseMode("multiple_response")).toBe(true);
    expect(isResponseMode("single")).toBe(false);
    expect(isResponseMode("multi")).toBe(false);
    expect(isResponseMode("")).toBe(false);
    expect(isResponseMode(null as unknown)).toBe(false);
  });

  it("normalizeOptionLabels dedupes and sorts A<B<C<D", () => {
    expect(normalizeOptionLabels(["D", "B", "A", "B", "X"] as string[])).toEqual(["A", "B", "D"]);
    expect(normalizeOptionLabels([])).toEqual([]);
  });

  it("normalizeOptionLabels drops invalid tokens", () => {
    expect(normalizeOptionLabels(["A", "Z", 1, null, "B"] as unknown[])).toEqual(["A", "B"]);
  });

  it("OPTION_LABELS is the canonical A/B/C/D tuple", () => {
    expect(OPTION_LABELS).toEqual(["A", "B", "C", "D"]);
  });
});