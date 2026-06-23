// Phase 9.5 — derive the compact `Review next` block from a Challenge.
//
// The block surfaces only links that came from the selected concept packet
// (official_docs / skill_builder_links / lab_links). The SageCard must
// render the block only when at least one item exists; this helper returns
// `null` for an empty packet so the UI can simply hide the section.

import type { Challenge, ReviewNext, ReviewNextItem } from "@/lib/types";

const TITLE_BY_HOST: Record<string, string> = {
  "docs.aws.amazon.com": "AWS official docs",
  "skillbuilder.aws": "Skill Builder",
  "clouderlabs.com": "ClouderLabs",
};

const FALLBACK_TITLES = {
  official_docs: "AWS official docs",
  skill_builder: "Skill Builder",
  lab_links: "Hands-on lab",
} as const;

function titleForUrl(url: string, fallback: string): string {
  try {
    const host = new URL(url).host.toLowerCase();
    return TITLE_BY_HOST[host] ?? fallback;
  } catch {
    return fallback;
  }
}

function urlsToItems(
  urls: string[] | undefined,
  source: ReviewNextItem["source"],
  fallbackTitle: string,
): ReviewNextItem[] {
  if (!urls || urls.length === 0) return [];
  return urls.map((url) => ({
    url,
    title: titleForUrl(url, fallbackTitle),
    source,
  }));
}

export function deriveReviewNext(challenge: Challenge | null | undefined): ReviewNext | null {
  if (!challenge) return null;
  const items: ReviewNextItem[] = [
    ...urlsToItems(challenge.official_docs, "official_docs", FALLBACK_TITLES.official_docs),
    ...urlsToItems(challenge.skill_builder_links, "skill_builder", FALLBACK_TITLES.skill_builder),
    ...urlsToItems(challenge.lab_links, "lab", FALLBACK_TITLES.lab_links),
  ];
  if (items.length === 0) return null;
  return { items };
}
