# AGENTS.md

## Repo Reality (current state)
- This repository is planning-only right now: only `docs/*.md` exist, with no app code, manifests, lockfiles, CI workflows, or runnable test/lint/typecheck setup yet.
- Do not claim commands were run unless you first create the relevant toolchain files.

## Source of truth order
- Prefer executable config/code over docs whenever code exists.
- In the current planning-only state, use this order:
  1. `docs/implementation-backlog.md` (issue-level acceptance criteria)
  2. `docs/tech-stack.md` (locked stack and env/infra plan)
  3. `docs/ux-flows.md` (UI behavior, edge/error states)
  4. `docs/tracker.md` (what is complete vs draft, key constraints)

## Phase guardrails (high-risk mistakes)
- Phase 1 is only Rex+Sage loop validation; do not add infra/auth/LangGraph yet.
- Phase 1 uses direct OpenRouter calls from Next.js.
- LangGraph + Postgres checkpointer start in Phase 2.
- Keep DVA-C02 hardcoded for early phases; no multi-exam generalization in V1.
- Clerk auth is Phase 4, not earlier.
- User intent is to learn LangGraph deeply: keep graph structure/state/edges explicit, not hidden behind heavy abstractions.

## Planned dev runbook (to match when scaffolding)
- Frontend dev server target: `npm run dev` on `:3000`.
- Python agents service target: `cd agents && python -m uvicorn main:app --reload` on `:8000`.
- Local infra target: `docker compose up -d` for Postgres (`:5432`) and Redis (`:6379`).
- Planned setup order in docs: env file -> Docker services -> Python deps -> Node deps.
- Planned env vars by phase: `OPENROUTER_API_KEY` (Phase 1), `DATABASE_URL` + `REDIS_URL` (Phase 2), Clerk keys (Phase 4).

## Known doc conflicts to resolve before implementation
- Boss Battles are marked deferred to v1.1 in `docs/tracker.md` and `docs/product-spec.md`, but appear in Phase 5 backlog items. Resolve scope before building.

## Scope traps to avoid
- Do not add second-exam support before DVA-C02 flow is complete.
- Do not make the onboarding agent feed interactive in V1 (status display only).
- Do not add a notes feature in V1 (explicitly out of scope).

## Hard workflow rules
- Hard rule: no code file may exceed 200 lines. If a file approaches 200 lines, split logic into smaller modules before continuing.
- Hard rule: commit every change immediately after it is made. Do not batch unrelated edits into one commit.
