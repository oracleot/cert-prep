import type { AgentFeedEvent } from "@/lib/types";

type FeedAgent = { label: string; aliases: string[] };

type FeedHandlers = {
  onEvent: (event: AgentFeedEvent) => void;
  onComplete: () => void;
  onFailure: (message: string) => void;
  onError: () => void;
};

export type FeedIssue = { message: string; action: "build" | "plan" };

export const FEED_AGENTS: FeedAgent[] = [
  { label: "Onboarding Agent", aliases: ["Onboarding Agent", "Onboarding"] },
  { label: "Blueprint Scout", aliases: ["Blueprint Scout", "Blueprint"] },
  { label: "Curriculum Builder", aliases: ["Curriculum Builder", "Curriculum"] },
];

export function latestAgentEvent(events: AgentFeedEvent[], label: string) {
  const agent = FEED_AGENTS.find((item) => item.label === label);
  if (!agent) return undefined;
  return [...events].reverse().find((event) => agent.aliases.includes(event.agent));
}

export function isCurriculumComplete(event: AgentFeedEvent) {
  const latest = latestAgentEvent([event], "Curriculum Builder");
  return Boolean(latest && event.status === "complete");
}

export function openOnboardingFeed(onboardingId: string, handlers: FeedHandlers) {
  const source = new EventSource(`/api/onboarding/feed?onboarding_id=${onboardingId}`);
  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as AgentFeedEvent;
    handlers.onEvent(event);
    if (event.status === "failed") {
      source.close();
      handlers.onFailure(event.message);
    }
    if (isCurriculumComplete(event)) {
      source.close();
      handlers.onComplete();
    }
  };
  source.onerror = () => {
    source.close();
    handlers.onError();
  };
  return source;
}
