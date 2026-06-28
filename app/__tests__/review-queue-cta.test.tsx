/**
 * Review Queue CTA — V1 contract tests (Phase 10).
 *
 * Verifies the dashboard's review-queue CTA surfaces the count to the
 * learner and silently hides itself when the queue endpoint errors out so
 * the dashboard is never blocked by the queue.
 *
 * Run: npm test -- --grep "review-queue-cta"
 *
 * Uses `react-dom/server` for static markup because the project's vitest
 * config runs in `node` environment with no jsdom. Rendering to a string
 * avoids the cost of an extra DOM dependency for two assertions.
 */
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { ReviewQueueCta } from "@/components/dashboard/review-queue-cta";

describe("ReviewQueueCta — dashboard tile", () => {
  it("renders 'Review Queue (3 due)' when count is 3", () => {
    const html = renderToStaticMarkup(<ReviewQueueCta count={3} />);
    expect(html).toContain("Review Queue (3 due)");
    expect(html).toContain('href="/review"');
  });

  it("renders nothing when error is true", () => {
    const html = renderToStaticMarkup(<ReviewQueueCta count={5} error />);
    expect(html).toBe("");
  });

  it("renders nothing when count is 0", () => {
    const html = renderToStaticMarkup(<ReviewQueueCta count={0} />);
    expect(html).toBe("");
  });
});
