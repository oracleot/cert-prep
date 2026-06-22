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
  familiarity_level?: "new" | "building" | "review";
  scenario: string;
  question: string;
};

export type EvaluationResult = {
  outcome: "correct" | "incorrect";
  reasoning: string;
  answer_intent?: AnswerIntent;
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
  answer_intent?: AnswerIntent;
  review_status?: ExchangeReviewStatus;
  feedback?: SageFeedback | null;
};

export type AnswerIntent = "attempt" | "knowledge_gap";
export type ExchangeReviewStatus = "active" | "excluded_pending_review" | "confirmed_hallucination" | "dismissed";
export type SageFeedbackType = "factual_error" | "bad_source" | "confusing_explanation";
export type SageFeedbackStatus = "pending_review" | "confirmed_hallucination" | "dismissed";
export type SageFeedback = {
  feedback_type: SageFeedbackType;
  status: SageFeedbackStatus;
  excludes_metrics: boolean;
  review_status: ExchangeReviewStatus;
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
  readiness_contribution?: number;
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

export type ExamOption = {
  exam_code: string;
  canonical_name: string;
  provider: string;
};

export type RexRecord = { user_wins: number; rex_wins: number };

export type SessionStreak = {
  current_streak: number;
  last_completed_on: string | null;
};

export type DashboardSummary = {
  exam_id: string;
  readiness_score: number;
  today_domain: string;
  today_topic: string;
  rex_record: RexRecord;
  streak: SessionStreak;
  domains: DomainPlan[];
};

export type SessionHistoryItem = {
  id: string;
  started_at: string;
  ended_at: string | null;
  exam_id: string;
  domain: string;
  topic: string;
  total_cycles: number;
  correct_count: number;
};

export type SessionHistoryExchange = {
  cycle: number;
  domain: string;
  topic: string;
  challenge: Challenge;
  user_answer: string;
  outcome: "correct" | "incorrect";
  answer_intent?: AnswerIntent;
  review_status?: ExchangeReviewStatus;
  feedback?: SageFeedback | null;
  sage_response: string;
  citations: Citation[];
};

export type SessionHistoryDetail = {
  id: string;
  started_at: string;
  ended_at: string | null;
  exam_id: string;
  domain: string;
  topic: string;
  exchanges: SessionHistoryExchange[];
};
