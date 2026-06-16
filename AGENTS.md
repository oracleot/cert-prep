# AGENTS.md

## Repo Reality (current state)
- **Phase 1 is fully shipped.** `app/`, `lib/`, `components/`, `agents/state.py`, `agents/db.py`, `migrations/`, `docker-compose.yml` all exist. The "planning-only" claim in prior sessions is stale.
- **Phase 2 in progress.** SessionSubgraph (2.3) and Postgres checkpointer + persistence (2.4) shipped. `agents/graphs/`, `agents/nodes/`, `agents/routes/`, and `agents/repositories.py` are all populated. Remaining Phase 2: 2.2 (docker compose AC checklist), 2.5 (BullMQ), 2.6 (Next.js → LangGraph API), 2.7 (Railway deploy).
- No CI workflows, no test runner (Jest/Vitest/pytest), no `pyproject.toml`.

## Source of truth order
- Prefer executable code/config over docs whenever code exists.
- For planning decisions, use:
  1. `docs/implementation-backlog.md` — issue-level acceptance criteria
  2. `docs/tech-stack.md` — locked stack decisions
  3. `docs/ux-flows.md` — UI behavior, edge/error states
  4. `docs/tracker.md` — what is complete vs in-progress, key constraints

## Sensitive files — never read
Agents must never open, read, grep, cat, dump, log, or echo the contents of secret-bearing files. Treat them as opaque. If a task seems to require a secret, ask the user to paste the relevant value (or a redacted shape) — never the file.

Blocked by default (non-exhaustive):
- `.env`, `.env.local`, `.env.*.local`, `.env.development`, `.env.production`, `.envrc`, `direnv`-managed files
- Anything matching `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.crt`, `*.cer`
- `secrets.*`, `credentials.*`, `*.token`, `*password*`, `*secret*` (case-insensitive)
- `.aws/`, `.ssh/` (incl. `id_rsa*`, `id_ed25519*`, `known_hosts`, `config`), `.gcp/`, `.kube/`, `.docker/config.json`
- `.netrc`, `.pgpass`, `.npmrc` (real user config), `.pypirc`, `service-account*.json`, `gcloud-credentials.json`
- Anything in `migrations/` that is named like seed data with PII

Safe to read (these are templates, not secrets): `.env.example`, `.env.sample`, `.env.test`, CI workflow YAMLs, `docker-compose.yml`, `pyproject.toml`, `package.json`.

If you accidentally read a sensitive file, stop, do not echo its contents back, and tell the user which path was opened so they can rotate it. Do not commit, paste, or summarize secret values.

## Dev runbook (verified against actual repo)
```
cp .env.example .env.local      # fill OPENROUTER_API_KEY at minimum; DATABASE_URL is required for Phase 2 and has a working default in .env.example
docker compose up -d            # Postgres :5432, Redis :6379 (both named "gauntlet")
npm install && npm run dev      # Next.js on :3000
# Phase 2 only:
cd agents && pip install -r requirements.txt
python -m uvicorn main:app --reload  # target: :8000
```
- The agents service refuses to start if `DATABASE_URL` is unset. If you see `RuntimeError: DATABASE_URL is not set` on boot, copy it from `.env.example` into `.env.local`.
- `langgraph-checkpoint-postgres==2.0.3`'s `AsyncPostgresSaver.setup()` is broken on a fresh DB (UndefinedTable in the version-probe SELECT aborts the transaction before migrations run). `agents/db.py:setup_checkpointer_tables` works around it by pre-creating the checkpointer tables in autocommit mode. Do not "simplify" this back to a plain `await checkpointer.setup()`.
- `npm run lint` runs ESLint (eslint-config-next, core-web-vitals + TypeScript).
- No typecheck script in package.json; run `npx tsc --noEmit` manually.
- No test command exists yet.

## Architecture: what's actually wired
- **Phase 1 loop (fully working):** `app/session/use-session.ts` orchestrates the full 2-cycle Rex→Sage loop via direct Next.js API routes (`/api/rex/challenge`, `/api/rex/rechallenge`, `/api/evaluate`, `/api/sage`). Domain hardcoded to `"Deployment"`, `MAX_CYCLES = 2` in `use-session.ts`.
- **OpenRouter clients:** `lib/openrouter.ts` (SSE streaming) and `lib/openrouter-json.ts` (structured JSON). The SSE client strips markdown fences before `JSON.parse` in the JSON client.
- **Agent prompts:** `agents/prompts/` has both `.ts` files (consumed by Next.js API routes now) and `.py` ports (for Phase 2 LangGraph). All three Python ports (`rex.py`, `sage.py`, `evaluator.py`) exist.
- **Phase 2 graph runtime:** `agents/state.py` has the full `AppState` TypedDict with `Annotated[list[Exchange], operator.add]` for LangGraph additive state. `agents/graphs/session.py` builds the SessionSubgraph explicitly (no abstractions) and compiles lazily with the Postgres checkpointer on first call. `agents/db.py` owns the pool + AsyncPostgresSaver singleton; `agents/repositories.py` owns application-table CRUD (sessions, exchanges). The checkpointer setup is idempotent and survives restart (see runbook note).

## LLM model assignments (from `docs/tech-stack.md`)
- Rex, Sage, Curriculum Builder → `anthropic/claude-sonnet-4.6`
- Onboarding Agent → `anthropic/claude-haiku-4.5`
- Blueprint Scout → `openai/gpt-4.1`
- Resource Gatherer → `deepseek/deepseek-v4-flash`
- Gap Tracker → `deepseek/deepseek-v4-pro`
- Coach → `meta-llama/llama-3.3-70b-instruct`
- Do not swap Rex or Sage models without A/B test — they are product-critical.

## Phase guardrails
- **Phase 1 is done.** Phase 2 is next: LangGraph graph + FastAPI service + Postgres checkpointer.
- Do not wire Clerk auth before Phase 4.
- Keep DVA-C02 hardcoded; no multi-exam generalization in V1.
- LangGraph graph structure/state/edges must stay explicit — no heavy abstractions. The user is learning LangGraph deeply.
- `agents/main.py` exists as the FastAPI entry point for Phase 2; keep graph wiring explicit as routes and nodes are added.

## Known violation to fix before editing `lib/openrouter.ts`
- `lib/openrouter.ts` is 266 lines — violates the 200-line hard rule. Split before adding any more code to it.

## Known doc conflict
- Boss Battles: deferred to v1.1 in `docs/tracker.md` and `docs/product-spec.md`, but appear as issue 5.5 in `docs/implementation-backlog.md` (marked P2). Resolve scope before building.

## Scope traps to avoid
- No second-exam support until DVA-C02 flow is complete.
- No interactive onboarding agent feed in V1 (status display only).
- No notes feature in V1 (explicitly out of scope).
- No Coach agent, Gap Tracker, Boss Battles, RAG, or spaced repetition in V1.

## Hard workflow rules
- No code file may exceed 200 lines. Split before continuing if approaching the limit.
- Commit every change immediately after it is made. Do not batch unrelated edits.

## Communication style - IMPORTANT!

Please keep explanations extremely minimal. I don't want too much talk and won't need explanations of what you did, except I ask.

## Diff-first output

### Core behavior

- Return changes as *unified diffs* (`diff -u` format) by default.
- Never rewrite an entire file unless the change touches more than 60% of it.
- When a full rewrite is genuinely required, say so in one sentence before the block.

### Diff format

Use standard unified diff headers:

```diff
--- a/path/to/file
+++ b/path/to/file
@@ -L,N +L,N @@
-removed line
+added line
 unchanged context line
```

Include 3 lines of context above and below each chunk. Use the real file path, not a placeholder.

### Output rules

- No preamble ("Here's what I changed...", "I'm going to...", "This update will...", etc).
- No step-by-step narration during generation.
- No `Explanation:` section after the diff unless explicitly asked with `explain:`.
- One short comment is allowed inside a diff hunk if the change is non-obvious - use the language's inline comment syntax on the `+` line itself.

### When to use prose instead of diffs

Only respond in prose (no diffs) when:

- The user asks a question (`?` present or clearly interrogative).
- The user uses `explain:` or `why:` as a prefix.
- No existing file is being modified (net-new file creation).

For new files, output a fenced code block with the language tag, no diff header needed.

### Trigger words

The user can override this behavior per message:

- `explain:` - provide a prose explanation of the change instead of a diff.
- `full:` - return the complete file instead of a diff.
- `why:` - explain the reasoning behind a change in prose.
- `handing off` - summarize the problem and your solution in one or two sentences; the user needs the input to start a new conversation or context window.

### Token discipline

- Keep responses minimal. If the diff speaks for itself, stop there.
- Do not summarize what the diff already shows.
- Avoid restating the user's request back to them.
- When running tests, linting, or type checks, call the underlying runner directly via RTK (for example, in `app/frontend`, `rtk vitest --run --environment jsdom`).
- Reference individual package folders for the respective `AGENTS.md` instructions.
