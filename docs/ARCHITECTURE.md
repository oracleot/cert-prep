# Architecture

The system-level deep dive for **Gauntlet**. Read this when you need to understand *why* the code is shaped the way it is, *what the contracts are* between services, or *what changes when* you add a feature.

For the day-to-day onboarding, setup, and recipes, see [`docs/DEVELOPER_GUIDE.md`](./DEVELOPER_GUIDE.md). For the planning rationale and phase history, see [`docs/tracker.md`](./tracker.md), [`docs/tech-stack.md`](./tech-stack.md), [`docs/system-design.md`](./system-design.md), and [`docs/implementation-backlog.md`](./implementation-backlog.md).

---

## 1. System overview

Gauntlet is a three-process system:

1. **Next.js** (TypeScript, App Router, port 3000) — UI, SSE streaming, session orchestration on the client, BullMQ worker.
2. **Python LangGraph service** (FastAPI + uvicorn, port 8000) — agent runtime, Postgres checkpointer, exam-artifact store, background-job HTTP handlers.
3. **Postgres + Redis** (Docker Compose, ports 5432 / 6379) — application state + LangGraph checkpointer tables in Postgres, BullMQ queues in Redis.

The Next.js process and the Python service are **separate deployables** that communicate only over HTTP. There is no shared module, no shared process, no shared runtime. The browser talks to Next.js `/api/*`; Next.js proxies the production agent requests to Python.

```
                          ┌────────────────────────────────────┐
                          │            Browser                 │
                          │  Next.js (client components)       │
                          │  - anonymous user (localStorage)   │
                          │  - session thread (sessionStorage) │
                          │  - SSE consumer (lib/sse-reader)   │
                          └─────┬──────────────────────┬───────┘
                                │ fetch + SSE
                                ▼
            ┌──────────────────────────────┐   ┌──────────────────────────┐
            │  Next.js server              │   │  Python LangGraph        │
            │  (App Router, nodejs)        │   │  service (uvicorn :8000) │
            │  - /api/* thin proxies       │   │  - LangGraph state graph │
            │  - BullMQ Worker (lib/queue)  │──▶│  - Exam artifact store   │
            │  - OpenRouter client (legacy)│   │  - Background job HTTP   │
            │                              │   │  - OpenRouter (via LC)   │
            └──────────────┬───────────────┘   └──────────┬───────────────┘
                           │                                │
                           ▼                                ▼
                  ┌─────────────────┐            ┌──────────────────┐
                  │  Redis (BullMQ) │            │  Postgres        │
                  │  agent-tasks Q  │            │  - sessions      │
                  └─────────────────┘            │  - exchanges    │
                                                  │  - curricula    │
                                                  │  - exam_artifacts│
                                                  │  - onboarding_runs│
                                                  │  - agent_feed_events│
                                                  │  - performance_*
                                                  │  - LangGraph checkpointer tables│
                                                  └──────────────────┘
```

### Architectural posture

A **modular monolith headed toward service separation**, not a microservices stack. Today everything is one Next.js app and one Python service, and the boundary between them is "thin HTTP proxy vs. domain logic". This is a deliberate trade:

- The user is solo, learning the stack, and needs to ship fast.
- Microservices overhead is not justified at V1.
- Service separation happens only when a boundary becomes genuinely painful.

The Next.js ↔ Python split exists because **LangGraph + the Python LLM SDK ecosystem** are non-negotiable for the user (they want to learn LangGraph deeply). The browser ↔ server split within Next.js is just standard App Router.

### The one-way doors (locked in)

From `docs/tech-stack.md`:

- **LangGraph as orchestration layer** — state typing, checkpointer, and graph structure are deeply coupled by Phase 2. Migration = rewrite of the entire agent layer.
- **Postgres as primary DB** — the LangGraph checkpointer is Postgres-coupled. Swapping DB means replacing the checkpointer.
- **Card-based session UI** — the product's UX identity. A pivot to chat/quiz = product redesign, not refactor.
- **SSE for streaming** — switching to WebSockets mid-build requires changes on both server and client.

---

## 2. Service topology

### Next.js (port 3000)

Single Next.js 16 App Router project. Server components by default; `"use client"` only on the four screens (`/`, `/onboarding`, `/dashboard`, `/session`, `/progress`) and the two hooks (`useSession`, `useOnboarding`).

The Node.js server runtime runs:

- **API routes** (`app/api/*/route.ts`) — thin proxies to the Python service, plus the legacy Phase 1 direct-OpenRouter endpoints (`/api/rex/challenge`, `/api/rex/rechallenge`, `/api/evaluate`, `/api/sage`).
- **The BullMQ worker** (`lib/queue.ts`) — booted in the Node.js runtime by `instrumentation.ts` at server start. Processes `agent-tasks` jobs, calling `POST :8000/jobs/blueprint-scout` and `POST :8000/jobs/curriculum-builder`.

`instrumentation.ts` is the seam: it conditionally imports `./lib/queue` only when `NEXT_RUNTIME === "nodejs"`. The worker is **not** a separate process — it's a long-lived Worker inside the Next.js server, wired in for Phase 3.

### Python LangGraph service (port 8000)

Single FastAPI app (`agents/main.py`). Four routers:

- `agents/routes/onboarding.py` — `POST /onboarding/start`, `POST /onboarding/state`, `GET /onboarding/{id}/feed` (SSE).
- `agents/routes/session.py` — `POST /session/start`, `POST /session/submit` (SSE), `POST /session/state`, `POST /session/next`.
- `agents/routes/jobs.py` — `POST /jobs/blueprint-scout`, `POST /jobs/curriculum-builder`. Called by the Next.js BullMQ worker.
- `agents/routes/dashboard.py` — `POST /dashboard/summary`, `POST /progress`.

Plus `GET /health` (mounted on the app directly) which returns `{status, openrouter_configured, database_configured}`.

### Postgres + Redis

`docker-compose.yml` runs `postgres:16-alpine` and `redis:7-alpine`. Both have healthchecks for local operator visibility; the host-run agents service and Next.js worker do not block startup on Compose health.

- **Postgres** holds application state (sessions, exchanges, curricula, onboarding runs, agent feed events, performance aggregates, exam artifacts) **and** the LangGraph checkpointer tables. One database, one pool.
- **Redis** holds the BullMQ queue and events. The `agent-tasks` queue is the only queue.

---

## 3. Frontend architecture

### Rendering model

App Router with `"use client"` on every interactive screen. Server components are intentionally not used for screens that need state or effects.

| Route | Component | Hook | API calls |
|---|---|---|---|
| `/` | `app/page.tsx` | inline `useEffect` | `POST /api/onboarding/state` (server check, then redirect) |
| `/onboarding` | `app/onboarding/page.tsx` | `useOnboarding` | `POST /api/onboarding/state` (resume check), `POST /api/onboarding/start` (submit), `GET /api/onboarding/feed` (SSE), `POST /api/dashboard/summary` (after complete) |
| `/dashboard` | `app/dashboard/page.tsx` → `DashboardClient` | inline | `POST /api/dashboard/summary` |
| `/session` | `app/session/page.tsx` | `useSession` | `POST /api/session/start`, `POST /api/session/state`, `POST /api/session/submit` (SSE), `POST /api/session/next` |
| `/progress` | `app/progress/page.tsx` → `ProgressClient` | inline | `POST /api/progress` |

### State management

Two custom hooks own almost all interactive state. The pattern is:

1. **One state object** with `useState` for the discriminated `phase` and a handful of typed fields.
2. **A `lastActionRef`** that remembers the last action the user triggered. Used by `retry` to replay the action that failed.
3. **`sessionStorage` for the in-progress session** so a page reload can resume.

There's no Redux, Zustand, or React Query. The state is small enough that the hooks handle it directly.

### Streaming

- **OpenRouter SSE client** (`lib/openrouter.ts`) — converts OpenRouter's `data: {...}\n\n` chunks into our `{type: "token"|"done"|"error"}` envelope. Used by legacy `/api/sage`.
- **OpenRouter JSON client** (`lib/openrouter-json.ts`) — non-streaming; strips markdown code fences before `JSON.parse`. Used by legacy `/api/rex/*` and `/api/evaluate`.
- **SSE reader** (`lib/sse-reader.ts`) — client-side. Parses the envelope and dispatches to a callback.
- **Session SSE dispatcher** (`app/session/session-stream.ts`) — extends the envelope to include `evaluation` and `citations` events (emitted by the agents service's `/session/submit` SSE stream).

The browser never reads from OpenRouter directly. The agents service is the only thing that talks to OpenRouter from the runtime. The legacy `/api/sage` route goes OpenRouter → Next.js → browser, but the production path goes OpenRouter → agents service → Next.js → browser.

### Theming

`next-themes` with `attribute="class"`, `defaultTheme="system"`, `enableSystem`. The provider is mounted in `app/layout.tsx`; the toggle is in `components/navigation/theme-toggle.tsx`. The design tokens are CSS variables in `app/globals.css` (light + `.dark` blocks) wired into Tailwind v4 via `@theme inline`.

`<html lang="en" suppressHydrationWarning>` is the FOUC prevention — `next-themes` writes the `class` attribute before React hydrates, and the warning is suppressed to silence the expected mismatch.

### Anonymous user identity

A single helper, `lib/anonymous-user.ts:getAnonymousUserId()`, generates (and persists) a UUID in `localStorage["gauntlet.anonymous-user-id"]` on first call. SSR returns `""`; client returns the UUID. Every API proxy in `app/api/*` reads this and includes it in the request body as `user_id`.

This is the one contract that has to stay stable through Phase 4: `user_id` is a string, opaque to the server, sourced from localStorage today and from Clerk `userId` tomorrow. Server code never inspects it.

---

## 4. Backend architecture

### FastAPI structure

```
agents/
├── main.py              # FastAPI app, lifespan, /health
├── db.py                # pool, checkpointer, migrations
├── state.py             # AppState TypedDict
├── llm.py               # ChatOpenAI singleton (OpenRouter)
├── blueprint.py         # Sync read of DVA-C02 artifact (shim)
├── blueprint_scout.py   # Async resolver
├── curriculum_repository.py  # active curriculum, today target, dashboard
├── curriculum_topics.py      # coverage matrix
├── curriculum_progress.py    # aggregates
├── coverage_scheduler.py     # target selection
├── onboarding_repository.py  # onboarding_runs, agent_feed_events
├── performance_repository.py # performance_aggregates writes
├── repositories.py           # sessions + exchanges CRUD
├── sage_sources.py           # citation grounding
├── data/exam_artifacts/      # source-of-truth JSON
├── exam_artifacts/           # loader, store, validator
├── evals/                    # content-quality harness
├── graphs/session.py         # SessionSubgraph
├── nodes/                    # 7 nodes
├── prompts/                  # .py and (legacy) .ts
└── routes/                   # 4 FastAPI routers
```

Module-level singletons live in `db.py` (`_pool`, `_checkpointer`) and `llm.py` (`_default_llm`). Both are initialised by the lifespan and reset on shutdown.

### Lifespan & boot sequence

`agents/main.py:lifespan` runs in this order:

1. `_required_env("OPENROUTER_API_KEY")` — raises `RuntimeError` if missing. The service refuses to start.
2. `init_pool()` — opens the async psycopg pool against `DATABASE_URL`. If `DATABASE_URL` is unset, sets `_pool = None` and logs a warning. The rest of the service keeps working with no persistence.
3. `init_checkpointer()` — returns `AsyncPostgresSaver(get_pool())` if the pool is up, else `InMemorySaver()`. `InMemorySaver` is dev-only — state doesn't survive a restart.
4. `run_migrations()` — runs every `migrations/*.sql` file in lexical order. **Idempotent** (every DDL uses `IF NOT EXISTS`).
5. `setup_checkpointer_tables()` — pre-creates the four LangGraph checkpointer tables in **autocommit mode**, registers the latest version in `checkpoint_migrations`, and lets the library's `setup()` be a no-op. This is a workaround for a known bug in `langgraph-checkpoint-postgres==2.0.3` whose first SELECT aborts the transaction before the migrations can run.
6. `ensure_seeded()` — upserts `agents/data/exam_artifacts/*.json` into the `exam_artifacts` table. Idempotent: skips rows whose `content_checksum` already matches.

If 4 or 5 fails, the service logs and continues with degraded persistence. The boot is **non-blocking on DB errors** by design — the dev experience is "agents service runs even if Postgres is down" (it just falls back to `InMemorySaver`).

### Router layout

```
POST /onboarding/start       → validate_exam_id → create_onboarding_run → add_feed_event
POST /onboarding/state       → get_latest_onboarding + get_active_curriculum
GET  /onboarding/{id}/feed   → SSE poll of agent_feed_events
POST /session/start          → new thread, run graph to first interrupt
POST /session/submit         → write user_answer, astream_events, emit SSE
POST /session/state          → aget_state only (no resume)
POST /session/next           → resume after Sage, return next challenge
POST /jobs/blueprint-scout   → called by Next.js BullMQ worker
POST /jobs/curriculum-builder → called by Next.js BullMQ worker
POST /dashboard/summary      → dashboard_summary()
POST /progress               → progress_map()
GET  /health                 → env presence
```

---

## 5. Data model

### Application tables

All in the default `public` schema. Every table uses `IF NOT EXISTS` in migrations, so migrations are re-runnable.

#### `sessions` (migration 001 + 002)

| column | type | notes |
|---|---|---|
| `id` | UUID PK | `gen_random_uuid()` default |
| `user_id` | TEXT | The anonymous UUID today; Clerk `userId` in Phase 4 |
| `exam_id` | TEXT | e.g. `dva-c02` |
| `domain` | TEXT | Resolved by `coach_open` |
| `topic` | TEXT | Resolved by `coach_open` (added in 002) |
| `curriculum_id` | UUID FK → `curricula(id)`, NULL on `SET NULL` (added in 002) |
| `started_at` | TIMESTAMPTZ | default `NOW()` |
| `ended_at` | TIMESTAMPTZ | stamped by `coach_close` |

Index: `sessions_user_id_idx(user_id)`, `sessions_curriculum_id_idx(curriculum_id)`.

Written by: `repositories.create_session` (in `coach_open`); `repositories.close_session` (in `coach_close`).

#### `exchanges` (migration 001 + 003)

| column | type | notes |
|---|---|---|
| `id` | UUID PK | |
| `session_id` | UUID FK → `sessions(id) ON DELETE CASCADE` | |
| `cycle` | INTEGER | 1-indexed within the session |
| `domain` | TEXT | |
| `topic` | TEXT | |
| `challenge` | JSONB | Full `Challenge` object |
| `user_answer` | TEXT | |
| `outcome` | TEXT | `correct` or `incorrect` (CHECK constraint) |
| `sage_response` | TEXT | Streamed text concatenated |
| `citations` | JSONB | Default `'[]'::jsonb` (added in 003); array of `{url, title, snippet_id}` |
| `created_at` | TIMESTAMPTZ | default `NOW()` |

Index: `exchanges_session_id_idx(session_id)`.

Written by: `repositories.create_exchange` (in `sage_depth` / `sage_explain`).

#### `onboarding_runs` (migration 002)

| column | type | notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | TEXT | |
| `exam_id` | TEXT | |
| `exam_name` | TEXT | Canonical name from the artifact |
| `learning_style` | TEXT | `pressure_drills` / `guided_explanations` / `mixed_review` |
| `status` | TEXT | `intake` → `blueprint_running` → `blueprint_complete` → `curriculum_running` → `complete` / `failed` |
| `step` | TEXT | `exam_input` → `agent_feed` → `plan_reveal` |
| `blueprint` | JSONB | Saved by Blueprint Scout |
| `curriculum_id` | UUID FK → `curricula(id)` (no FK declared — left nullable) | Set when Curriculum Builder finishes |
| `created_at`, `updated_at` | TIMESTAMPTZ | |
| `completed_at` | TIMESTAMPTZ | |

Index: `onboarding_runs_user_id_idx(user_id, created_at DESC)`.

#### `agent_feed_events` (migration 002)

| column | type | notes |
|---|---|---|
| `id` | BIGSERIAL PK | |
| `onboarding_run_id` | UUID FK → `onboarding_runs(id) ON DELETE CASCADE` | |
| `agent` | TEXT | `Onboarding Agent` / `Blueprint Scout` / `Curriculum Builder` |
| `status` | TEXT | `running` / `complete` / `failed` (CHECK) |
| `message` | TEXT | Human-readable |
| `created_at` | TIMESTAMPTZ | |

Index: `agent_feed_events_run_id_idx(onboarding_run_id, id)`. The SSE feed reads `(id > after_id ORDER BY id ASC)`.

#### `curricula` (migration 002)

| column | type | notes |
|---|---|---|
| `id` | UUID PK | |
| `user_id` | TEXT | |
| `exam_id` | TEXT | |
| `onboarding_run_id` | UUID FK → `onboarding_runs(id) ON DELETE SET NULL` | |
| `domains` | JSONB | The full domain array (with topics, study_order, performance_score) |
| `active` | BOOLEAN | `TRUE` is the live curriculum |
| `created_at` | TIMESTAMPTZ | |

Index: `curricula_user_exam_active_idx(user_id, exam_id, active)`. There is at most one active curriculum per `(user_id, exam_id)`.

#### `performance_aggregates` (migration 002)

| column | type | notes |
|---|---|---|
| `user_id` | TEXT | |
| `exam_id` | TEXT | |
| `domain` | TEXT | |
| `correct_count` | INTEGER | |
| `total_count` | INTEGER | |
| `updated_at` | TIMESTAMPTZ | |

Primary key: `(user_id, exam_id, domain)`. Updated by `performance_repository.record_session_history` after every session. Drives the Readiness Score.

#### `exam_artifacts` (migration 003)

| column | type | notes |
|---|---|---|
| `id` | UUID PK | |
| `exam_code` | TEXT UNIQUE | e.g. `dva-c02` |
| `canonical_name` | TEXT | |
| `provider` | TEXT | `aws` |
| `official_guide_url` | TEXT | |
| `captured_at` | DATE | |
| `source_version` | TEXT | |
| `content_checksum` | TEXT | SHA-256 of the raw JSON bytes |
| `domains` | JSONB | The full domain array |
| `is_active` | BOOLEAN | Allows soft-deprecating an artifact |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

Index: `exam_artifacts_active_idx(is_active)`. This is a **runtime cache** of the JSON file in `agents/data/exam_artifacts/<exam_id>.json`; the file is the source of truth.

### LangGraph checkpointer tables

Created by `setup_checkpointer_tables` in autocommit mode (see §4). The library expects four tables in this order:

- `checkpoints` — one row per node boundary, keyed by `(thread_id, checkpoint_id)`. Holds the full serialized state.
- `checkpoint_writes` — pending writes pending commit. Cleared on commit.
- `checkpoint_migrations` — `v INTEGER` column, one row per applied version.
- `checkpoint_blobs` — large binary payloads (LLM message history, etc.).

Don't touch these directly. Use `graph.aget_state(config)`, `graph.aupdate_state(config, delta)`, or `graph.ainvoke(state, config)` — the library handles serialization.

### Exam artifact model (JSON shape)

`agents/data/exam_artifacts/dva-c02.json` is a strict, validated shape. `validate_artifact_shape` checks:

- Top-level required keys: `exam_code`, `canonical_name`, `provider`, `official_guide_url`, `captured_at`, `source_version`, `domains`.
- Each domain: `name`, `weight` (int 1..100), `task_statements` (non-empty list), `topics` (non-empty list).
- Sum of `domain.weight` must equal exactly 100.
- Each task statement: `id` and `text` are non-empty strings.
- Each topic: `id`, `name`, `task_statement_id` (must match a `task_statements[].id` in the same domain), `services` (non-empty list of strings), `source_ids` (non-empty list of strings).

Topics can also be plain strings (e.g., `"S3"`) — that's accepted for compat but discouraged; the loader/validator treats strings as legacy.

The current DVA-C02 artifact has 4 domains, 14 task statements, and 90+ topics. See the file directly for the full inventory.

---

## 6. The LangGraph state machine

This is the heart of the agents service. The structure is intentionally explicit — no abstractions hiding the node/edge definitions. The user is learning LangGraph deeply.

### State shape

`agents/state.py:AppState` is a `TypedDict` with these fields:

| field | type | initial | written by |
|---|---|---|---|
| `user_id` | `str` | (from request) | initial |
| `exam_id` | `str` | `"dva-c02"` | initial |
| `curriculum_id` | `str` | `""` | `coach_open` |
| `curriculum` | `list[Domain]` | `[]` | `coach_open` |
| `current_domain` | `str` | `""` | `coach_open` |
| `current_topic` | `str` | `""` | `coach_open`, `rex_rechallenge` |
| `current_topic_id` | `str` | `""` | `coach_open`, `rex_rechallenge` |
| `current_task_statement_id` | `str` | `""` | `coach_open`, `rex_rechallenge` |
| `current_task_statement` | `str` | `""` | `coach_open`, `rex_rechallenge` |
| `current_services` | `list[str]` | `[]` | `coach_open`, `rex_rechallenge` |
| `current_source_ids` | `list[str]` | `[]` | `coach_open`, `rex_rechallenge` |
| `rex_difficulty` | `str` | `"medium"` | `coach_open`, `rex_rechallenge` |
| `max_cycles` | `int` | `2` | initial |
| `cycle` | `int` | `0` | `coach_open` (→ 1), `rex_rechallenge` (→ +1) |
| `current_challenge` | `Challenge` | `{}` | `rex_challenge`, `rex_rechallenge` |
| `user_answer` | `str` | `""` | set via `aupdate_state` in `/session/submit` |
| `last_evaluation` | `EvaluationResult` | `{}` | `evaluate_answer` |
| `session_history` | `Annotated[list[Exchange], operator.add]` | `[]` | `sage_depth`, `sage_explain`, `coach_close` |
| `db_session_id` | `str` | `""` | `coach_open` |

The `Annotated[list[Exchange], operator.add]` on `session_history` is the **only** place the graph depends on LangGraph's state-reduction machinery. When `sage_depth` returns `{"session_history": [exchange]}`, the reducer appends that exchange to the existing list rather than overwriting it. If you forget the annotation, every Sage node will wipe history.

`coach_close` returns a synthetic `Exchange` with `outcome: "summary"` so the summary line is part of the persisted history. The `_session_results` and `_latest_exchange` helpers in `agents/routes/session.py` filter on `outcome ∈ {correct, incorrect}` to skip it.

### Nodes, in execution order

#### `coach_open` (`agents/nodes/coach_open.py`)

- Reads `user_id`, `exam_id` from state.
- Calls `curriculum_repository.choose_today_target(user_id, exam_id)` to get `{domain, topic, topic_id, task_statement_id, task_statement, services, source_ids, difficulty, curriculum_id}`.
- Calls `curriculum_repository.get_active_curriculum(user_id, exam_id)` to load the full domain list.
- Calls `repositories.create_session(...)` to insert a `sessions` row. The UUID is stashed in `db_session_id`.
- Returns the delta: `current_domain`, `current_topic`, `current_*` family, `rex_difficulty`, `curriculum_id`, `curriculum`, `cycle: 1`, `db_session_id`.

#### `rex_challenge` (`agents/nodes/rex_challenge.py`)

- Synchronous (no `await`).
- Calls `prompts.rex.build_rex_challenge_prompt(...)` with the current domain/topic/services/source_ids.
- Calls `llm.get_llm(MODEL).invoke(...)` synchronously, parses the JSON (stripping code fences), asserts `domain/topic/scenario/question` are present, raises if not.
- Returns `current_challenge` (a `Challenge` TypedDict).

#### `evaluate_answer` (`agents/nodes/evaluate_answer.py`)

- **This is the first interrupt point.** The graph pauses *before* this node runs.
- Reads `user_answer` (set by `aupdate_state` in `/session/submit`).
- Calls `prompts.evaluator.build_evaluator_prompt(...)` with `domain/topic/scenario/question/user_answer`.
- Calls `llm.get_llm(MODEL).invoke(...)` with `temperature=0.2, max_tokens=256`.
- Asserts `outcome ∈ {correct, incorrect}`. Raises if not.
- Returns `last_evaluation`.

#### `sage_depth` and `sage_explain` (`agents/nodes/sage_respond.py`)

The conditional edge after `evaluate_answer` routes to one of these. They share `_generate_sage_response`; the only difference is the prompt builder.

- Calls `sage_sources.load_sage_grounding(exam_id, topic_id, topic, services, source_ids)` to build a `{source_context, citations}` bundle.
- Calls `prompts.sage.build_sage_depth_prompt` (or `build_sage_explain_prompt`) with the grounding attached. If the grounding is empty, the prompt includes the "Unverified explanation:" prefix automatically (`prompts/sage.py:_grounding_rules`).
- Calls `llm.get_llm(MODEL).ainvoke(...)` — the only `ainvoke` in the graph. Streams tokens (we don't read the stream directly — the SSE is captured by the route's `astream_events` consumer).
- Builds an `Exchange` record (challenge, user_answer, outcome, sage_response, citations) and appends it to `session_history`.
- Calls `repositories.create_exchange(...)` to persist the row. The DB write is fire-and-forget — failure logs but doesn't block.

#### Conditional edge after Sage: `rex_rechallenge` | `coach_close`

`route_after_sage(state)` returns `"rex_rechallenge"` if `cycle < max_cycles`, else `"coach_close"`. Note that `cycle` here is the *current* cycle, not the next one — `rex_rechallenge` increments it.

#### `rex_rechallenge` (`agents/nodes/rex_rechallenge.py`)

- **This is the second interrupt point.** The graph pauses *before* this node runs.
- Calls `curriculum_repository.choose_rechallenge_target(user_id, exam_id, domain, previous_topic, previous_task_statement_id)` — note the `previous_*` arguments from the just-finished challenge.
- The scheduler returns a different topic in the same domain (or a related one in the same task statement) with `difficulty: "hard"`.
- Calls `prompts.rex.build_rex_rechallenge_prompt(...)` with the new target.
- Calls `llm.get_llm(MODEL).invoke(...)` with `temperature=0.8, max_tokens=512`.
- Returns `current_challenge` (new), the `current_*` family (new), `rex_difficulty: "hard"`, and `cycle: state.cycle + 1`.

#### `coach_close` (`agents/nodes/coach_close.py`)

- Calls `repositories.close_session(db_session_id)` to stamp `ended_at`.
- Calls `performance_repository.record_session_history(user_id, exam_id, history)` to UPSERT per-domain `correct_count` / `total_count` into `performance_aggregates`.
- Returns a synthetic `Exchange` with `cycle: -1, domain: "__summary__", outcome: "summary"` and `sage_response: f"Session complete: {correct}/{len(history)} correct"`. This is the only place session_history grows without a real challenge.

### Conditional edges

Two:

```python
graph.add_conditional_edges(
    "evaluate_answer",
    route_after_evaluation,                 # outcome == "correct" ? "sage_depth" : "sage_explain"
    {"sage_depth": "sage_depth", "sage_explain": "sage_explain"},
)

# Two edges, same routing function:
graph.add_conditional_edges("sage_depth",  route_after_sage, ...)
graph.add_conditional_edges("sage_explain", route_after_sage, ...)
```

The mapping dict is required for LangGraph to render the graph and to validate that all routing destinations exist as nodes. Don't omit it.

### Interrupts

The graph is compiled with:

```python
_cached_graph = build_session_graph().compile(
    checkpointer=get_checkpointer(),
    interrupt_before=["evaluate_answer", "rex_rechallenge"],
)
```

This means LangGraph runs up to the node, pauses, and surfaces a snapshot. The next `ainvoke(None, config)` (or `aupdate_state(...)` then `ainvoke`) resumes the graph from that node. The state at the interrupt point is fully persisted in Postgres, so a process restart and resume works.

**Important**: interrupts happen *before* the node, not after. This is why `/session/submit` does `aupdate_state` *then* `ainvoke` — the answer is written into state, and when LangGraph resumes and runs `evaluate_answer`, the answer is already there.

### The compiled graph singleton

`get_session_graph()` in `agents/graphs/session.py` is lazy and cached. First call wires the checkpointer; subsequent calls return the same compiled graph. The cache is module-level; uvicorn's `--reload` re-imports the module and rebuilds on change.

---

## 7. SSE streaming topology

The session submit flow is the most complex piece of cross-service plumbing. It needs to:

1. Stream tokens from Rex/Sage LLM calls back to the browser.
2. Emit application-level events (the evaluation, the citations) at well-defined points.
3. Survive the LangGraph pause/resume cycle.

The full path:

```
OpenRouter  →  ChatOpenAI.ainvoke (LangChain)
                 ↓
              graph.astream_events  (route handler in agents/routes/session.py:submit_answer)
                 ↓ filtered: on_chat_model_stream where langgraph_node in {sage_depth, sage_explain}
              SSE event: { "type": "token", "token": "..." }
                 ↓
              FastAPI StreamingResponse
                 ↓
              Next.js /api/session/submit (proxied verbatim)
                 ↓
              browser fetch response body
                 ↓
              lib/sse-reader.ts:readSseStream → app/session/session-stream.ts:readSessionStream
                 ↓
              useSession handlers: onToken → setSageText; onEvaluation → setEvaluation; onCitations → setSageCitations; onDone → setPhase("sage_done")
```

The route handler is the orchestrator. It iterates `graph.astream_events(None, config=config, version="v2")` and emits SSE events at the right boundaries:

| LangGraph event | Filter | SSE event |
|---|---|---|
| `on_chat_model_stream` with `langgraph_node` in `{sage_depth, sage_explain}` | Yes | `{ "type": "token", "token": "<chunk.content>" }` |
| `on_chain_end` with `name == "evaluate_answer"` | Yes | `{ "type": "evaluation", "data": "<json.dumps(last_evaluation)>" }` |
| `on_chain_end` with `name in {"sage_depth", "sage_explain"}` | Yes | `{ "type": "citations", "data": <citations array> }` |
| `on_chain_end` with `name == "LangGraph"` | Yes | `{ "type": "done" }` |
| Anything else | No | (silently skipped) |

The `astream_events` iteration runs until the graph finishes — for the first cycle that's `evaluate → sage → END` (interrupt before next `rex_rechallenge`); for the second cycle that's `evaluate → sage → coach_close → END`.

### Why `astream_events` and not `astream`?

`astream` yields state deltas, which is the right primitive for state inspection but the wrong one for token streaming — you'd have to diff every chunk. `astream_events` exposes the underlying `on_chat_model_stream` callbacks, which is what you want for token-by-token UI updates. The `version="v2"` flag is required for the `on_chat_model_stream` event to be emitted.

The on-chain-end hooks (for `evaluate_answer` and the Sage nodes) are how the application injects its own events (the evaluation result, the citations) into the token stream. The graph's reducer machinery doesn't fire any application-level events on its own.

---

## 8. Onboarding pipeline

The onboarding flow runs three agents in sequence — Onboarding Agent, Blueprint Scout, Curriculum Builder — with a live SSE feed in between. Two of the three are background jobs that run inside the Next.js process via BullMQ.

```
Browser                   Next.js                                     Agents                                         Postgres
───────                   ────────                                     ──────                                         ────────
welcome → exam → style                                                  
  POST /api/onboarding/start ──▶ POST :8000/onboarding/start
                                  validate_exam_id ────▶ ExamValidation
                                  create_onboarding_run ──────────────▶ onboarding_runs row
                                  add_feed_event("Onboarding Agent", "complete", ...)
                                  ◀── { accepted: true, onboarding_id }
                              ──▶ agentQueue.add("blueprint_scout")   ──▶ Redis (LPUSH)
                              ◀── { accepted: true, ... }
                                                                        
[BullMQ worker (lib/queue.ts:agentWorker) picks up blueprint_scout]    
                              ──▶ POST :8000/jobs/blueprint-scout
                                  update_run_status → "blueprint_running"
                                  add_feed_event("Blueprint Scout", "running", ...)
                                  resolve_blueprint(exam_id) → BlueprintScoutResult
                                  save_blueprint(...) ─────────────────▶ onboarding_runs.blueprint
                                  add_feed_event("Blueprint Scout", "complete", "Domains: ...%")
                              ──▶ agentQueue.add("curriculum_builder") → Redis
                                                                        
[BullMQ worker picks up curriculum_builder]                              
                              ──▶ POST :8000/jobs/curriculum-builder
                                  update_run_status → "curriculum_running"
                                  add_feed_event("Curriculum Builder", "running", ...)
                                  build_curriculum(blueprint, learning_style) → list[Domain]
                                  create_curriculum(...) ─────────────▶ curricula row
                                  complete_onboarding(...) ────────────▶ onboarding_runs row
                                  add_feed_event("Curriculum Builder", "complete", ...)
                                                                        
Browser (subscribed via SSE)                                              
  GET /api/onboarding/feed?onboarding_id=... ──▶ GET :8000/onboarding/{id}/feed
                                                  poll agent_feed_events (500ms)
                                                  ◀── SSE events
  Curriculum Builder "complete" arrives → close EventSource
  loadPlan() → /api/dashboard/summary → PlanReveal
  "Let's go" → /dashboard
```

The key point: **there is no long-polling or websockets**. The agents service polls `agent_feed_events` every 500ms in the SSE generator and emits whatever has appeared since the last cursor. The Next.js worker runs the jobs and writes the events; the SSE is a thin tail of the table.

The 500ms poll interval is the latency floor. If you need lower latency, the natural change is to introduce a Postgres `LISTEN`/`NOTIFY` channel — but that's not warranted at V1.

### Job chaining

`blueprint_scout` chains to `curriculum_builder` by enqueueing the next job from inside the worker:

```python
// lib/queue.ts (agentWorker.process)
if (job.name === "blueprint_scout") {
  await runBackendJob("/jobs/blueprint-scout", job.data.onboardingId);
  await agentQueue.add(
    "curriculum_builder",
    { onboardingId: job.data.onboardingId },
    { jobId: `curriculum-${job.data.onboardingId}` },
  );
} else if (job.name === "curriculum_builder") {
  await runBackendJob("/jobs/curriculum-builder", job.data.onboardingId);
}
```

The `jobId` is namespaced (`blueprint-<id>`, `curriculum-<id>`) so BullMQ dedupes if the same job is enqueued twice (e.g., a retry).

### Failure handling

A failed `blueprint_scout` writes a `failed` event to `agent_feed_events` and marks the run as `failed`. The SSE loop's `get_onboarding_run` check picks that up and the generator exits. The UI shows the failure message and the user can retry from the `style` step.

A failed `curriculum_builder` does the same. There's no automatic retry at the Bull level beyond the default `attempts: 1` (effectively none); if the LLM call fails or the artifact is malformed, the user gets a "Curriculum Builder rejected this exam" message.

---

## 9. Coverage scheduling

`agents/coverage_scheduler.py` is the most subtle piece of the agents service. It answers "what (domain, topic) should Rex challenge next, given what the user has already done?".

### Candidates

For each (domain, topic) pair in the active curriculum (or the default artifact if no curriculum is set), build a candidate row:

```python
{
  "domain": <name>,
  "domain_weight": <int 1..100>,
  "study_order": <int 1..4>,
  "topic": { id, name, task_statement_id, services, source_ids },
  "task_statement": <text>,
  "stat": { correct_count, total_count }  # from exchanges grouped by topic
}
```

`topic_payload` (in `agents/curriculum_topics.py`) normalises topic objects to dicts with `{id, name, task_statement_id, services, source_ids}` — strings are upgraded to `{id, name, services: [], source_ids: []}` for compat.

### Today target — `select_today_target`

Ranks candidates by a 6-tuple key:

```python
key = (
  _topic_rank(item),                       # 0=untouched, 1=mixed, 2=mastered
  domain_total - expected,                 # domain under-tried vs. weight-share
  item["stat"]["total_count"],             # topic under-tried
  -item["domain_weight"],                  # prefer higher-weight domains (descending)
  item["study_order"],                     # earlier study_order
  item["topic"]["name"],                   # deterministic
)
```

`expected = total_attempts * (domain_weight / 100)`. So if a domain has 30% weight and the user has done 10 attempts total, expected is 3; if they've done only 1 attempt in that domain, the deficit is -2 (lower is better). This biases the scheduler toward domains that are **under-represented relative to their blueprint weight**.

`min(candidates, key=...)` wins.

### Rechallenge target — `select_rechallenge_target`

Same domain as the previous challenge, but a different topic. The algorithm:

1. Filter candidates to the same domain and `topic.name != previous_topic`.
2. If empty, allow same-topic candidates in the same domain.
3. If empty, return an empty target.
4. Try `_weak_or_uncovered(same_task_statement_id)` first (candidates sharing the previous task statement with `_topic_rank < 2`).
5. Fall back to `_weak_or_uncovered(all_candidates_in_domain)`.
6. Fall back to `same_task_statement_id` candidates.
7. Fall back to any candidate.
8. Pick `min(...)` with the key `(_topic_rank, total_count, name)`.
9. Force `difficulty: "hard"` on the result.

The result is **always** harder than the first challenge and **always** in the same domain. The topic moves deliberately so a session doesn't sample the same narrow area.

### What the scheduler does NOT do

- **No difficulty tracking across sessions.** A topic's difficulty is determined by its per-topic stat: `medium` if never tried or mixed, `hard` if mastered. The Phase 5 5.6 work (consecutive-session accuracy thresholds) is not wired.
- **No LLM calls.** The scheduler is pure Python over the active curriculum + `performance_aggregates` + `exchanges`.
- **No user preferences.** Learning style only influences the *order of study* (via `study_order` in the curriculum). It does not change today's target.

---

## 10. Sage grounding & citation pipeline

Sage's job is to explain a Rex challenge with AWS-specific depth. The pipeline has three components: **source resolution** (what to cite), **prompt shaping** (how to instruct Sage), and **storage** (where citations go).

### Source resolution — `agents/sage_sources.py`

`load_sage_grounding(exam_id, topic_id, topic, services, source_ids)` returns:

```python
{
  "source_context": "<text block injected into the prompt>",
  "citations": [{"url": ..., "title": ..., "snippet_id": ...}, ...]
}
```

The algorithm:

1. **Per-topic snippet file** — if `agents/data/sage_snippets/<exam_id>/<topic_id>.md` exists, use it as the `source_context` and parse `Source: <title> | <url> | <snippet_id>` lines as citations. This is the highest-fidelity path; it's where you'd hand-curate overrides for topics whose citations are unreliable from the auto-resolution.

2. **Auto-resolve from `source_ids`** — for each `source_id` like `developer-associate-02-domain1.md#anchor`, build a citation pointing at `https://docs.aws.amazon.com/aws-certification/latest/developer-associate-02/developer-associate-02-domain1.html#anchor`. The exam-guide root is looked up in `EXAM_GUIDE_ROOTS`. The `snippet_id` is the raw source_id, so you can trace the citation back to the artifact.

3. **Auto-resolve from `services`** — for each AWS service in `services` (e.g., `"AWS Lambda"`, `"Amazon DynamoDB"`), look up the curated entry in `SERVICE_DOCS` and add `{title, url, snippet_id: "aws-service-docs:<service>"}`. The dict also carries a one-sentence snippet, which becomes part of the `source_context`.

4. **Dedupe** by URL, cap at 4 citations.

5. **Empty fallback** — if the result is empty, return `source_context: "No verified official AWS source was found for this topic."`. The prompt builder (`prompts/sage.py:_grounding_rules`) sees `has_verified_sources == False` and prepends "Unverified explanation:" instructions.

The current `SERVICE_DOCS` is hand-curated with 8 services (Lambda, API Gateway, DynamoDB, SQS, SNS, EventBridge, IAM, Step Functions). When Rex starts generating challenges for services not in this list, add them.

### Prompt shaping — `agents/prompts/sage.py`

Two paths, `build_sage_depth_prompt` and `build_sage_explain_prompt`. They differ in tone (depth goes broader; explain fixes a misconception) but share the structure:

```
Topic: <topic> (<domain>)
Grounding:
  <if verified>: "Use the verified AWS sources below..."
  <if not>:     "No verified AWS source was available. Begin exactly with 'Unverified explanation:'..."
Source material:
  <source_context>

The challenge:
  <scenario>
  <question>

They answered: "<user_answer>"
Evaluator note: <reasoning>

[depth: "They got it right. Now go deeper..."]
[explain: "Correct the misconception. Cite the specific AWS service..."]
```

The system prompt (shared) establishes Sage's voice: "dry wit, hard-won confidence. You never lecture. You never hedge." This is the product differentiator; don't soften it.

### Storage

Citations are returned from the node as part of the `Exchange` dict and persisted by `repositories.create_exchange` to the `exchanges.citations` JSONB column. The shape is `[{url, title, snippet_id}, ...]`. They're surfaced to the UI in the SSE `citations` event (`agents/routes/session.py:submit_answer`) and rendered by `components/session/sage-card.tsx`.

The `__summary__` exchange written by `coach_close` has `citations: []`.

### The "unverified" path

If no source could be resolved, Sage is told to begin with "Unverified explanation:" and not invent citations. The Sage card renders the explanation without the citation panel. This is the explicitly-handled failure mode — see R5.4 in `docs/exam-reliability-rubric.md`.

---

## 11. Trust & audit model

The product is built on the rule: **LLM outputs never directly mutate persistent state**. Every state mutation goes through application code that validates the LLM output first.

### The boundary

```
Rex LLM call    → JSON.parse + assert {domain, topic, scenario, question}
               → application code writes to state["current_challenge"]
               → Postgres write happens in repositories.create_session (coach_open) or repositories.create_exchange (sage_*)

Sage LLM call   → LLM streams text + application code resolves citations from sage_sources
               → application code writes an Exchange {challenge, user_answer, outcome, sage_response, citations}
               → Postgres write via repositories.create_exchange

Evaluator LLM  → JSON.parse + assert {outcome: correct|incorrect}
               → application code writes to state["last_evaluation"]
```

LLM output is never written to the DB as-is. The application always wraps it in a typed structure with explicit fields.

### What this prevents

- A misbehaving LLM cannot, e.g., fabricate an `exchanges` row with `outcome: "correct"` and a fake `user_answer`. The `outcome` is parsed and validated; an unknown value raises.
- A misbehaving LLM cannot inject SQL into the `challenge` JSONB. JSON parsing happens in application code; the JSON is then `json.dumps`'d and passed as a parameter to a `psycopg` query (parameterised, no string interpolation).
- A misbehaving LLM cannot write a citation URL that points at attacker-controlled content. The `sage_sources` module owns citation resolution; the LLM prompt *requests* a citation, but the actual `url/title/snippet_id` comes from the curated source set.

### What this does NOT prevent

- A misbehaving LLM can produce factually wrong explanations. Phase 7's evaluation harness (issue 7.7) measures this; the rubric (`docs/exam-reliability-rubric.md`) sets the human-review pass bar.
- A misbehaving LLM can produce a malformed JSON that causes `_strip_code_fences + json.loads` to raise. The node raises; LangGraph records the error; the route returns a 500; the UI shows "Rex couldn't generate a challenge. Try again." (or "Evaluation failed", etc.). No half-written state.

### Replay

The full graph state is persisted at every node boundary (the checkpointer). A `thread_id` lets you resume from any checkpoint. To replay a session:

```python
config = {"configurable": {"thread_id": "<uuid>"}}
state = await graph.aget_state(config)
# state.values is the full AppState
# state.next is the set of next nodes (empty if done)
```

Combined with the `exchanges` table, you have an immutable record of what happened in every session — the challenge, the answer, the outcome, the Sage response, the citations. This is the audit trail.

---

## 12. External integrations & failure handling

### OpenRouter

- **Endpoint:** `https://openrouter.ai/api/v1/chat/completions`
- **Library:** LangChain `ChatOpenAI` (`agents/llm.py:get_llm`) — pointed at OpenRouter via `base_url`. Caches per model.
- **Failure mode:** network error / 4xx / 5xx raises a LangChain exception. The node raises; the route returns 500; the UI shows an error.
- **No automatic retry today.** Add retries with backoff in `agents/llm.py` if you need them.

### Postgres

- **Failure mode:** psycopg pool raises on connect / query error. If the pool cannot open at boot, `init_checkpointer()` uses `InMemorySaver`; state does not survive restart.
- **Runtime DB outage:** repository writes may log and continue where call sites catch them, but an active `AsyncPostgresSaver` can still fail checkpoint writes. The in-memory fallback is selected at boot, not after a live pool drops.

### Redis (BullMQ)

- **Failure mode:** if Redis is down, the Next.js worker logs errors and retries. The onboarding flow won't complete (no jobs run).
- **No idempotency guarantees** beyond the namespaced `jobId` (see §8). Don't dispatch the same job from two places.

### BullMQ worker (in Next.js process)

- **Failure mode:** if the worker crashes mid-job, the job retries. The `jobId` dedupes re-enqueues.
- **Hot-reload safety:** `lib/queue.ts` uses a `global` singleton to survive Next.js dev-mode hot reloads. The `WORKER_VERSION` constant is bumped when worker logic changes; on mismatch, the old worker is closed.

### SSE consumers

- **Failure mode:** if the browser's `fetch` to `/api/session/submit` is dropped (e.g., network blip), the SSE stream ends mid-sentence. The UI's `useSession` does not auto-resume — the user must hit **Retry**, which calls `restoreSession` then replays the last action (start / resume / submit / next).
- **On the server side:** the agents service's `astream_events` is consumed inside the route handler. If the client disconnects, the route returns; the SSE generator raises; the graph stays paused at the next interrupt (state is persisted by the checkpointer, so a resume works).

### Unknown / unsupported exam codes

- **Failure mode:** `validate_exam_id` returns `accepted=False` with a message naming the supported codes. `/api/onboarding/start` returns 200 with `{accepted: false, message: ...}`. The UI shows the message and stays on the style step. **No silent coercion to a default.**

---

## 13. LLM model & cost strategy

All models are routed through OpenRouter with one API key.

| Agent | Model | Cost / 1M in→out | Why this model |
|---|---|---|---|
| Rex | `anthropic/claude-sonnet-4.6` | $3 → $15 | Quality non-negotiable — challenge realism is the product. |
| Sage | `anthropic/claude-sonnet-4.6` | $3 → $15 | Accuracy non-negotiable — explanations must cite correctly. |
| Evaluator | `anthropic/claude-sonnet-4.6` | $3 → $15 | Trust the outcome — a wrong evaluation erodes the product. |
| Curriculum Builder | `anthropic/claude-sonnet-4.6` | $3 → $15 | One-shot, reasoning-heavy. Quality worth paying for. |
| Onboarding Agent (planned) | `anthropic/claude-haiku-4.5` | $1 → $5 | Warm conversational, mid-cost. |
| Blueprint Scout (planned) | `openai/gpt-4.1` | $2 → $8 | Best tool-use + structured extraction. |
| Resource Gatherer (v1.1) | `deepseek/deepseek-v4-flash` | $0.09 → $0.18 | Background, near-zero cost. |
| Coach (v1.1) | `meta-llama/llama-3.3-70b-instruct` | $0.10 → $0.32 | Template-driven. |
| Gap Tracker (v1.1) | `deepseek/deepseek-v4-pro` | $0.44 → $0.87 | Strong analytical MoE. |

Estimated per-session cost: **~$0.054** (Rex + Sage account for ~98%).

### Locked decisions

- **Rex and Sage are product-critical.** Do not swap their models without an explicit A/B test showing quality parity. From AGENTS.md.
- **Cost-optimisation candidates** (`x-ai/grok-4.20` is mentioned in `docs/tech-stack.md`) are tracked as a post-MVP A/B test, not an active change.

### How the LLM is called

`agents/llm.py:get_llm(model)` is the only construction site. It lazily creates a `ChatOpenAI` (LangChain) configured for OpenRouter. Cached per model name. Used from `rex_challenge`, `rex_rechallenge`, `evaluate_answer`, `sage_depth`, `sage_explain`, `build_curriculum`, and `evals.content_quality` (live mode).

The legacy `lib/openrouter.ts` and `lib/openrouter-json.ts` are direct (non-LangChain) OpenRouter callers used by the `/api/rex/*`, `/api/evaluate`, and `/api/sage` routes. These are kept for reference and for any future need to call OpenRouter from the browser/Next.js without going through the agents service.

---

## 14. Environment & configuration

### Env vars

| Var | Default | Where used | Notes |
|---|---|---|---|
| `OPENROUTER_API_KEY` | — (required) | Agents service (lifespan raises if missing) | The single LLM key. |
| `DATABASE_URL` | `postgresql://gauntlet:gauntlet@localhost:5432/gauntlet` | Agents service | Falls back to `InMemorySaver` if unset, but only with degraded persistence. |
| `REDIS_URL` | `redis://localhost:6379` | Next.js (`lib/queue.ts`) | The BullMQ connection. |
| `LANGGRAPH_URL` | `http://localhost:8000` | Next.js API proxies | The agents service. |
| `CLERK_*` | — (Phase 4) | Future | Not read today. |

Loaded in two places:
- **Next.js:** automatically via `next dev` / `next start`. File: `.env.local` (gitignored) and `.env.example` (template).
- **Python:** `agents/main.py` does `load_dotenv(PROJECT_ROOT / ".env.local")` then `load_dotenv(PROJECT_ROOT / ".env")`. Both are read; `.env.local` wins.

### Docker Compose

`docker-compose.yml` runs `postgres:16-alpine` and `redis:7-alpine`. Both have healthchecks; both named `gauntlet` for credentials (`gauntlet` / `gauntlet`). No app containers — the Next.js and Python services run on the host.

### Next.js config

- `next.config.ts` is empty (5 lines).
- `tsconfig.json` is strict mode, `moduleResolution: "bundler"`, `@/*` path alias to root.
- `eslint.config.mjs` uses flat config: `eslint-config-next/core-web-vitals` + `eslint-config-next/typescript`.
- `postcss.config.mjs` enables `@tailwindcss/postcss` (Tailwind v4).
- `components.json` is the shadcn config (`new-york`, `neutral` base, lucide icons).

### Python config

- No `pyproject.toml`. Dependencies pinned in `agents/requirements.txt`.
- No test runner. No CI. No lint. (Phase 8 is the planned landing pad.)
- `agents/main.py` uses Python 3.10+ syntax (`from __future__ import annotations` everywhere; `str | None` union syntax).

---

## 15. Open questions, debt, known limitations

### Documented conflicts

- **Boss Battles:** deferred to v1.1 in `docs/tracker.md` and `docs/product-spec.md`, but listed as issue 5.5 (P2) in `docs/implementation-backlog.md`. Resolved scope before building.
- **`/api/sage` and `/api/rex/*` legacy routes:** still wired but not used by the production session flow. Kept for reference and for direct-from-frontend tests. Removing them is a 1-PR cleanup.

### Known violations

- **`lib/openrouter.ts` is 266 lines** (200-line hard rule). Must be split before adding more code. The natural split is: (1) `lib/openrouter/sse.ts` (the SSE encoding), (2) `lib/openrouter/errors.ts` (the typed error code and `openRouterErrorToSseResponse`), (3) `lib/openrouter/stream.ts` (the upstream→SSE transform), (4) `lib/openrouter.ts` (the public `streamOpenRouterResponse` and `sseResponseFromStream` facade).
- **`agents/routes/onboarding.py:18-21` and `agents/routes/jobs.py:39-41` have hardcoded DVA-C02 strings** in event messages ("DVA-C02 only", "Deployment 32%..."). These are the violations called out in R6 of the exam-reliability-rubric.

### Known limitations (V1)

- **No second exam.** `dva-c02.json` is the only artifact. `validate_exam_id` rejects everything else. The second-cert smoke (issue 7.8) is not yet shipped.
- **No Coach agent.** The session summary is static. ADR-0001 explains the design choice.
- **No Boss Battles, Gap Tracker, RAG, spaced repetition, notes.** All deferred to v1.1.
- **No Clerk auth.** All `user_id`s are anonymous browser UUIDs.
- **No PWA.** No service worker, no manifest, no offline state.
- **No CI, no tests, no `pyproject.toml`.** Phase 8 is the planned landing pad.
- **2-cycle session length.** ADR-0001 makes the default explicit; re-evaluation criterion is "engagement vs. signal vs. time" after dogfood.

### What needs to be true for "done"

The phase-level Definition of Done is in `docs/task-breakdown.md`. The current status (per `docs/tracker.md`):

- ✅ Phase 1, 2, 3, 6 complete.
- 🟡 Phase 7 in progress (7.1–7.7 done; 7.8 next).
- ⏳ Phase 4 (Clerk), Phase 5 (PWA + polish), Phase 8 (tests + CI) planned.
- ⏭️ Pilot/launch deferred to post-MVP.

The exam-reliability-rubric (`docs/exam-reliability-rubric.md`) is the most concrete "done" definition for Phase 7: every R1–R6 must PASS for DVA-C02, R6.4 must PASS for SAA-C03, and R7 (manual QA) must record at least 20 DVA-C02 + 5 SAA-C03 sessions.
