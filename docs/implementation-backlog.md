# Implementation Backlog
Status: first-pass | Date: 2026-06-15

## Labels

**Priority**
- P0 — blocking milestone; phase cannot close without it
- P1 — important for phase; ships with phase
- P2 — nice to have; can slip to next phase

**Size**
- S — < 0.5 day
- M — 0.5–2 days
- L — 2–5 days

**Phase:** 1 · 2 · 3 · 4 · 5

**Area:** frontend · agents · infra · auth · gamification

---

## Working Rules
- No phase closes until the Definition of Done is met end-to-end
- Security and observability ACs are embedded in feature tickets — not separate hardening tickets
- Phase 1 has no infrastructure dependency — raw OpenRouter calls from Next.js only
- Auth (Clerk) is Phase 4 — do not introduce user identity before then
- LangGraph is introduced in Phase 2 — Phase 1 uses direct API calls only

---

## Phase 1: Rex + Sage Loop — Issues 1.1 through 1.9

**Done when:** Complete a Rex→Sage→Rex exchange on a hardcoded DVA-C02 topic and it feels genuinely engaging. You want to do another.

---

### 1.1 — Project scaffold (P0, S, frontend)
**Acceptance criteria:**
- [x] Next.js app initialised with App Router
- [x] shadcn/ui installed and configured
- [x] `.env.example` contains `OPENROUTER_API_KEY`
- [x] `npm run dev` starts the app on :3000 with no errors
- [x] Basic folder structure matches `docs/tech-stack.md` (`app/`, `lib/`, `agents/`)

---

### 1.2 — OpenRouter client utility (P0, S, agents)
**Acceptance criteria:**
- [x] `lib/openrouter.ts` wraps OpenRouter API calls
- [x] Accepts model ID, system prompt, and user message
- [x] Returns streamed response via SSE
- [x] Handles API errors with typed error responses (not raw throws)
- [x] `OPENROUTER_API_KEY` read from env — never hardcoded

---

### 1.3 — Rex challenge generation (P0, M, agents)
**Acceptance criteria:**
- [x] Rex system prompt implemented — competitive, ruthless persona
- [x] Generates scenario-based challenge for a hardcoded DVA-C02 topic (Deployment domain)
- [x] Challenge includes: scenario description, question, and domain + topic tag
- [x] Response is structured (JSON or clearly parseable) — not free prose
- [x] Hardcoded topic for Phase 1 — no curriculum selection yet
- [x] Model: `anthropic/claude-sonnet-4.6` via OpenRouter

---

### 1.4 — Session screen UI — challenge card (P0, M, frontend)
**Acceptance criteria:**
- [x] Full-focus layout — no navigation visible
- [x] Challenge card renders: domain tag, topic tag, scenario text, question
- [x] Mobile-first layout — card readable and usable on 375px viewport
- [x] Text answer input field below challenge
- [x] Submit button — disabled until user has typed something
- [x] Loading state while Rex generates (skeleton or spinner on card)

---

### 1.5 — Answer evaluation (P0, M, agents)
**Acceptance criteria:**
- [x] Evaluation prompt assesses user answer against challenge
- [x] Returns structured result: `{ outcome: "correct" | "incorrect", reasoning: string }`
- [x] Outcome used to route to Sage depth vs Sage explain
- [x] Evaluation is strict — partial credit counts as incorrect for MVP
- [x] Model: `anthropic/claude-sonnet-4.6` via OpenRouter
- [x] Evaluation logged to console in dev (outcome + reasoning) for QA purposes

---

### 1.6 — Sage response (P0, M, agents)
**Acceptance criteria:**
- [x] Two Sage prompts: `sage_depth` (correct path) and `sage_explain` (incorrect path)
- [x] Sage persona implemented — dry wit, never lectures, confident and specific
- [x] `sage_explain`: explains the gap, corrects the misconception, cites relevant AWS service/concept directly. No hedging.
- [x] `sage_depth`: adds depth beyond the correct answer — what else is worth knowing about this topic
- [x] Response streams to frontend via SSE
- [x] Model: `anthropic/claude-sonnet-4.6` via OpenRouter

---

### 1.7 — Session screen UI — Sage response (P0, M, frontend)
**Acceptance criteria:**
- [x] Sage response animates in below the challenge card after evaluation
- [x] Distinct visual treatment from Rex card (different background, typography weight, or border — clearly a different voice)
- [x] Streams in token-by-token (SSE) — not a loading spinner then full dump
- [x] Correct/incorrect outcome subtly reflected in card treatment (green/neutral — no red, no alarm)
- [x] "Next challenge" CTA appears after Sage response completes

---

### 1.8 — Rex rechallenge (P0, M, agents)
**Acceptance criteria:**
- [x] Rex generates a harder variant on the same domain after Sage responds
- [x] Rechallenge prompt references that the user has just seen Sage's explanation — raises the stakes
- [x] Difficulty is explicitly incremented in the prompt (same domain, harder scenario)
- [x] Loop completes after 2 full cycles (challenge → eval → sage → rechallenge × 2)
- [x] After 2nd cycle: session summary screen rendered (static for Phase 1)

---

### 1.9 — Static session summary screen (P0, S, frontend)
**Acceptance criteria:**
- [x] Shows: number of correct answers out of total, domain covered
- [x] "Start another session" CTA resets and restarts the loop
- [x] No score persistence in Phase 1 — purely in-memory display
- [x] Mobile-first layout

---

## Phase 2: LangGraph + State Persistence — Issues 2.1 through 2.7

**Done when:** Reload the page mid-session. Your session is intact.

---

### 2.1 — Python LangGraph service scaffold (P0, S, infra)
**Acceptance criteria:**
- [x] Python project initialised in `agents/` with `pyproject.toml` or `requirements.txt`
- [x] FastAPI or equivalent serving LangGraph graph over HTTP
- [x] `uvicorn main:app --reload` starts on :8000 with no errors
- [x] Health check endpoint: `GET /health` returns 200
- [x] `OPENROUTER_API_KEY` and `DATABASE_URL` read from env

---

### 2.2 — Docker Compose for local dev (P0, S, infra)
**Acceptance criteria:**
- [ ] `docker-compose.yml` at project root starts Postgres + Redis
- [ ] Postgres accessible at `localhost:5432`
- [ ] Redis accessible at `localhost:6379`
- [ ] `docker compose up -d` documented in README
- [ ] `.env.example` updated with `DATABASE_URL` and `REDIS_URL`

---

### 2.3 — AppState TypedDict + LangGraph SessionSubgraph (P0, L, agents)
**Acceptance criteria:**
- [ ] `AppState` TypedDict implemented per `docs/system-design.md`
- [ ] SessionSubgraph implements all nodes: `coach_open`, `rex_challenge`, `evaluate_answer`, `sage_respond`, `rex_rechallenge`, `coach_close`
- [ ] Conditional edge: `correct → sage_depth | incorrect → sage_explain`
- [ ] Graph is compiled and executable end-to-end with a hardcoded user_id
- [ ] Each node implementation matches Phase 1 agent logic (ported, not rewritten)
- [ ] Graph structure is explicit — no abstraction hiding the node/edge definitions (learning objective)

---

### 2.4 — Postgres checkpointer setup (P0, M, infra)
**Acceptance criteria:**
- [ ] LangGraph Postgres checkpointer configured and connected
- [ ] Session state is persisted to Postgres at each node completion
- [ ] State is resumable: stopping mid-session and restarting loads the correct checkpoint
- [ ] Exchange records written to Postgres on cycle completion
- [ ] DB schema documented or managed via migration file

---

### 2.5 — BullMQ + Redis setup (P1, M, infra)
**Acceptance criteria:**
- [ ] BullMQ installed and connected to Redis
- [ ] Placeholder background job queue defined (ready for Phase 3 Blueprint Scout + Curriculum Builder)
- [ ] Queue health visible in logs
- [ ] No actual jobs dispatched yet — infrastructure only

---

### 2.6 — Next.js → LangGraph API integration (P0, M, frontend)
**Acceptance criteria:**
- [ ] Session screen calls LangGraph Python service instead of direct OpenRouter
- [ ] SSE streaming preserved end-to-end (LangGraph service → Next.js → browser)
- [ ] Hardcoded user_id passed in all requests (`"dev-user"` for Phase 2)
- [ ] Error handling for LangGraph service unavailability (shows inline retry per UX spec)

---

### 2.7 — Railway deployment: Postgres + Redis + Python service (P1, L, infra)
**Acceptance criteria:**
- [ ] Postgres provisioned on Railway
- [ ] Redis provisioned on Railway
- [ ] Python LangGraph service deployed as Railway service
- [ ] Next.js deployed as Railway service
- [ ] All services communicate via Railway internal networking
- [ ] Environment variables set in Railway dashboard

---

## Phase 3: Onboarding + Curriculum — Issues 3.1 through 3.8

**Done when:** A fresh user can input an exam → watch agents build curriculum → see plan reveal → land on dashboard. No hardcoded user_id.

---

### 3.1 — Onboarding flow UI (P0, L, frontend)
**Acceptance criteria:**
- [ ] Welcome screen → Exam input → Learning style → Agent feed → Plan reveal → Dashboard
- [ ] Exam input: text field with DVA-C02 autocomplete
- [ ] Learning style: single-select from 3 options with descriptions
- [ ] Agent feed: live SSE status display (non-skippable)
- [ ] Plan reveal: exam name, 4 domains with weightings, "Let's go" CTA
- [ ] Mobile-first layout across all steps
- [ ] Onboarding state persisted — refreshing mid-onboarding resumes at correct step

---

### 3.2 — Onboarding Agent (P0, M, agents)
**Acceptance criteria:**
- [ ] Collects exam name + learning style
- [ ] Validates exam name (DVA-C02 accepted; unknown exams gracefully handled in MVP)
- [ ] Stores intake to Postgres
- [ ] Dispatches background jobs via BullMQ on completion
- [ ] Warm, curious persona in any conversational elements

---

### 3.3 — Blueprint Scout (hardcoded DVA-C02) (P0, S, agents)
**Acceptance criteria:**
- [ ] Hardcoded DVA-C02 domain weights:
  - Deployment: 32%, Security: 26%, Development: 30%, Troubleshooting: 12%
- [ ] Returns structured blueprint object matching `Domain` type in AppState
- [ ] Runs as BullMQ job dispatched from Onboarding Agent
- [ ] Completion updates onboarding state — triggers Curriculum Builder job
- [ ] No web scraping in Phase 3 — hardcoded only

---

### 3.4 — Curriculum Builder (P0, M, agents)
**Acceptance criteria:**
- [ ] Takes blueprint + learning style as input
- [ ] Generates personalised domain ordering (weighting + learning style influence sequencing)
- [ ] Output is a structured `list[Domain]` with study order
- [ ] Runs as BullMQ job after Blueprint Scout completes
- [ ] Result persisted to Postgres and attached to user session
- [ ] Model: `anthropic/claude-sonnet-4.6` via OpenRouter

---

### 3.5 — Agent feed SSE endpoint (P0, M, agents)
**Acceptance criteria:**
- [ ] SSE endpoint streams job status events: `{ agent: string, status: "running" | "complete" | "failed", message: string }`
- [ ] Events emitted as each BullMQ job starts, completes, or fails
- [ ] Frontend agent feed UI subscribes and renders live status
- [ ] Feed shows Blueprint Scout → Curriculum Builder progression

---

### 3.6 — Dashboard (P1, M, frontend)
**Acceptance criteria:**
- [ ] Renders: Readiness Score (0% with ghost overlay on first visit), today's domain, Rex's record (0–0 initially), domain overview
- [ ] "Continue" / "Start your first session" CTA routes to session screen
- [ ] Readiness Score formula: `Σ (domain_weight × domain_performance_score)`
- [ ] Score is prominently displayed — not buried
- [ ] Empty state per `docs/ux-flows.md`
- [ ] Mobile-first layout

---

### 3.7 — SessionSubgraph wired to real curriculum (P0, M, agents)
**Acceptance criteria:**
- [ ] `coach_open` node reads curriculum from Postgres to select today's domain + topic
- [ ] Rex challenge uses curriculum-driven domain/topic — not hardcoded
- [ ] Session exchanges written to Postgres with correct domain/topic attribution
- [ ] Performance aggregates updated after each session

---

### 3.8 — Progress map (P1, M, frontend)
**Acceptance criteria:**
- [ ] Shows all domains at their completion % 
- [ ] 0% domains shown with lock icon (per empty state spec)
- [ ] Domain completion % derived from Performance aggregates
- [ ] Mobile-first layout

---

## Phase 4: Auth + Persistent Progress — Issues 4.1 through 4.5

**Done when:** Log in on a different device. Your progress, score, and Rex's record are there.

---

### 4.1 — Clerk auth integration (P0, L, auth)
**Acceptance criteria:**
- [ ] Clerk installed in Next.js (`@clerk/nextjs`)
- [ ] Sign up / sign in flows working
- [ ] All routes behind `/app` protected — redirect to sign-in if unauthenticated
- [ ] Clerk `userId` passed through to LangGraph service on all requests (replacing `"dev-user"`)
- [ ] Clerk unavailability handled gracefully: "Sign-in temporarily unavailable" (per UX spec)
- [ ] `CLERK_SECRET_KEY` + `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` in `.env.example`

---

### 4.2 — User table + data migration (P0, M, infra)
**Acceptance criteria:**
- [ ] `users` table created with `clerk_user_id` as the identity key
- [ ] All existing tables (`sessions`, `exchanges`, `performance`, `rex_record`) have `user_id` foreign key
- [ ] Migration script handles transition from hardcoded `"dev-user"` to real user IDs
- [ ] No cross-user data leakage — queries always scoped by `user_id`

---

### 4.3 — Exam Readiness Score (P0, M, agents)
**Acceptance criteria:**
- [ ] Score calculated as: `Σ (domain_weight × domain_performance_score)`
- [ ] `domain_performance_score` = correct_challenges / total_challenges per domain
- [ ] Score persisted to Postgres after every session
- [ ] Score displayed on dashboard with domain weight breakdown visible (not a black box)
- [ ] Ghost/projected score overlay shown at 0% (per empty state spec)

---

### 4.4 — Rex's record persistence (P1, M, agents)
**Acceptance criteria:**
- [ ] `rex_record` table stores `rex_wins` and `user_wins` per user
- [ ] Updated after every session cycle evaluation
- [ ] Displayed on dashboard
- [ ] Resets only on explicit "Reset progress" action (per destructive action spec)

---

### 4.5 — Settings screen (P1, S, frontend)
**Acceptance criteria:**
- [ ] Accessible from nav (not prominent — tucked away)
- [ ] "Change learning style" option — warns curriculum will rebuild
- [ ] "Reset exam progress" option — buried, 3s delay confirmation modal per UX spec
- [ ] Sign out option

---

## Phase 5: Polish + Dogfood — Issues 5.1 through 5.6

**Done when:** PWA installed and used for at least one week of real DVA-C02 prep.

---

### 5.1 — PWA configuration (P0, M, frontend)
**Acceptance criteria:**
- [ ] `manifest.json` configured with app name, icons, theme colour
- [ ] Service worker registered (Next.js PWA plugin or manual)
- [ ] "Add to Home Screen" prompt works on iOS Safari + Android Chrome
- [ ] Offline state: shows "You're offline — come back when connected" gracefully

---

### 5.2 — Mobile layout polish (P0, M, frontend)
**Acceptance criteria:**
- [ ] Full session loop tested and usable on 375px (iPhone SE) viewport
- [ ] No horizontal scroll on any screen
- [ ] Touch targets minimum 44×44px
- [ ] Keyboard behaviour on answer input field correct (no layout jump on focus)
- [ ] Bottom nav doesn't overlap content on any screen

---

### 5.3 — Streaks (P1, M, gamification)
**Acceptance criteria:**
- [ ] Streak counter tracks consecutive days with at least one completed session
- [ ] Displayed on dashboard
- [ ] Streak broken if no session completed on a calendar day (user's local timezone)
- [ ] No streak celebration animation — display update only

---

### 5.4 — Rex's record on session screen (P1, S, gamification)
**Acceptance criteria:**
- [ ] Rex's running record displayed during session (compact, not distracting)
- [ ] Updates live as each cycle completes
- [ ] Matches the record on dashboard

---

### 5.5 — Boss Battles (P2, L, gamification)
**Acceptance criteria:**
- [ ] Unlocks when a domain reaches a defined completion threshold (TBD — suggest 80% challenges complete)
- [ ] 10-challenge Rex gauntlet — no Sage safety net
- [ ] Boss Battle UI distinct from regular session (higher stakes visual treatment)
- [ ] "Domain complete" card on dashboard shows Boss Battle unlock teaser
- [ ] Boss Battle result recorded in performance aggregates

---

### 5.6 — Difficulty progression (P2, M, agents)
**Acceptance criteria:**
- [ ] Rex tracks rolling accuracy per domain across sessions
- [ ] Upgrades difficulty (easy → medium → hard) when accuracy exceeds threshold for 3 consecutive sessions on a domain
- [ ] Downgrades if accuracy drops below threshold for 2 consecutive sessions
- [ ] Difficulty level visible somewhere in session UI (subtle — domain tag or similar)

---

## Ready Queue
Issues startable right now (no dependencies unmet):
- **1.1** — Project scaffold

---

## Deferred (not in any phase)
- Diagnostic challenge during onboarding (v1.1)
- Coach agent with full personality (v1.1) — static summary screen in MVP
- Gap Tracker (v1.1) — rule-based logic in MVP
- Resource Gatherer + RAG pipeline (v1.1)
- Score decay / spaced repetition (v1.1)
- Multi-exam support beyond DVA-C02 (Phase 3+ generalisation, not in backlog yet)
- Native iOS/Android apps (post-validation)
- Leaderboard / social features (v2)
- Notes feature (explicitly not in scope — antithetical to challenge-first model)
- Interactive agent feed (read-only status display only)
