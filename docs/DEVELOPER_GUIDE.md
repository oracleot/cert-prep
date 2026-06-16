# Developer Guide

A practical onboarding doc for engineers ramping on the **Gauntlet** repo. Read this top-to-bottom on day one; it should take ~30 minutes plus the time to actually run the app.

For the system-level deep dive (data model, state machine, contracts, design rationale), see [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## 1. What is Gauntlet?

Gauntlet is an AI-powered AWS certification prep app. The user picks an exam (DVA-C02 in V1), watches background agents build a personalised curriculum, then runs short "Rex → Sage" study sessions. Rex throws a scenario-based challenge, the user answers, Sage explains the result with citations to AWS docs.

The product lives in two services:

- **Next.js** (`app/`, `lib/`, `components/`) — UI, SSE streaming, session orchestration on the client.
- **Python LangGraph** (`agents/`) — agent runtime, Postgres checkpointer, background job endpoints, exam-artifact store.

Storage: Postgres (app state + LangGraph checkpointer) and Redis (BullMQ, for the background jobs wired in Phase 3). LLM calls go through OpenRouter so we can mix model providers behind one key.

### Scope today (which phases are shipped)

| Phase | Status | What it adds |
|---|---|---|
| Phase 1 | Shipped | Rex + Sage loop, hardcoded DVA-C02, no persistence. Still in code but superseded. |
| Phase 2 | Shipped | SessionSubgraph (LangGraph), Postgres checkpointer, BullMQ infrastructure, Next.js → LangGraph proxy. |
| Phase 3 | Shipped | Onboarding, Blueprint Scout, Curriculum Builder, agent feed, dashboard, progress map. Curriculum is real, not hardcoded. |
| Phase 4 | Planned | Clerk auth, cross-device progress, user_id everywhere. |
| Phase 5 | Planned | PWA, mobile polish, Boss Battles, streaks, difficulty progression. |
| Phase 6 | Shipped | UX refinements: returning-user redirects, dashboard CTA states, Sage markdown rendering, theme toggle, 2-cycle default (ADR-0001). |
| Phase 7 | In progress (7.1–7.7 done, 7.8 next) | Exam artifacts, full DVA-C02 topic map, Rex coverage scheduler, Sage AWS-doc grounding + citations, content-quality eval harness. |
| Phase 8 | Planned | Vitest + pytest, smoke tests, CI. **No test runner is wired today.** |

The end-to-end happy path works today: `open app → onboarding → see agent feed → land on dashboard → start a 2-cycle session → see Rex's challenge, answer it, watch Sage stream back → get a summary → dashboard reflects your win/loss`. What's not done: real auth, PWA, any exam other than DVA-C02.

### V1 hard scope (don't drift)

- **DVA-C02 only.** SAA-C03 is the allowlisted second cert (7.8) but not yet shipped.
- **Anonymous browser user.** A UUID is generated client-side in `localStorage` and passed as `user_id` on every request. Clerk replaces this in Phase 4 — `user_id` is the only contract that has to stay stable.
- **2 cycles per session.** Hardcoded as `DEFAULT_CYCLES = 2` in `app/session/use-session.ts:10`. ADR-0001 explains why.
- **No Coach, Gap Tracker, Boss Battles, RAG, spaced repetition, notes.** Static summary screen stands in for Coach in MVP.

---

## 2. Quick start (10 minutes)

### Prerequisites

- **Node.js 20+** and **npm**
- **Python 3.10+** (3.11+ recommended; some installs use 3.12)
- **Docker / Docker Compose** for Postgres + Redis
- An **OpenRouter API key** (https://openrouter.ai). Get one before you start — every screen in the app depends on LLM calls.

### One-time setup

```bash
# 1. Clone and enter
git clone <repo>
cd cert-prep

# 2. Environment
cp .env.example .env.local
# Open .env.local and paste your key into OPENROUTER_API_KEY.
# The other defaults (DATABASE_URL, REDIS_URL, LANGGRAPH_URL) already match docker compose.

# 3. Start Postgres + Redis (both named "gauntlet", exposed on 5432 / 6379)
docker compose up -d
docker compose ps        # both should report "healthy" within ~5s

# 4. Install everything
npm install
cd agents && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
cd ..

# 5. Apply the DB migrations (idempotent; safe to re-run)
# Option A — via the API on first boot (recommended; the lifespan runs them):
#    skip this and let step 6 do it
# Option B — manually:
docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet < migrations/001_initial.sql
docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet < migrations/002_phase3_onboarding_curriculum.sql
docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet < migrations/003_phase7_exam_artifacts.sql
```

### Run the two services

In **two terminals**:

```bash
# Terminal 1 — Python LangGraph service (port 8000)
cd agents
source venv/bin/activate
python -m uvicorn main:app --reload

# Terminal 2 — Next.js (port 3000)
cd cert-prep
npm run dev
```

Open http://localhost:3000. The app should:
1. Detect no curriculum → show the home page.
2. Click **Start onboarding** → exam input defaults to `DVA-C02` → pick a learning style → **Build my plan**.
3. The agent feed runs Blueprint Scout → Curriculum Builder (5–15s).
4. Plan reveal → **Let's go** → dashboard with `0%` readiness.
5. **Start your first session** → Rex's first challenge streams in.
6. Type an answer, **Submit** → evaluation → Sage's explanation streams back with citations.
7. **Next challenge** → second cycle (harder) → Sage again → **View session summary** → score tally.

If you see the dashboard `0%` → close the tab → reopen `/session`: the checkpointer should restore your last in-progress session via the saved `thread_id` in `sessionStorage`.

### Sanity checks

```bash
# Health endpoint
curl -s http://localhost:8000/health | jq
# → { "status": "ok", "openrouter_configured": true, "database_configured": true }

# Migrations applied?
docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet -c '\dt'
# → expect: agent_feed_events, curricula, exam_artifacts, exchanges,
#           onboarding_runs, performance_aggregates, sessions,
#           plus langgraph checkpointer tables (checkpoints, checkpoint_writes, checkpoint_migrations, checkpoint_blobs)

# Lint the frontend
npm run lint

# Type-check the frontend (no script in package.json; do it manually)
npx tsc --noEmit
```

---

## 3. Repo layout

```
cert-prep/
├── app/                    # Next.js App Router
│   ├── api/                # HTTP routes — all thin proxies to the agents service
│   │   ├── session/        #   /start, /state, /submit, /next
│   │   ├── rex/            #   /challenge, /rechallenge (legacy Phase 1 paths, still wired)
│   │   ├── sage/           #   /sage (legacy Phase 1 SSE)
│   │   ├── evaluate/       #   /evaluate (legacy Phase 1 JSON)
│   │   ├── onboarding/     #   /start, /state, /feed (SSE proxy)
│   │   ├── dashboard/      #   /summary
│   │   └── progress/       #   /progress
│   ├── dashboard/          # /dashboard page
│   ├── onboarding/         # /onboarding page
│   ├── progress/           # /progress page
│   ├── session/            # /session page
│   ├── globals.css         # Tailwind v4 + design tokens (light/dark)
│   ├── layout.tsx          # Root layout, wraps ThemeProvider
│   └── page.tsx            # / (home) — redirects returning users to /dashboard
├── components/             # React UI
│   ├── dashboard/          #   dashboard-client.tsx, AppNav
│   ├── navigation/         #   app-nav.tsx, theme-toggle, theme-provider
│   ├── onboarding/         #   welcome/exam/style/plan/agent-feed steps
│   ├── progress/           #   progress-client.tsx
│   ├── session/            #   challenge-card, answer-form, sage-card, summary-screen, markdown-stream
│   └── ui/                 #   shadcn primitives (button, etc.)
├── lib/                    # Browser + server utilities
│   ├── openrouter.ts       # SSE client for OpenRouter (legacy Phase 1 path)
│   ├── openrouter-json.ts  # JSON client for OpenRouter (legacy Phase 1 path)
│   ├── sse-reader.ts       # Client-side SSE parser
│   ├── queue.ts            # BullMQ worker + queue (runs in Next.js process)
│   ├── anonymous-user.ts   # localStorage-backed user_id
│   ├── types.ts            # Shared domain types (Challenge, EvaluationResult, ...)
│   └── utils.ts            # cn() for classnames
├── agents/                 # Python LangGraph service
│   ├── main.py             # FastAPI entry; lifespan runs migrations + checkpointer setup
│   ├── state.py            # AppState TypedDict for the session graph
│   ├── db.py               # psycopg pool, AsyncPostgresSaver, migration runner
│   ├── llm.py              # Cached ChatOpenAI pointed at OpenRouter
│   ├── blueprint.py        # Sync read of DVA-C02 artifact (back-compat shim)
│   ├── blueprint_scout.py  # Async resolver: validate_exam_id → cache or file
│   ├── curriculum_repository.py  # Active curriculum, today-target, dashboard, progress
│   ├── curriculum_topics.py      # Coverage matrix, valid_domains
│   ├── curriculum_progress.py    # Performance aggregates, topic-level stats
│   ├── coverage_scheduler.py     # select_today_target / select_rechallenge_target
│   ├── onboarding_repository.py  # onboarding_runs, agent_feed_events
│   ├── performance_repository.py # performance_aggregates writes
│   ├── repositories.py           # sessions + exchanges CRUD
│   ├── sage_sources.py           # Citation grounding (exam-guide + curated service docs)
│   ├── data/
│   │   └── exam_artifacts/
│   │       └── dva-c02.json      # Hand-authored, source-of-truth blueprint
│   ├── exam_artifacts/           # Loader, validator, Postgres cache
│   ├── evals/                    # content-quality eval harness (issue 7.7)
│   ├── graphs/session.py         # SessionSubgraph definition
│   ├── nodes/                    # coach_open, rex_challenge, evaluate_answer, sage_respond, rex_rechallenge, coach_close
│   ├── prompts/                  # Rex, Sage, Evaluator, Curriculum Builder (Python ports)
│   ├── routes/                   # FastAPI routers: onboarding, session, jobs, dashboard
│   └── requirements.txt
├── migrations/             # Plain SQL; applied in lexical order on FastAPI boot
│   ├── 001_initial.sql
│   ├── 002_phase3_onboarding_curriculum.sql
│   └── 003_phase7_exam_artifacts.sql
├── docs/                   # Planning + architecture docs (this file lives here)
├── .env.example            # Copy → .env.local
├── docker-compose.yml      # Postgres + Redis
├── instrumentation.ts      # Next.js — boots lib/queue.ts in nodejs runtime
├── components.json         # shadcn config
├── eslint.config.mjs       # Flat config; next-vitals + next-ts
├── next.config.ts
├── tsconfig.json
└── package.json
```

### Where to look for what

| You want to … | Start here |
|---|---|
| Add a new screen | `app/<screen>/page.tsx` (route) + `app/<screen>/use-<screen>.ts` (state hook) + `components/<screen>/` (UI). Follow the pattern of `app/session/` and `app/onboarding/`. |
| Add a new API route | `app/api/<group>/<verb>/route.ts`. Most are thin proxies — they `fetch` the agents service and return. |
| Change a Rex / Sage prompt | `agents/prompts/rex.py` or `agents/prompts/sage.py` (Python — the source of truth). The `.ts` versions in `agents/prompts/` are only consumed by the legacy `/api/rex/*` and `/api/sage` paths. |
| Change the DVA-C02 blueprint | `agents/data/exam_artifacts/dva-c02.json` (the file is the source of truth; the `exam_artifacts` DB row is just a cache, reseeded on every boot). |
| Change the LangGraph graph | `agents/graphs/session.py`. Don't add abstractions — graph structure stays explicit. |
| Change session cycle count | `agents/state.py:initial_state` (`max_cycles: 2`) and `app/session/use-session.ts:10` (`DEFAULT_CYCLES = 2`). Keep them in sync. |
| Add a new background job | `lib/queue.ts` (queue + worker) and `agents/routes/jobs.py` (handler). The worker runs in the Next.js process — see §6. |
| Tweak the design system | `app/globals.css` (Tailwind v4 tokens, light + dark), `components/navigation/theme-provider.tsx`, `components/ui/`. |

---

## 4. Frontend tour (Next.js)

### Routing

`app/` follows the App Router. The five user-facing routes:

- `/` (`app/page.tsx`) — home. On mount, calls `/api/onboarding/state` and **server-side-equivalent redirect** to `/dashboard` if a curriculum exists, otherwise shows the marketing card.
- `/onboarding` (`app/onboarding/page.tsx`) — 5-step flow driven by `use-onboarding.ts`: `welcome → exam → style → feed → plan`.
- `/dashboard` (`app/dashboard/page.tsx`) — readiness score, today card, Rex's record, domain tiles.
- `/session` (`app/session/page.tsx`) — the Rex + Sage loop. Restores an in-progress session from `sessionStorage` on mount.
- `/progress` (`app/progress/page.tsx`) — full blueprint with per-topic coverage.

### Client state

The two big custom hooks do all the work:

- **`useSession`** (`app/session/use-session.ts`) — owns the session state machine: `phase` ∈ {`loading_challenge`, `ready`, `evaluating`, `streaming_sage`, `sage_done`, `loading_rechallenge`, `summary`, `error`}. Handles the 2-cycle loop, the `Retry` action (which replays the last action — `start`/`resume`/`submit`/`next`), and persistence of the `thread_id` to `sessionStorage` (cleared on success or explicit `restart`).
- **`useOnboarding`** (`app/onboarding/use-onboarding.ts`) — orchestrates the 5 steps. On mount, calls `/api/onboarding/state` to short-circuit to `/dashboard` for returning users, or resumes an in-progress onboarding run by reconnecting the SSE agent feed.

### Persistence primitives

- **`getAnonymousUserId`** (`lib/anonymous-user.ts`) — localStorage-backed UUID. Generated on first call, read on every subsequent call. SSR-safe (returns `""` on the server).
- **`loadThreadId` / `saveThreadId` / `clearThreadId`** (`app/session/session-persistence.ts`) — sessionStorage-backed LangGraph `thread_id`. Distinct from `localStorage` so closing the tab does not auto-restore a half-finished session.
- **`loadOnboardingId` / `saveOnboardingId`** (`app/onboarding/onboarding-persistence.ts`) — localStorage-backed `onboarding_id` so refreshing mid-onboarding doesn't lose the run.

### SSE plumbing

- **`streamOpenRouterResponse`** (`lib/openrouter.ts:36`) — server-side SSE client. Encodes OpenRouter's `data: {...}\n\n` stream into our `{type: "token"|"done"|"error"}` envelope. Used by legacy `/api/sage`.
- **`readSseStream`** (`lib/sse-reader.ts:12`) — client-side parser. Reads the response body and invokes a callback per event.
- **`readSessionStream`** (`app/session/session-stream.ts:15`) — session-aware dispatcher. Handles our extended envelope: `{type: "evaluation" | "citations" | "token" | "done" | "error"}` (the agents service emits `evaluation` and `citations` events in addition to the OpenRouter token stream).

### shadcn / styling

- `components.json` — shadcn config (`new-york` style, `neutral` base, lucide icons, `app/globals.css` for tokens).
- `app/globals.css` — Tailwind v4 with CSS variables for the design system. Both light and dark themes; `next-themes` toggles the `.dark` class on `<html>`.
- `components/ui/button.tsx` — the one shadcn primitive we have so far. Use `<Button>` (not raw `<button>`) for consistent focus rings, sizes, and 44×44 touch targets.

### Instrumentation

`instrumentation.ts` boots `lib/queue.ts` only in the Node.js runtime — that import side-effects a BullMQ `Worker` and a `QueueEvents` listener. This is how the Next.js process consumes the `agent-tasks` queue.

---

## 5. Backend tour (Python LangGraph service)

### Entry point

`agents/main.py` builds a FastAPI app. The `lifespan` context manager:

1. Validates `OPENROUTER_API_KEY` is set (raises if not — agents service refuses to start).
2. `init_pool()` — opens the async psycopg pool against `DATABASE_URL`.
3. `init_checkpointer()` — builds the `AsyncPostgresSaver` (or `InMemorySaver` if the pool is down).
4. `run_migrations()` — applies all `migrations/*.sql` in lexical order. **Idempotent** (every DDL uses `IF NOT EXISTS`).
5. `setup_checkpointer_tables()` — pre-creates the LangGraph checkpointer tables in autocommit mode. **This is a workaround** for a known bug in `langgraph-checkpoint-postgres==2.0.3`. See §11.
6. `ensure_seeded()` — upserts `agents/data/exam_artifacts/*.json` into the `exam_artifacts` table. Idempotent (skips rows whose `content_checksum` already matches).

Then four routers are mounted: `dashboard`, `jobs`, `onboarding`, `session`. The `GET /health` endpoint reports key presence.

### The session graph

`agents/graphs/session.py` is the LangGraph state machine. The 7 nodes are wired in this order:

```
START → coach_open → rex_challenge → evaluate_answer
                                       ↓ (conditional)
                            ┌──── sage_depth ────┐
                            │   (correct)         │
                            └─────────────────────┤
                            ┌──── sage_explain ───┤  (conditional)
                            │  (incorrect)        │  → rex_rechallenge | coach_close
                            └─────────────────────┘
rex_rechallenge → evaluate_answer (loop)
coach_close → END
```

Two conditional edges: **after evaluation** (correct vs. incorrect) and **after Sage** (more cycles vs. done). The compile call passes `interrupt_before=["evaluate_answer", "rex_rechallenge"]` — that's how the graph pauses for the user to type an answer.

State shape lives in `agents/state.py` (see ARCHITECTURE.md for the full list). One thing to internalize: `session_history` is `Annotated[list[Exchange], operator.add]`, so each Sage node **appends** an exchange rather than overwriting state.

### How a submit round-trips

1. Browser POSTs to `/api/session/submit` with `{thread_id, user_answer}`.
2. Next.js proxy (`app/api/session/submit/route.ts`) forwards to `agents/routes/session.py:submit_answer`.
3. The route calls `graph.aupdate_state(config, {"user_answer": ...})` to put the answer into the paused state, then iterates `graph.astream_events(None, ...)`.
4. It filters on `event["event"] == "on_chat_model_stream"` with `event["metadata"]["langgraph_node"]` ∈ {`sage_depth`, `sage_explain`} and emits SSE `token` events.
5. On `on_chain_end` for `evaluate_answer` it emits the `evaluation` event; for Sage nodes it emits the `citations` event (pulled from the last `session_history` entry); for the top-level `LangGraph` node it emits `done`.
6. The proxy returns the SSE body verbatim; the client parser dispatches tokens to the Sage card, the evaluation to the header badge, and the citations to the link list.

### Coverage scheduling

`agents/coverage_scheduler.py` is pure-Python (no LLM call) and answers "what should Rex challenge next?". Two entry points:

- `select_today_target` — ranks all (domain, topic) candidates using a tuple key `(topic_rank, domain_total - expected_attempts, topic_total, -weight, study_order, name)` where `topic_rank` is 0 (untouched) / 1 (mixed) / 2 (mastered). The smallest tuple wins.
- `select_rechallenge_target` — same domain, but prefers a different topic. Falls back through "weak or uncovered" within the same task statement, then within the domain, then within the same task statement again. Always returns `difficulty: "hard"`.

### Exam artifact store

`agents/data/exam_artifacts/<exam_id>.json` is the **source of truth**. The DB row in `exam_artifacts` is a cache. Three modules split the work:

- **`agents/exam_artifacts/loader.py`** — file reads, `content_checksum` (SHA-256 of raw bytes), and shape validation (`validate_artifact_shape`).
- **`agents/exam_artifacts/store.py`** — `ensure_seeded` upserts the JSON into Postgres on boot; `get_artifact` reads the row (falls through to `None` when the pool is down, so the loaders take over).
- **`agents/exam_artifacts/validate.py`** — `validate_exam_id(raw)` normalises input (lowercase, collapses whitespace, strips leading `aws `) and checks it against the set of `*.json` files. **Unknown codes are never silently coerced to a default** — the route surfaces the rejection to the user.

### Sage grounding & citations

`agents/sage_sources.py:load_sage_grounding(exam_id, topic_id, topic, services, source_ids)` builds a citation bundle for a topic:

1. Look for `agents/data/sage_snippets/<exam_id>/<topic_id>.md` (curated per-topic source overrides). If present, use it and its `Source:` lines as citations.
2. Otherwise, build citations from `source_ids` (turn `developer-associate-02-domain1.md#anchor` into the public `https://docs.aws.amazon.com/...` URL using the per-exam root in `EXAM_GUIDE_ROOTS`) and from `services` (each known service in `SERVICE_DOCS` adds a citation).
3. Dedupe, cap at 4 citations. If the result is empty, return a "no verified AWS source was found" marker so Sage's prompt injects the "Unverified explanation:" prefix.

The `SERVICE_DOCS` dict in this file is the curated list of AWS service doc URLs and one-sentence descriptions. Add to it when Rex starts generating challenges about services not in the list.

### The prompts

`agents/prompts/` has both `.ts` and `.py` versions of Rex, Sage, Evaluator. The **`.py` versions are the source of truth** — they're what `nodes/*.py` import. The `.ts` versions are only used by the legacy `/api/rex/*` and `/api/sage` endpoints and are kept for reference / future direct-from-frontend tests. Don't edit the `.ts` ones unless you're also editing the `.py` ones.

There's also `agents/prompts/curriculum_builder.py` for the Curriculum Builder. That one is Python-only.

---

## 6. End-to-end user flows

### Onboarding

```
Browser                                Next.js                                  Agents                                 Postgres / Redis
────────                                ────────                                  ──────                                 ───────────────
GET /                                                              
  → useEffect → /api/onboarding/state
  app/api/onboarding/state/route.ts                                
    → POST :8000/onboarding/state                                  
      agents/routes/onboarding.py:onboarding_state                 
        → get_latest_onboarding(user_id)                            
        → get_active_curriculum(user_id, dva-c02)                   
        ← { has_onboarding, run, curriculum }                      
      ← 200                                                         
    ← 200                                                           
  if curriculum exists → router.replace('/dashboard')              
                                                                    
<welcome> → <exam> → <style>                                         
  user clicks "Build my plan"                                      
  → POST /api/onboarding/start { user_id, exam_name, learning_style }
    app/api/onboarding/start/route.ts                              
      → POST :8000/onboarding/start                                 
        agents/routes/onboarding.py:start_onboarding                
          → validate_exam_id("DVA-C02")                             
          → create_onboarding_run(...) → onboarding_runs row        
          → add_feed_event(... Onboarding Agent complete ...)       
          ← { accepted: true, onboarding_id }                       
      ← 200                                                         
      → agentQueue.add("blueprint_scout", ...)                     
        lib/queue.ts:agentQueue (BullMQ)                           
          → Redis (LPUSH agent-tasks)                               
                                                                    
UI subscribes:                                                       
  EventSource('/api/onboarding/feed?onboarding_id=...')            
    app/api/onboarding/feed/route.ts                               
      → GET :8000/onboarding/<id>/feed                              
        agents/routes/onboarding.py:onboarding_feed                 
          → polls agent_feed_events (500ms)                         
          ← SSE: { agent, status, message }                         
                                                                    
[Next.js worker picks up the job from Redis]                        
  lib/queue.ts:agentWorker                                           
    → POST :8000/jobs/blueprint-scout { onboarding_id }             
      agents/routes/jobs.py:run_blueprint_scout                     
        → resolve_blueprint(exam_id) → BlueprintScoutResult         
        → save_blueprint(...)                                       
        → add_feed_event(... Blueprint Scout complete ...)         
    → agentQueue.add("curriculum_builder", ...)                    
                                                                    
[Next.js worker picks up next job]                                  
    → POST :8000/jobs/curriculum-builder                            
      agents/routes/jobs.py:run_curriculum_builder                  
        → build_curriculum(blueprint, learning_style)               
        → create_curriculum(...) → curricula row                    
        → complete_onboarding(...)                                  
        → add_feed_event(... Curriculum Builder complete ...)       
                                                                    
SSE emits "complete" → UI calls dashboardSummaryRequest             
  → /api/dashboard/summary                                           
  → :8000/dashboard/summary                                          
  → { readiness_score, today_domain, today_topic, ... }             
  → UI shows <PlanReveal> → click "Let's go" → /dashboard           
```

The key point: **the worker runs inside the Next.js process** (booted by `instrumentation.ts` → `lib/queue.ts`). The agents service is intentionally stateless across the two background jobs; it just receives `POST /jobs/...` from the worker.

### Session

```
Browser                                Next.js                                  Agents                                 Postgres
────────                                ────────                                  ──────                                 ───────────────
GET /session                                                          
  useSession mount:                                                   
    savedThreadId = loadThreadId() (sessionStorage)                  
    if savedThreadId:                                                 
      POST /api/session/state { thread_id }                          
        → :8000/session/state                                        
          → graph.aget_state(config)                                 
          ← { phase, cycle, max_cycles, challenge, ... }             
        apply snapshot to useSession state                           
    else:                                                             
      POST /api/session/start { user_id }                            
        → :8000/session/start                                        
          thread_id = uuid4()                                        
          → graph.ainvoke(initial_state, interrupt_before=...)       
          → aget_state → current_challenge                           
          ← { thread_id, challenge }                                
        saveThreadId(thread_id)                                      
                                                                    
[Browser shows ChallengeCard + AnswerForm]                            
user types → POST /api/session/submit { thread_id, user_answer }     
  → :8000/session/submit                                             
    → aupdate_state(config, { user_answer })                         
    → astream_events                                                 
      on 'on_chat_model_stream' for sage nodes → emit 'token'        
      on 'on_chain_end' for evaluate_answer → emit 'evaluation'       
      on 'on_chain_end' for sage nodes → emit 'citations'            
      on 'on_chain_end' for LangGraph → emit 'done'                  
    ← SSE stream                                                      
  ← SSE stream (proxied)                                              
  client readSessionStream → setSageText, setEvaluation, setCitations
                                                                    
[Browser shows SageCard with streaming text + citations + Next button]
user clicks Next → cycle < DEFAULT_CYCLES ?                          
  POST /api/session/next { thread_id }                               
    → :8000/session/next                                             
      → graph.ainvoke(None, config)                                  
      → aget_state → new current_challenge                           
    ← { challenge, cycle }                                           
                                                                    
[cycle 2 done → UI sets phase = "summary" → SummaryScreen]           
user clicks Restart → clearThreadId() → startSession()               
                                                                    
[On the agents side, sage_respond persists an exchanges row          
 in Postgres for every cycle, and coach_close stamps the session     
 ended_at and updates performance_aggregates.]                       
```

---

## 7. Key concepts

### Anonymous user → thread_id → checkpointer

- **Anonymous user** — `getAnonymousUserId()` in `lib/anonymous-user.ts` reads / writes a UUID under `localStorage["gauntlet.anonymous-user-id"]`. Server-side (SSR) it returns `""` and the API proxies always pass it through. When Phase 4 lands, this is the one place the Clerk `userId` plugs in.
- **Thread ID** — every session is a LangGraph thread, identified by a UUID generated server-side in `agents/routes/session.py:start_session`. The browser persists it in `sessionStorage["gauntlet.session.thread-id"]` (not localStorage) so the next tab doesn't auto-restore a half-finished session. It survives page reloads and intentional navigation away; it's cleared on `restart`.
- **Checkpointer** — `AsyncPostgresSaver` in `agents/db.py` writes the full graph state to Postgres on every node boundary. A `thread_id` lets you resume from any checkpoint. This is why a page reload mid-Sage still works.

### LangGraph interrupt pattern

The graph is compiled with `interrupt_before=["evaluate_answer", "rex_rechallenge"]` (`agents/graphs/session.py:109`). That means LangGraph runs the graph up to (but not into) those nodes, then pauses. To resume you either:

- **Call `aupdate_state` then `ainvoke(None, config)`** — used by `/session/submit` (write the user answer, then keep going) and `/session/next` (just resume after the Sage node finished).
- **Call `ainvoke(initial_state, config)`** — used by `/session/start` (fresh thread, no prior state).

`agents/routes/session.py:state` only does `aget_state` — never resumes. It returns the snapshot the browser needs to repaint, including the `_snapshot_phase` heuristic (no `next` nodes → "summary", `rex_rechallenge` queued → "sage_done", otherwise → "ready").

### Exam artifact model

The **blueprint is data, not code**. `agents/data/exam_artifacts/dva-c02.json` is a hand-authored, versioned JSON file. The shape is validated at boot by `validate_artifact_shape`. The DB row in `exam_artifacts` is a cache; the file is the source of truth. To add a new exam, drop a `saa-c03.json` next to `dva-c02.json` with the same shape and re-start the service.

The `source_ids` in each topic are page-relative paths to AWS-hosted exam-guide markdown (e.g., `developer-associate-02-domain1.md#developer-associate-02-domain1-task1`). The grounding layer in `agents/sage_sources.py` resolves them to public `https://docs.aws.amazon.com/` URLs.

### Curriculum / coverage scheduler

`agents/curriculum_repository.py:choose_today_target` returns a `{domain, topic, topic_id, task_statement_id, task_statement, services, source_ids, difficulty, curriculum_id}` for the next challenge. The scheduler (`agents/coverage_scheduler.py`) ranks every (domain, topic) candidate in the curriculum using a tuple key that prioritises (a) untouched topics, then (b) under-tried domains vs. their blueprint weight, then (c) untouched topics within the same weight, then (d) higher-weight domains, then (e) earlier study_order, then (f) name.

`choose_rechallenge_target` is similar but stays in the same domain and always returns `difficulty: "hard"`. It deliberately moves to a different topic (or a related uncovered topic in the same task statement) so a session never samples the same narrow area twice.

### Trust & audit (the "LLMs don't write the DB" rule)

LLM outputs are **never** written to the database directly. Every state mutation goes through application code:

- `evaluate_answer` parses the LLM JSON, asserts `outcome ∈ {correct, incorrect}`, and writes to `last_evaluation`. A bad LLM response raises.
- `rex_challenge` / `rex_rechallenge` parse the JSON, assert `domain/topic/scenario/question` are present, and write to `current_challenge`. A bad response raises.
- `sage_depth` / `sage_explain` assemble an exchange dict (with citations) and call `repositories.create_exchange`. They don't insert the Sage text raw — they wrap it.

This means a misbehaving LLM can't, e.g., fabricate exchange rows with fake outcomes or inject SQL.

---

## 8. LLM models & where they're called

| Agent | Model | Caller | File:line |
|---|---|---|---|
| Rex (challenge + rechallenge) | `anthropic/claude-sonnet-4.6` | `agents/nodes/rex_challenge.py:32`, `agents/nodes/rex_rechallenge.py:41` | Also legacy `app/api/rex/*` if you go direct. |
| Sage (depth + explain) | `anthropic/claude-sonnet-4.6` | `agents/nodes/sage_respond.py:58` (via `llm.get_llm`) | Legacy `app/api/sage`. |
| Evaluator | `anthropic/claude-sonnet-4.6` | `agents/nodes/evaluate_answer.py:38` | Legacy `app/api/evaluate`. |
| Curriculum Builder | `anthropic/claude-sonnet-4.6` | `agents/curriculum_repository.py:48` (via `prompts.curriculum_builder`) | |
| Content-quality eval (live mode) | `anthropic/claude-sonnet-4.6` | `agents/evals/content_quality.py:120` | |

**Do not swap Rex or Sage models without an A/B test.** They're product-critical — see the guardrail in AGENTS.md and the cost table in `docs/tech-stack.md`. If you must change, edit the `MODEL` constant at the top of the relevant prompt file (`agents/prompts/rex.py:3`, `agents/prompts/sage.py:9`, `agents/prompts/evaluator.py:8`, `agents/prompts/curriculum_builder.py:5`).

All LLM calls go through `agents/llm.py:get_llm(model)` which lazily creates a `ChatOpenAI` pointed at `https://openrouter.ai/api/v1` and caches per model. `lib/openrouter.ts` and `lib/openrouter-json.ts` are the legacy Phase 1 direct callers — they hit the same OpenRouter endpoint from the Next.js process.

Estimated per-session cost is ~$0.054 — Rex and Sage account for ~98% of it. See `docs/tech-stack.md` for the full cost table.

---

## 9. Conventions & hard rules

These are enforced (or expected to be enforced) by the codebase, lint, and AGENTS.md. If you're about to break one, stop and check.

### From AGENTS.md

- **No code file may exceed 200 lines.** Split before continuing if you approach the limit. The only known violation today is `lib/openrouter.ts` (266 lines) — fix it before adding more code there.
- **Commit every change immediately after it is made.** Don't batch unrelated edits into one commit.
- **No CI workflows, no test runner, no `pyproject.toml`.** Don't add them without an explicit ask. (Phase 8 is the planned landing pad.)
- **DVA-C02 only.** Don't generalise to a second exam, second user model, or any other phase-bait. Phase 7.8 is the allowlist gate.
- **No Clerk auth before Phase 4.** All `user_id`s are the anonymous UUID today.
- **No Boss Battles, Coach agent, Gap Tracker, RAG, spaced repetition, notes feature** in V1.
- **LangGraph graph stays explicit** — no abstractions hiding the node/edge definitions. The user is learning LangGraph deeply.
- **The `agents/main.py` `lifespan` runs migrations + checkpointer setup on every boot.** Don't move them out.
- **Never read or echo secrets** (`.env.local`, `*.pem`, `*.key`, `.aws/`, etc.).

### From the code

- **The 2-cycle session length is locked at `DEFAULT_CYCLES = 2`** (`app/session/use-session.ts:10`) and `max_cycles: 2` in `agents/state.py:initial_state`. Bumping either is a 1-line change but is gated on ADR-0001 re-evaluation (engagement vs. signal).
- **`pending_user_answers` was removed in 2.6** — the graph now uses LangGraph interrupts to wait for the real user. Don't re-add it.
- **LLM outputs are wrapped in `_strip_code_fences` before `JSON.parse`** in both `lib/openrouter-json.ts:72` and every Python node that parses LLM output (`nodes/*.py`). Don't skip this — Rex and Sage occasionally wrap JSON in ```json``` fences.
- **Migrations are plain SQL, idempotent, and applied in lexical order** by `run_migrations()`. Add a new file (`004_*.sql`) — don't edit the existing ones.
- **Background jobs go through BullMQ** (`lib/queue.ts`). Don't `fetch` from inside a node — use the queue so failures are retried.
- **Citations come from `agents/sage_sources.py`, not from the prompt.** The prompt tells Sage *to* cite; the `exchanges.citations` JSONB column is populated by application code that loads the citation bundle, not by the LLM.

### Style

- **TypeScript:** strict mode (`tsconfig.json:7`); use `type` not `interface` for shape-only types; prefer `as` assertions only at HTTP boundaries; no `any` unless there's a real reason (then comment why).
- **Python:** typed throughout; `from __future__ import annotations` at the top of every module; `async def` only when actually awaiting something; `logger = logging.getLogger(__name__)` per module; never `print()`.
- **Frontend components:** `"use client"` at the top of any file that uses hooks; server components by default in `app/`.
- **Styling:** Tailwind v4 utility classes with the design tokens from `app/globals.css`. Use `<Button>` from `components/ui/`, not raw `<button>`, so focus rings and 44×44 touch targets stay consistent. Every interactive control on mobile should hit 44×44 minimum.

---

## 10. Recipes: how to add a new feature

### Add a new screen

1. Create `app/<screen>/page.tsx` with `"use client"` and a hook import.
2. Create `app/<screen>/use-<screen>.ts` for state, mirroring the pattern in `app/session/use-session.ts` (single state object + named actions).
3. Create `app/<screen>/<screen>-api.ts` for `fetch` wrappers and `app/<screen>/<screen>-persistence.ts` for any localStorage / sessionStorage keys.
4. Create `components/<screen>/` with one file per visual component.
5. Add a route to `components/navigation/app-nav.tsx` if it should be in the bottom nav / sidebar.
6. If the screen needs a new API proxy, create `app/api/<group>/<verb>/route.ts` and a corresponding `agents/routes/<group>.py` router.

### Add a new LangGraph node

1. Write the node function in `agents/nodes/<name>.py`. It takes `state: AppState` and returns a `dict` (the state delta). For LLM calls, use `llm.get_llm(MODEL)`. For DB writes, use the existing `repositories.py` helpers or a new one.
2. Add the node to `agents/graphs/session.py:build_session_graph` with `graph.add_node("name", node_fn)`.
3. Wire the edges. Use `add_conditional_edges` if there's a routing decision. Pass the routing function as the second arg, with a third arg being the literal `{"label": "node_name"}` mapping.
4. If the node should pause for the user, add it to the `interrupt_before` list in `compile(...)`.
5. Make sure the state field it returns is in `agents/state.py:AppState` and is mergeable (use `Annotated[list[X], operator.add]` for collections you want to grow).

### Add a new exam

1. Author `agents/data/exam_artifacts/<exam_id>.json` with the shape documented in `agents/exam_artifacts/loader.py:_REQUIRED_TOP_LEVEL` and `_REQUIRED_DOMAIN` and `_REQUIRED_TOPIC`. Sum of `domain.weight` must equal 100.
2. Add an entry to `EXAM_GUIDE_ROOTS` in `agents/sage_sources.py:19` (key = `exam_id`, value = the public docs.aws.amazon.com root).
3. Add the AWS services you'll need to `SERVICE_DOCS` in the same file.
4. Restart the agents service. The `ensure_seeded` lifespan call will validate the shape, refuse to seed if invalid, and otherwise upsert the row. Check the log for `Seeded N exam artifact(s) into the DB cache.`.
5. Add the code to `components/onboarding/exam-step.tsx:29-32`'s `<datalist>` so the autocomplete picks it up.
6. Update `agents/prompts/curriculum_builder.py` if the new exam's blueprint has fewer/more domains (currently hardcoded to 4 — parameterise it).

### Add a new background job

1. Add the handler in `agents/routes/jobs.py` (POST endpoint that takes a `JobRequest` and does the work).
2. Add the worker case in `lib/queue.ts:agentWorker.process` (an `if (job.name === "...")` branch that calls the new endpoint with `runBackendJob`).
3. If this job is the start of a chain, use `agentQueue.add(...)` inside the worker — same pattern as `blueprint_scout` → `curriculum_builder`.
4. Make sure the UI subscribes to feed events (the agent feed SSE already includes whatever you write to `agent_feed_events`).

### Add a new agent prompt

1. Add `agents/prompts/<agent>.py` with a `MODEL` constant, a `build_<verb>_prompt(input)` function returning `(system, user)`, and any dataclasses for input shape.
2. Use it from the relevant node (`agents/nodes/<name>.py`).
3. If the prompt is also used from the frontend (legacy), mirror it in `agents/prompts/<agent>.ts`. Otherwise skip.

---

## 11. How to debug

### Logging

- **Next.js** — `console.log` / `console.error`. The dev server prints to the terminal that ran `npm run dev`. Notable call sites: `[evaluate] Result: ...` (dev-only), `[rex/challenge] Generated: ...` (dev-only), `console.error("[sage] OpenRouter error:", ...)` on every OpenRouter failure.
- **Python** — `logger = logging.getLogger(__name__)` per module. The lifespan in `agents/main.py` configures Python's logging; uvicorn's `--reload` keeps logs in the terminal that ran `python -m uvicorn main:app --reload`. Tail the `agents/uvicorn.log` file if you started it detached.
- **BullMQ** — `[JobQueue] ...` lines. Connection errors and failed jobs both log here.
- **Postgres** — `docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet` for ad-hoc queries. `\dt` lists tables; `SELECT * FROM exchanges ORDER BY created_at DESC LIMIT 5;` to spot-check.

### The two big gotchas

**1. `langgraph-checkpoint-postgres==2.0.3`'s `AsyncPostgresSaver.setup()` is broken on a fresh DB.**

Symptom: `agents/main.py` lifespan raises `UndefinedTable` from the version-probe SELECT, then `InFailedSqlTransaction` from the subsequent CREATE TABLE statements. The service still starts (we swallow the exception and log it) but the checkpointer is in an inconsistent state.

Why: the library runs the SELECT in the same transaction as the migrations. On a fresh DB the SELECT aborts the transaction before the migrations can run.

Fix in place: `agents/db.py:setup_checkpointer_tables` pre-creates the four checkpointer tables in autocommit mode, registers the latest version in `checkpoint_migrations`, and then `setup()` is a no-op. **Do not** "simplify" this back to a plain `await checkpointer.setup()`.

**2. `lib/openrouter.ts` is 266 lines and violates the 200-line hard rule.**

It works fine, but you can't add anything more to it. If you need to add an OpenRouter feature (e.g. tool calls, JSON schema mode), split the file first — extract the SSE encoding helpers and the error wrapper into their own modules.

### Other common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: DATABASE_URL is not set` on agents service boot | `.env.local` missing or empty | Copy from `.env.example` and re-source. |
| `RuntimeError: OPENROUTER_API_KEY is not set` | Same | Same. |
| Dashboard says "Dashboard is waiting for the agent service" | Agents service not running, or crashed | Check the uvicorn terminal; `curl http://localhost:8000/health`. |
| Onboarding feed hangs on "Waiting for signal…" | BullMQ worker not running | The Next.js process must be running (`npm run dev`); `instrumentation.ts` boots the worker. |
| Onboarding feed shows "Blueprint Scout rejected this exam" | Exam code not in the allowlist | Only `DVA-C02` is seeded today. The error message names the supported codes. |
| Sage streams but `citations` panel never appears | Either checkpointer isn't writing or `load_sage_grounding` returned empty | Check `agents/data/sage_snippets/<exam_id>/` and `SERVICE_DOCS`. |
| `TypeError: Cannot read properties of null (reading 'domain')` in browser | The server returned an error shape, not a Challenge | Check the network tab for the actual 4xx/5xx; look at the relevant `/api/session/*` route. |
| Theme flashes on reload (FOUC) | `next-themes` `<ThemeProvider>` not wrapping the layout, or `suppressHydrationWarning` missing on `<html>` | Both are in `app/layout.tsx`; check they haven't been edited. |

### Inspecting the database

```bash
docker exec -it cert-prep-postgres-1 psql -U gauntlet -d gauntlet

# Inside psql:
\dt                                  -- list tables
\du                                  -- nothing custom, default user
\d sessions                          -- show sessions schema
\d exchanges                         -- show exchanges schema

SELECT * FROM exam_artifacts;        -- what's seeded
SELECT * FROM curricula LIMIT 5;     -- your curriculum (if you've onboarded)
SELECT * FROM sessions ORDER BY started_at DESC LIMIT 5;
SELECT cycle, topic, outcome, left(sage_response, 80) FROM exchanges ORDER BY created_at DESC LIMIT 10;
SELECT * FROM performance_aggregates;
SELECT * FROM agent_feed_events ORDER BY id DESC LIMIT 20;
```

The LangGraph checkpointer tables (`checkpoints`, `checkpoint_writes`, `checkpoint_migrations`, `checkpoint_blobs`) are managed by the library; the human-readable view is `checkpoints` (one row per node boundary, keyed by `thread_id`).

### Resetting state

```bash
# Wipe everything (DESTRUCTIVE — drops the gauntlet DB)
docker compose down -v
docker compose up -d

# Just clear application tables
docker exec -i cert-prep-postgres-1 psql -U gauntlet -d gauntlet -c "
  TRUNCATE exchanges, sessions, curricula, onboarding_runs,
           agent_feed_events, performance_aggregates, exam_artifacts
          RESTART IDENTITY CASCADE;
  DELETE FROM checkpoints; DELETE FROM checkpoint_writes;
  DELETE FROM checkpoint_migrations; DELETE FROM checkpoint_blobs;
"

# Clear just your browser state
# In DevTools: Application → Local Storage → delete gauntlet.anonymous-user-id
#              Application → Session Storage → delete gauntlet.session.thread-id
#              Application → Local Storage → delete gauntlet.onboarding-id
```

### The eval harness (7.7)

```bash
# From agents/, with venv active:
python -m evals.content_quality --exam-id dva-c02           # mock mode (no LLM calls)
python -m evals.content_quality --exam-id dva-c02 --mode live
python -m evals.content_quality --exam-id dva-c02 --max-topics 5

# Reports land in agents/reports/evals/<run_id>-<exam_id>-content-quality.{json,md}
```

The mock mode generates a deterministic placeholder challenge for each (domain, topic) and exercises the grounding / citation / shape / leakage / duplicate checks against the real artifact. Live mode swaps in `llm.get_llm(MODEL).invoke(...)` for Rex.

---

## 12. Glossary

- **Anonymous user** — A UUID generated in `localStorage` by `lib/anonymous-user.ts`. Used as `user_id` everywhere. Replaced by Clerk `userId` in Phase 4.
- **Blueprint** — A structured representation of a certification's exam guide: domains, weights, task statements, topics, services, source IDs. Authored as JSON in `agents/data/exam_artifacts/<exam_id>.json`. Cached in the `exam_artifacts` DB table.
- **BullMQ** — Redis-backed job queue used for the Blueprint Scout and Curriculum Builder background jobs. The worker runs in the Next.js process (`lib/queue.ts`).
- **Checkpointer** — The LangGraph component that persists full graph state at every node boundary. `AsyncPostgresSaver` in this app.
- **Citation** — A `{url, title, snippet_id}` triple attached to a Sage exchange. Resolved by `agents/sage_sources.py` from `source_ids` and known AWS service doc URLs.
- **Conditional edge** — A LangGraph routing decision between nodes. The session graph has two: `evaluate → sage_depth | sage_explain` and `sage → rex_rechallenge | coach_close`.
- **Cycle** — One Rex → evaluate → Sage round in a session. A session is 2 cycles by default.
- **Exchange** — A persisted record of one cycle: challenge, user answer, outcome, Sage response, citations. Stored in the `exchanges` table.
- **Interrupt** — A LangGraph pause point. The session graph uses `interrupt_before=["evaluate_answer", "rex_rechallenge"]` to wait for the user to type.
- **Rex** — The challenger agent. Generates scenario-based challenges for a (domain, topic, difficulty) target.
- **Sage** — The tutor agent. Two paths: `sage_depth` (after correct) and `sage_explain` (after incorrect). Streams explanations with citations.
- **Source IDs** — Page-relative pointers in the AWS exam guide (e.g., `developer-associate-02-domain1.md#anchor`). Resolved to public docs.aws.amazon.com URLs by Sage grounding.
- **Task statement** — A row in the official AWS exam guide. Each `topic` in a blueprint references exactly one `task_statement_id`.
- **Thread ID** — A UUID that identifies a session to the LangGraph checkpointer. Generated server-side, persisted in client `sessionStorage` under `gauntlet.session.thread-id`.
- **Topic** — A skill the blueprint tests (e.g., `1.2.3 Lambda event lifecycle and error handling`). The unit at which coverage is tracked.
