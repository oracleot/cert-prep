# AGENTS.md

## Repo Reality (current state)
- **Phase 1 is fully shipped.** `app/`, `lib/`, `components/`, `agents/state.py`, `agents/db.py`, `migrations/`, `docker-compose.yml` all exist. The "planning-only" claim in prior sessions is stale.
- Phase 2 Python service is partially scaffolded: `agents/state.py`, `agents/db.py`, and `agents/main.py` are implemented, while `agents/graphs/`, `agents/nodes/`, and `agents/routes/` are still empty `__init__.py` stubs.
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
cp .env.example .env.local      # fill OPENROUTER_API_KEY at minimum
docker compose up -d            # Postgres :5432, Redis :6379 (both named "gauntlet")
npm install && npm run dev      # Next.js on :3000
# Phase 2 only:
cd agents && pip install -r requirements.txt
python -m uvicorn main:app --reload  # target: :8000
```
- `npm run lint` runs ESLint (eslint-config-next, core-web-vitals + TypeScript).
- No typecheck script in package.json; run `npx tsc --noEmit` manually.
- No test command exists yet.

## Architecture: what's actually wired
- **Phase 1 loop (fully working):** `app/session/use-session.ts` orchestrates the full 2-cycle Rex→Sage loop via direct Next.js API routes (`/api/rex/challenge`, `/api/rex/rechallenge`, `/api/evaluate`, `/api/sage`). Domain hardcoded to `"Deployment"`, `MAX_CYCLES = 2` in `use-session.ts`.
- **OpenRouter clients:** `lib/openrouter.ts` (SSE streaming) and `lib/openrouter-json.ts` (structured JSON). The SSE client strips markdown fences before `JSON.parse` in the JSON client.
- **Agent prompts:** `agents/prompts/` has both `.ts` files (consumed by Next.js API routes now) and `.py` ports (for Phase 2 LangGraph). `sage.py` and `evaluator.py` Python ports do not exist yet.
- **Phase 2 foundations ready:** `agents/state.py` has the full `AppState` TypedDict with `Annotated[list[Exchange], operator.add]` for LangGraph additive state. `agents/db.py` has `AsyncPostgresSaver` setup.

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
