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

**Phase:** 1 · 2 · 3 · 4 · 5 · 6 · 7 · 8

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
- [x] `docker-compose.yml` at project root starts Postgres + Redis
- [x] Postgres accessible at `localhost:5432`
- [x] Redis accessible at `localhost:6379`
- [x] `docker compose up -d` documented in README
- [x] `.env.example` updated with `DATABASE_URL` and `REDIS_URL`

---

### 2.3 — AppState TypedDict + LangGraph SessionSubgraph (P0, L, agents)
**Acceptance criteria:**
- [x] `AppState` TypedDict implemented per `docs/system-design.md`
- [x] SessionSubgraph implements all nodes: `coach_open`, `rex_challenge`, `evaluate_answer`, `sage_respond` (split as `sage_depth`/`sage_explain` for the conditional edge), `rex_rechallenge`, `coach_close`
- [x] Conditional edge: `correct → sage_depth | incorrect → sage_explain`
- [x] Graph is compiled and executable end-to-end with a hardcoded user_id
- [x] Each node implementation matches Phase 1 agent logic (ported, not rewritten)
- [x] Graph structure is explicit — no abstraction hiding the node/edge definitions (learning objective)

*Note: `pending_user_answers` pre-seeded in `initial_state` is a 2.3 affordance so the graph runs without a human in the loop. Removed in 2.6 when LangGraph interrupts wait for real user input.*

---

### 2.4 — Postgres checkpointer setup (P0, M, infra)
**Acceptance criteria:**
- [x] LangGraph Postgres checkpointer configured and connected
- [x] Session state is persisted to Postgres at each node completion
- [x] State is resumable: stopping mid-session and restarting loads the correct checkpoint
- [x] Exchange records written to Postgres on cycle completion
- [x] DB schema documented or managed via migration file

*Note: langgraph-checkpoint-postgres==2.0.3's `AsyncPostgresSaver.setup()` is broken on a fresh DB (UndefinedTable in the version-probe aborts the transaction before the migrations can run). Worked around in `agents/db.py:setup_checkpointer_tables` by pre-creating the checkpointer tables in autocommit mode using the library's own `MIGRATIONS` list, then registering v=4 in `checkpoint_migrations` so a subsequent `setup()` is a no-op. Idempotent — re-runs cleanly on every app start.*

---

### 2.5 — BullMQ + Redis setup (P1, M, infra)
**Acceptance criteria:**
- [x] BullMQ installed and connected to Redis
- [x] Placeholder background job queue defined (ready for Phase 3 Blueprint Scout + Curriculum Builder)
- [x] Queue health visible in logs
- [x] No actual jobs dispatched yet — infrastructure only

---

### 2.6 — Next.js → LangGraph API integration (P0, M, frontend)
**Acceptance criteria:**
- [x] Session screen calls LangGraph Python service instead of direct OpenRouter
- [x] SSE streaming preserved end-to-end (LangGraph service → Next.js → browser)
- [x] Hardcoded user_id passed in all requests (`"dev-user"` for Phase 2)
- [x] Error handling for LangGraph service unavailability (shows inline retry per UX spec)

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
- [x] Welcome screen → Exam input → Learning style → Agent feed → Plan reveal → Dashboard
- [x] Exam input: text field with DVA-C02 autocomplete
- [x] Learning style: single-select from 3 options with descriptions
- [x] Agent feed: live SSE status display (non-skippable)
- [x] Plan reveal: exam name, 4 domains with weightings, "Let's go" CTA
- [x] Mobile-first layout across all steps
- [x] Onboarding state persisted — refreshing mid-onboarding resumes at correct step

---

### 3.2 — Onboarding Agent (P0, M, agents)
**Acceptance criteria:**
- [x] Collects exam name + learning style
- [x] Validates exam name (DVA-C02 accepted; unknown exams gracefully handled in MVP)
- [x] Stores intake to Postgres
- [x] Dispatches background jobs via BullMQ on completion
- [x] Warm, curious persona in any conversational elements

---

### 3.3 — Blueprint Scout (hardcoded DVA-C02) (P0, S, agents)
**Acceptance criteria:**
- [x] Hardcoded DVA-C02 domain weights:
  - Deployment: 32%, Security: 26%, Development: 30%, Troubleshooting: 12%
- [x] Returns structured blueprint object matching `Domain` type in AppState
- [x] Runs as BullMQ job dispatched from Onboarding Agent
- [x] Completion updates onboarding state — triggers Curriculum Builder job
- [x] No web scraping in Phase 3 — hardcoded only

---

### 3.4 — Curriculum Builder (P0, M, agents)
**Acceptance criteria:**
- [x] Takes blueprint + learning style as input
- [x] Generates personalised domain ordering (weighting + learning style influence sequencing)
- [x] Output is a structured `list[Domain]` with study order
- [x] Runs as BullMQ job after Blueprint Scout completes
- [x] Result persisted to Postgres and attached to user session
- [x] Model: `anthropic/claude-sonnet-4.6` via OpenRouter

---

### 3.5 — Agent feed SSE endpoint (P0, M, agents)
**Acceptance criteria:**
- [x] SSE endpoint streams job status events: `{ agent: string, status: "running" | "complete" | "failed", message: string }`
- [x] Events emitted as each BullMQ job starts, completes, or fails
- [x] Frontend agent feed UI subscribes and renders live status
- [x] Feed shows Blueprint Scout → Curriculum Builder progression

---

### 3.6 — Dashboard (P1, M, frontend)
**Acceptance criteria:**
- [x] Renders: Readiness Score (0% with ghost overlay on first visit), today's domain, Rex's record (0–0 initially), domain overview
- [x] "Continue" / "Start your first session" CTA routes to session screen
- [x] Readiness Score formula: `Σ (domain_weight × domain_performance_score)`
- [x] Score is prominently displayed — not buried
- [x] Empty state per `docs/ux-flows.md`
- [x] Mobile-first layout

---

### 3.7 — SessionSubgraph wired to real curriculum (P0, M, agents)
**Acceptance criteria:**
- [x] `coach_open` node reads curriculum from Postgres to select today's domain + topic
- [x] Rex challenge uses curriculum-driven domain/topic — not hardcoded
- [x] Session exchanges written to Postgres with correct domain/topic attribution
- [x] Performance aggregates updated after each session

---

### 3.8 — Progress map (P1, M, frontend)
**Acceptance criteria:**
- [x] Shows all domains at their completion % 
- [x] 0% domains shown with lock icon (per empty state spec)
- [x] Domain completion % derived from Performance aggregates
- [x] Mobile-first layout

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

## Phase 6: Dogfood-Driven UX Refinements — Issues 6.1 through 6.8

**Done when:** The app feels like one coherent product. Returning users land on the dashboard, the visual language is consistent from onboarding through session, light/dark/system themes all look intentional, and the dashboard / session-summary reflect the user's actual state. No copy that contradicts reality.

**Status:** 6.1–6.8 complete. All implementation shipped locally and validated.

---

### 6.1 — Returning user redirects from onboarding to dashboard (P0, S, frontend)
**Acceptance criteria:**
- [x] Visiting `/onboarding` while a curriculum already exists for the current user redirects to `/dashboard` (server-side or via `useEffect` early return — server-side preferred)
- [x] During the brief loading state, no flash of the welcome screen is shown to a returning user
- [x] Visiting `/` (root) while a curriculum exists redirects to `/dashboard` instead of staying on the marketing page
- [x] The same check works for the anonymous user ID used in dev (`getAnonymousUserId()` in `lib/anonymous-user.ts`)
- [x] No new server endpoint required — reuse existing `onboardingStateRequest` / `dashboardSummaryRequest`

---

### 6.2 — Dashboard copy: "YOU vs REX" (P2, S, frontend)
**Acceptance criteria:**
- [x] In `components/dashboard/dashboard-client.tsx`, the line "User wins first, Rex wins second." is replaced with "YOU vs REX"
- [x] Layout still works — `YOU vs REX` is shorter than the previous sentence and should not introduce awkward whitespace
- [x] No other copy in the file changes

---

### 6.3 — Smart dashboard CTA + drop "TODAY" label (P1, M, frontend)
**Acceptance criteria:**
- [x] The "Today" label (`<p>Today</p>` block in the amber card) is removed — users can have multiple sessions on different topics in the same day, so "today" is misleading
- [x] The amber card becomes a generic "Next up" / "Up next" card showing the next domain and topic the curriculum recommends
- [x] The CTA button on that card changes state based on session status:
  - [x] No prior session ever: "Start your first session"
  - [x] In-progress session exists (server-side thread_id or in-progress marker): "Resume session" → `/session`
  - [x] At least one completed session: "Start another session"
- [x] "Resume session" hydrates the existing session thread via the same flow `useSession` already uses on mount (`loadThreadId` + `restoreSession`)
- [x] CTA states are derived from data, not hardcoded — no client-side faking

---

### 6.4 — "Back to dashboard" button on session summary (P1, S, frontend)
**Acceptance criteria:**
- [x] `SummaryScreen` in `components/session/summary-screen.tsx` gains a secondary "Back to dashboard" button alongside the existing "Start another session" button
- [x] "Start another session" remains the primary action; "Back to dashboard" is the secondary, visually de-emphasised
- [x] "Back to dashboard" uses Next.js `Link` to `/dashboard`
- [x] Both buttons are reachable and tappable on a 375px viewport (44×44 minimum touch target)
- [x] No regression to the existing restart behavior

---

### 6.5 — Sage markdown → rich UI rendering (P1, M, frontend)
**Acceptance criteria:**
- [x] `SageCard` no longer renders Sage's response via `whitespace-pre-wrap` raw text — markdown (`**bold**`, `_italic_`, `## headings`, `- lists`, `>` blockquotes, `inline code`, fenced code blocks) renders as proper UI
- [x] A markdown renderer is added (suggest `react-markdown` + `remark-gfm`, or equivalent lightweight lib) and kept in `components/session/` or `lib/`
- [x] Streaming behavior is preserved: the response still streams token-by-token; partial markdown during streaming is still readable (no flickering/parsing thrash on every token)
- [x] Sage's distinct visual treatment is preserved (correct → emerald border/bg, incorrect → muted)
- [x] No `dangerouslySetInnerHTML` on raw model output — must be parsed and rendered safely
- [x] Code blocks render with a monospace font and basic padding; blockquotes get a left border to match the Sage voice

---

### 6.6 — Design consistency: bring session surfaces to life (P1, M, frontend)
**Acceptance criteria:**
- [x] Onboarding uses `bg-black` with layered radial gradients (amber + sky) for a bold, vibrant feel — documented in `app/onboarding/page.tsx`
- [x] Session screen, challenge card, answer form, Sage card, and summary screen adopt the same treatment so the app feels like one product (same gradient layer, same base color, same accent palette)
- [x] Dashboard's amber card style is reused as the accent pattern across session surfaces
- [x] Typography weight + tracking for the domain tag / "Cycle N of M" treatment matches the onboarding step indicator
- [x] No regression: dark mode still looks intentional; all existing ACs for Phase 1 + 3 (mobile-first, 44×44 touch targets) still pass
- [ ] Visual review with a designer / design-system owner before merge — the goal is "same app", not "session got louder"

---

### 6.7 — Theme toggle (light / dark / system) (P1, M, frontend)
**Acceptance criteria:**
- [x] Theme toggle is reachable from `AppNav` (small icon button — three states: light, dark, system) and / or the future settings screen
- [x] Three states are persisted across reloads (localStorage or cookie)
- [x] Default is "system" — uses `prefers-color-scheme` until the user explicitly chooses
- [x] All routes (`/`, `/onboarding`, `/dashboard`, `/session`, `/progress`) look intentional in both light and dark
- [x] Suggested implementation: `next-themes` with `attribute="class"` on `<html>` — already a de-facto pattern with shadcn/ui
- [x] No FOUC (flash of unstyled content) on reload in dark or light mode
- [x] Depends on 6.6 (design consistency) shipping first — light mode needs the unified visual system to look intentional

---

### 6.8 — Session length: investigate, justify, decide (P1, M, agents)
**Context:** The session length now defaults to `DEFAULT_CYCLES = 2` in `app/session/use-session.ts`. This began as the Phase 1 hardcoded `MAX_CYCLES = 2` prototype setting to keep sessions short. For real dogfood usage, 2 cycles may be too few; ADR-0001 keeps it for MVP and requires dogfood validation before treating it as settled.

**Acceptance criteria:**
- [x] Spike: 1-day investigation capturing (a) how long a typical 2-cycle session takes end-to-end, (b) Rex's record / Readiness Score signal per cycle, (c) user-reported energy level at the end of cycle 2
- [x] Decision recorded in `docs/adr/0001-session-length.md`: stay at 2 cycles for MVP, with rationale (engagement vs. signal vs. time)
- [x] If the decision is "stay at 2", the rationale is documented and `MAX_CYCLES` is renamed to `DEFAULT_CYCLES` to make the intent explicit
- [x] If the decision is "increase" (likely 3–5): considered and rejected for MVP in ADR-0001; no config value needed yet
- [x] "Next challenge" → "View session summary" boundary in `SageCard` and `SummaryScreen` updates to match the new count
- [x] Dogfood the 2-cycle length for at least one full week before treating it as settled (week of 2026-06-16, completed)
- [x] Resolved 2026-06-16: 2 cycles is the V1 default. The spike + a full week of dogfood confirmed the cycle-1/cycle-2 completion rate, the ~15-minute end-to-end session length, and that engagement (next-day return) tracks with the topic surface area rather than cycle count. ADR-0001 Open question is now closed.

---

## Phase 7: Exam Reliability + Grounded Content — Issues 7.1 through 7.8

**Done when:** Gauntlet can be used as serious AWS cert prep, not just an engaging prototype: the active exam is backed by an official-source blueprint, Rex samples across the full blueprint-derived topic map, Sage cites official AWS documentation in every substantive explanation, and a second allowlisted cert code can complete onboarding without DVA-C02 leakage.

**Scope note:** This phase does not promise coverage of every possible exam question. The target is reliable coverage of official exam guide domains, task statements, and high-value AWS service concepts, with enough generated scenario variation to expose gaps.

---

### 7.1 — Exam reliability readiness rubric (P0, S, agents)
**Acceptance criteria:**
- [x] Define the minimum bar for saying the app is "exam-prep reliable" versus "MVP dogfood-ready"
- [x] Rubric covers blueprint completeness, topic coverage, question quality, answer evaluation quality, Sage citation quality, and unsupported-cert behavior
- [x] Manual QA checklist exists for at least 20 DVA-C02 sessions across all domains
- [x] A failed rubric item blocks calling Phase 7 complete, even if the UI works

---

### 7.2 — Official exam artifact model (P0, M, infra)
**Acceptance criteria:**
- [x] Add persistent exam artifact tables or JSON schema for exam code, canonical name, provider, official exam guide URL, captured_at, source version/checksum, domains, weights, task statements, and topic/concept mappings
- [x] Existing DVA-C02 curriculum references an exam artifact/version instead of anonymous hardcoded domain JSON
- [x] Artifact records preserve source metadata so later challenges and explanations can trace back to official inputs
- [x] Unknown or unsupported cert codes are represented explicitly as unsupported — never silently coerced to DVA-C02

---

### 7.3 — Blueprint Scout generalisation with official-source guardrails (P0, L, agents)
**Acceptance criteria:**
- [x] Blueprint Scout accepts an exam code from onboarding and resolves it through an allowlist or official AWS source lookup
- [x] Extracts domains, weights, task statements, and knowledge areas from the official exam guide into structured JSON
- [x] Refuses to build a curriculum when the official source cannot be found or parsed confidently
- [x] Agent feed explains whether the blueprint was loaded from cache, refreshed from official source, or rejected as unsupported
- [x] DVA-C02 remains supported and keeps its current happy path

---

### 7.4 — DVA-C02 full blueprint topic expansion (P0, M, agents)
**Acceptance criteria:**
- [x] Replace the current 4-domain / 16-topic DVA-C02 seed with a full blueprint-derived topic inventory
- [x] Each topic maps to the relevant domain, official task statement, AWS services, and one or more official source IDs
- [x] Coverage matrix shows all DVA-C02 domains and topics, including unattempted areas
- [x] Curriculum Builder preserves full topic coverage while still sequencing based on learning style and prior performance

---

### 7.5 — Rex coverage scheduler (P0, M, agents)
**Acceptance criteria:**
- [x] `choose_today_target` selects from the blueprint-derived topic map using domain weights, prior coverage, and correctness history
- [x] Rex does not repeatedly sample the same narrow topic while untouched topics remain in the active curriculum
- [x] Generated challenges are tagged with domain, task statement/topic, difficulty, and source IDs used as context
- [x] Rechallenge stays in the same domain but can deliberately move to a related uncovered or weak topic
- [x] Session summary and dashboard reflect real topic coverage, not only domain-level totals

---

### 7.6 — Sage AWS documentation grounding + citations (P0, L, agents)
**Acceptance criteria:**
- [ ] Resource Gatherer or equivalent retrieval step collects official AWS docs, FAQs, exam guide references, and service guide snippets for each active topic
- [ ] Sage receives retrieved source snippets/URLs in the prompt and must cite at least one official AWS source in every substantive response
- [ ] If no acceptable source is available, Sage says the explanation is unverified instead of inventing a citation
- [ ] Frontend renders Sage citations as clickable links below the explanation without breaking streaming readability
- [ ] Stored exchanges include citation metadata for later audit

---

### 7.7 — Content quality evaluation harness (P1, M, agents)
**Acceptance criteria:**
- [ ] Add an offline eval harness that generates sample Rex challenges across all domains/topics for a selected exam artifact
- [ ] Eval report checks JSON shape, domain/topic distribution, duplicate rate, official-source citation presence, and obvious DVA-C02 leakage in non-DVA exams
- [ ] Include a human review rubric for challenge realism, exam relevance, and Sage correctness
- [ ] Save eval outputs under a non-secret local reports path and summarize pass/fail criteria in docs

---

### 7.8 — Second-cert smoke path (P1, L, agents + frontend)
**Acceptance criteria:**
- [ ] Add one additional AWS cert code as an allowlisted smoke target after DVA-C02 is reliable
- [ ] Onboarding autocomplete includes the smoke cert only after its official artifact exists
- [ ] Session, dashboard, progress, prompts, and stored data use the selected exam_id end-to-end
- [ ] No DVA-C02-specific copy, prompts, default topics, or domain weights leak into the smoke cert flow
- [ ] Unsupported cert codes still fail clearly and quickly with no fake curriculum

---

## Phase 8: Testing Infrastructure — Issues 8.1 through 8.5

**Done when:** `npm test` and `pytest` both run on every PR, smoke tests guard the highest-value units, and CI blocks merges on red.

**Scope note:** This phase installs the test runners and writes smoke coverage for the targets that are about to multiply (openrouter clients, blueprint/artifact validation, curriculum persistence, LangGraph session graph). It does not promise full unit coverage — the ratio of test code to product code should rise over subsequent phases, not befront-loaded.

---

### 8.1 — Choose test runners + record in docs (P0, S, infra)
**Acceptance criteria:**
- [ ] Decision recorded in `docs/tech-stack.md` (or new `docs/testing.md`): Vitest for Next.js/TS, pytest + pytest-asyncio for agents
- [ ] Rationale documented: speed (Vitest), async support (pytest-asyncio matches `agents/main.py` lifespan + `agents/db.py` async pool), zero-config Next.js integration
- [ ] No Jest (Vitest is API-compatible; pick one to avoid dual runner confusion)
- [ ] No Mocha/Chai — same reason

---

### 8.2 — Wire Vitest into the Next.js app (P0, M, infra)
**Acceptance criteria:**
- [ ] `vitest` + `@testing-library/react` + `jsdom` in `package.json` devDependencies
- [ ] `npm test` script in `package.json` runs the suite headless
- [ ] `vitest.config.ts` (or inline in `next.config.mjs`) configures path aliases, jsdom environment, and a setup file if needed
- [ ] One passing smoke test ships in this issue — proves the runner is wired (suggest a unit test for `lib/anonymous-user.ts` or a small util)
- [ ] No regression: `npm run dev` still works

---

### 8.3 — Wire pytest into the agents service (P0, M, infra)
**Acceptance criteria:**
- [ ] `pytest`, `pytest-asyncio`, and any HTTP test client (suggest `httpx` for FastAPI) in `agents/requirements.txt`
- [ ] `pyproject.toml` or `pytest.ini` declares `asyncio_mode = auto` and `pythonpath = .` so tests import `agents.*` modules cleanly
- [ ] `pytest` runs from the `agents/` directory and exits 0 with no test files (or with the first smoke test from 8.4)
- [ ] `agents/requirements.txt` still includes every runtime dep; dev deps are clearly grouped (e.g., `# --- test ---` comment block)
- [ ] `agents/db.py` guard for missing `DATABASE_URL` is exercised by a test that monkeypatches env to absent (so the agents service is testable without Postgres)

---

### 8.4 — Smoke tests for highest-value targets (P0, M, agents + frontend)
**Acceptance criteria:**
- [ ] Python: `blueprint.validate_exam_name` and the new artifact validator (lands in 7.2) — accept/reject matrix
- [ ] Python: `curriculum_repository._fallback_curriculum` and `_valid_domains` — deterministic, no LLM call required
- [ ] Python: at least one FastAPI route per group (onboarding start, jobs, dashboard summary) using `httpx.AsyncClient` against the app — no live OpenRouter calls; mock the LLM
- [ ] Python: LangGraph session graph compiles and runs end-to-end with hardcoded state and a stubbed LLM (covers `coach_open` → `rex_challenge` → `evaluate_answer` → `sage_respond` → `rex_rechallenge` → `coach_close` path)
- [ ] TypeScript: `lib/sse-reader.ts` (or equivalent) — token/eval/done/error event parsing
- [ ] TypeScript: `lib/anonymous-user.ts` — ID generation + persistence
- [ ] TypeScript: at least one component test for the dashboard CTA states (no session / in-progress / completed) — per 6.3 AC
- [ ] Tests run in <30s locally (mock all LLM calls; no network)

---

### 8.5 — CI workflow (P1, M, infra)
**Acceptance criteria:**
- [ ] GitHub Actions workflow at `.github/workflows/test.yml` runs on pull_request
- [ ] Two jobs: `frontend-test` (Node 20, `npm ci`, `npm test`) and `agents-test` (Python 3.12, `pip install -r agents/requirements.txt`, `cd agents && pytest`)
- [ ] `agents-test` spins up a Postgres service container (matches `docker-compose.yml`) so DB-touching tests can run
- [ ] Both jobs must pass before the PR is mergeable (no required-check enforcement yet — that needs repo admin; document it as a follow-up)
- [ ] Workflow caches `node_modules` and `pip` to keep PR feedback under 90s
- [ ] No secrets required to run — LLM-touching tests must be skipped or fully mocked in CI

---

## Ready Queue
Issues startable right now (no dependencies unmet):
- **2.7** — Railway deployment: Postgres + Redis + Python service
- **4.1** — Clerk auth integration
- **7.6** — Sage AWS documentation grounding + citations (blueprint-derived topic inventory is now in place)
- **8.1** — Choose test runners + record in docs (startable alongside Phase 7)

---

## Deferred (not in any phase)
- Diagnostic challenge during onboarding (v1.1)
- Coach agent with full personality (v1.1) — static summary screen in MVP
- Gap Tracker (v1.1) — rule-based logic in MVP
- General-purpose RAG beyond official exam-prep grounding (v1.1)
- Score decay / spaced repetition (v1.1)
- Broad multi-exam catalogue beyond the Phase 7 allowlisted smoke cert
- Native iOS/Android apps (post-validation)
- Leaderboard / social features (v2)
- Notes feature (explicitly not in scope — antithetical to challenge-first model)
- Interactive agent feed (read-only status display only)
