import { describe, expect, it } from "vitest";
import { nextSelectedLabels } from "@/app/session/use-option-selection";

describe("nextSelectedLabels", () => {
  it("toggles single_response off when the same option is clicked twice", () => {
    expect(nextSelectedLabels([], "A", "single_response")).toEqual(["A"]);
    expect(nextSelectedLabels(["A"], "A", "single_response")).toEqual([]);
  });

  it("keeps multiple_response behavior unchanged", () => {
    expect(nextSelectedLabels([], "B", "multiple_response")).toEqual(["B"]);
    expect(nextSelectedLabels(["B"], "B", "multiple_response")).toEqual([]);
    expect(nextSelectedLabels(["B"], "A", "multiple_response")).toEqual(["A", "B"]);
    expect(nextSelectedLabels(["A", "B"], "C", "multiple_response")).toEqual(["A", "B"]);
  });

  it("is a no-op when mode is undefined (free-text / pre-mode challenges)", () => {
    // The hook forwards `challenge?.response_mode` directly; an undefined
    // mode must not toggle anything so a free-text challenge never picks up
    // stray option selections.
    expect(nextSelectedLabels([], "A", undefined)).toEqual([]);
    expect(nextSelectedLabels(["A"], "A", undefined)).toEqual(["A"]);
  });
});
