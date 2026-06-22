// Re-export from canonical location to eliminate duplicate implementation
export {
  MODEL,
  buildRexChallengePrompt,
  buildRexRechallengePrompt,
} from "@/agents/prompts/rex";
export type { RexChallengeInput, RexRechallengeInput } from "@/agents/prompts/rex";
