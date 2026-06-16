// Shared domain types for the app and API proxy boundaries.

export type Challenge = {
  domain: string;
  topic: string;
  topic_id?: string;
  task_statement_id?: string;
  task_statement?: string;
  difficulty?: "easy" | "medium" | "hard";
  services?: string[];
  source_ids?: string[];
  scenario: string;
  question: string;
};

export type EvaluationResult = {
  outcome: "correct" | "incorrect";
  reasoning: string;
};

export type Citation = {
  url: string;
  title: string;
  snippet_id: string;
};

export type SessionResult = {
  cycle: number;
  topic: string;
  outcome: "correct" | "incorrect";
};

export type LearningStyle =
  | "pressure_drills"
  | "guided_explanations"
  | "mixed_review";

export type TopicPlan = {
  id: string;
  name: string;
  task_statement_id?: string;
  services?: string[];
  source_ids?: string[];
  status?: "covered" | "in_progress" | "untouched";
  correct_count?: number;
  total_count?: number;
};

export type DomainPlan = {
  name: string;
  weight: number;
  topics: Array<string | TopicPlan>;
  task_statements?: Array<{ id: string; text: string }>;
  study_order: number;
  performance_score: number;
  correct_count?: number;
  total_count?: number;
  topic_count?: number;
  covered_topic_count?: number;
  completion_percent?: number;
};

export type AgentFeedEvent = {
  id?: number;
  agent: string;
  status: "running" | "complete" | "failed";
  message: string;
  created_at?: string;
};

export type OnboardingRun = {
  id: string;
  exam_id: string;
  exam_name: string;
  learning_style: LearningStyle;
  status: string;
  step: string;
  curriculum_id: string | null;
};

export type DashboardSummary = {
  readiness_score: number;
  today_domain: string;
  today_topic: string;
  rex_record: { user_wins: number; rex_wins: number };
  domains: DomainPlan[];
};
