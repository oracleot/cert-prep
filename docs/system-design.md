# System Design
<!-- IN PROGRESS — gaps: failure handling per dependency, formal provider abstraction map -->
Status: draft | Date: 2026-06-15

## Architecture Decision
**Modular monolith → phased towards service separation.**

Phase 1–2: Single Next.js app + Python LangGraph backend. No microservices.
Phase 3+: Separate Railway services as complexity warrants — but only when the loop is validated.

Rationale: Microservices overhead is not justified at V1. The user is solo, learning the stack, and needs to ship fast. Separation happens when a service boundary becomes genuinely painful, not before.

## Module / Service Boundaries

| Module | Owns | Does Not Own |
|--------|------|--------------|
| Next.js frontend | UI, SSE streaming, session rendering | Agent logic, state management |
| LangGraph Python backend | Agent orchestration, graph execution, state | UI concerns, auth enforcement |
| Postgres | State persistence (LangGraph checkpointer), user/session data | File storage |
| BullMQ + Redis | Background job queue (Blueprint Scout, Curriculum Builder) | Foreground session execution |

## Core Domain Models

| Entity | Purpose | Essential Fields |
|--------|---------|-----------------|
| User | Authenticated learner | id, clerk_user_id, created_at |
| Exam | A certification being prepped for | id, name, blueprint (domains + weights) |
| Curriculum | Personalised study plan for a user + exam | id, user_id, exam_id, domains[], created_at |
| Domain | A weighted exam topic | id, exam_id, name, weight (float), display_order |
| Session | A single study session (one full Rex+Sage loop) | id, user_id, exam_id, started_at, ended_at, exchanges[] |
| Exchange | One Rex→Sage→Rex cycle within a session | id, session_id, domain, topic, challenge, user_answer, outcome (correct/incorrect), sage_response, rechallenge, rechallenge_outcome |
| Performance | Aggregate accuracy per domain per user | user_id, domain_id, correct_count, total_count, last_updated |
| RexRecord | Running win/loss rivalry tally | user_id, rex_wins, user_wins |

## Data Flow

### Core session flow (Rex + Sage loop)
```
User opens session
  → coach_open node: pulls curriculum, selects domain + topic for today
  → rex_challenge node: generates scenario-based challenge for selected topic
  → SSE streams challenge card to frontend
  → User submits answer
  → evaluate_answer node: LLM evaluates correctness
  → conditional_edge:
      correct  → sage_depth node (adds depth, elaborates on topic)
      incorrect → sage_explain node (explains the gap, clarifies misconception)
  → SSE streams Sage response below challenge card
  → rex_rechallenge node: generates harder variant on same domain
  → Exchange written to Postgres
  → Repeat × 2 cycles
  → coach_close node: summarises session, updates readiness score
  → Performance aggregates updated
```

### Onboarding flow
```
User submits exam name + learning style
  → OnboardingSubgraph: stores intake to Postgres
  → BackgroundSubgraph dispatched via BullMQ:
      blueprint_scout: loads hardcoded DVA-C02 blueprint (Phase 1-2)
                       → scrapes official exam guide (Phase 3+)
      curriculum_builder: builds personalised domain ordering
  → Frontend shows live agent feed (SSE) while waiting
  → On completion: redirect to dashboard
```

## Async Infrastructure

| Job | Queue | Why async |
|-----|-------|-----------|
| blueprint_scout | BullMQ | Can be slow (scraping in Phase 3+); must not block onboarding UI |
| curriculum_builder | BullMQ | LLM call that can take 5–15s; runs after blueprint_scout completes |
| resource_gatherer | BullMQ (v1.1) | Constant background crawl; async by nature |

## External Integration Abstractions
<!-- GAP: Interface names not formally defined — placeholder below -->

| Module | Interface (proposed) | Current Provider |
|--------|---------------------|-----------------|
| LLM calls | `LLMProvider` | OpenRouter |
| Web search | `SearchProvider` | Tavily or Serper (Phase 3+) |
| Auth | `AuthProvider` | Clerk (Phase 4) |
| Job queue | `JobQueue` | BullMQ + Redis |
| Streaming | `StreamTransport` | SSE |

*Note: Concrete interface signatures to be defined before Phase 2 when providers are first meaningfully swappable.*

## State Machines

### Session state
```
IDLE → ACTIVE (user opens session)
ACTIVE → CHALLENGE_PENDING (coach_open complete)
CHALLENGE_PENDING → AWAITING_ANSWER (rex_challenge streamed)
AWAITING_ANSWER → EVALUATING (user submits answer)
EVALUATING → SAGE_RESPONDING (evaluation complete)
SAGE_RESPONDING → RECHALLENGING (sage response complete)
RECHALLENGING → AWAITING_ANSWER (2nd cycle) | CLOSING (2 cycles done)
CLOSING → COMPLETE (coach_close done)
```

### LangGraph shared state object
```python
class AppState(TypedDict):
    user_id: str
    exam_id: str
    learning_style: str
    curriculum: list[Domain]
    current_domain: str
    current_topic: str
    session_history: list[Exchange]
    rex_difficulty: str        # easy | medium | hard
    rex_record: dict           # {rex_wins: int, user_wins: int}
    exam_readiness_score: float
```

## LangGraph Graph Structure
```
ParentGraph (orchestrator)
├── OnboardingSubgraph
│   ├── node: collect_exam_and_style
│   └── node: route_to_background_agents
├── BackgroundSubgraph (async via BullMQ)
│   ├── node: blueprint_scout
│   ├── node: resource_gatherer        ← v1.1
│   └── node: curriculum_builder
└── SessionSubgraph
    ├── node: coach_open
    ├── node: rex_challenge
    ├── node: evaluate_answer
    ├── conditional_edge: correct → sage_depth | incorrect → sage_explain
    ├── node: sage_respond
    ├── node: rex_rechallenge
    └── node: coach_close
```

## Failure Handling
<!-- GAP: Not formally defined — needs grilling for each external dependency -->

| Dependency | Failure scenario | Current handling |
|------------|-----------------|-----------------|
| OpenRouter | LLM call fails / times out | *Undefined — needs decision* |
| BullMQ / Redis | Job queue unavailable | *Undefined — needs decision* |
| Postgres | DB connection lost mid-session | *Undefined — needs decision* |
| Clerk (Phase 4+) | Auth service unavailable | *Undefined — needs decision* |
| Tavily/Serper (Phase 3+) | Search API fails during blueprint scrape | *Undefined — needs decision* |

## AI/ML Trust Architecture
Rex and Sage generate challenge content and evaluation responses — they do **not** directly mutate any persistent state. The flow is:

```
LLM output → evaluate_answer node (application code validates + classifies)
           → state update written by application code
           → Postgres write via LangGraph checkpointer
```

Model outputs never directly update the database. The `evaluate_answer` node is application-layer code that decides what the outcome means and what gets written.

## Audit and Traceability
- Every Exchange (challenge, answer, outcome, Sage response) is written to Postgres — immutable record of what happened in each session
- LangGraph Postgres checkpointer stores full graph state at each node — full replay capability
- Performance aggregates are derived from Exchanges, not manually editable
- Auth events handled by Clerk (Phase 4+)

## Implementation Sequence
1. Rex + Sage nodes (raw OpenRouter calls, no LangGraph) — Phase 1
2. LangGraph SessionSubgraph + Postgres checkpointer — Phase 2
3. OnboardingSubgraph + BackgroundSubgraph + BullMQ — Phase 3
4. Clerk auth integration + full state wired to real user_id — Phase 4
5. PWA config + mobile polish + gamification layer — Phase 5
