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
});
