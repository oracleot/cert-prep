# Tech Stack
Status: locked | Date: 2026-06-15

## Stack at a Glance

| Concern | Decision | Rationale |
|---------|----------|-----------|
| Frontend framework | Next.js | App Router, PWA support, SSE-friendly, dominant React meta-framework |
| UI components | shadcn/ui | Unstyled primitives, fully ownable, no vendor lock-in |
| Agent orchestration | LangGraph (Python) | Hierarchical subgraphs, Postgres checkpointer, user wants to learn it deeply |
| Database | Postgres | Relational, mature, powers LangGraph checkpointer, pgvector-ready for v1.1 |
| Hosting / infra | Railway | Simple multi-service deployment, Postgres managed, Redis managed |
| Auth | Clerk | Adds in Phase 4 — not before |
| LLM routing | OpenRouter | Multi-provider, cost/quality flexibility, single API key for all models |
| Job queue | BullMQ + Redis | Background agent tasks (Blueprint Scout, Curriculum Builder) |
| Streaming | SSE (Server-Sent Events) | Stream LLM responses to frontend; simpler than WebSockets for this use case |
| Vector search | pgvector (Postgres extension) | Deferred to v1.1 for RAG pipeline |
| Web search | Tavily or Serper API | Blueprint Scout scraping (Phase 3+) — not needed in Phase 1–2 |
| Platform | Web-first, PWA | No native apps until post-validation |

## LLM Model Assignments (via OpenRouter)

| Agent | Model | Input $/1M | Output $/1M | Rationale |
|-------|-------|-----------|------------|-----------|
| Onboarding Agent | `anthropic/claude-haiku-4.5` | $1.00 | $5.00 | Best warmth + conversational quality at mid cost |
| Blueprint Scout | `openai/gpt-4.1` | $2.00 | $8.00 | Best-in-class tool use + structured extraction |
| Resource Gatherer | `deepseek/deepseek-v4-flash` | $0.09 | $0.18 | Runs constantly — near-zero cost, 1M context |
| Curriculum Builder | `anthropic/claude-sonnet-4.6` | $3.00 | $15.00 | Reasoning-heavy one-shot task, quality worth paying for |
| Rex | `anthropic/claude-sonnet-4.6` | $3.00 | $15.00 | Core product quality — cannot compromise |
| Sage | `anthropic/claude-sonnet-4.6` | $3.00 | $15.00 | Accuracy non-negotiable |
| Coach | `meta-llama/llama-3.3-70b-instruct` | $0.10 | $0.32 | Template-driven output, near-zero cost |
| Gap Tracker | `deepseek/deepseek-v4-pro` | $0.44 | $0.87 | Strong analytical MoE, background task |

**Estimated cost per session:** ~$0.054 (Rex + Sage account for ~98% of cost)

**Post-MVP A/B test candidate:** `x-ai/grok-4.20` ($1.25/$2.50, 2M ctx) as Rex/Sage alternative. Only 2× output cost multiplier vs Claude's 5× — could cut session cost ~60% if quality holds.

## Provider Abstraction Map

| Concern | Interface (proposed) | Current Provider | Swap scenario |
|---------|---------------------|-----------------|---------------|
| LLM calls | `LLMProvider` | OpenRouter | Switch to direct Anthropic/OpenAI if OpenRouter has reliability issues |
| Web search | `SearchProvider` | Tavily or Serper | Either provider — swap without changing Business logic |
| Auth | `AuthProvider` | Clerk | Deferred concern; add abstraction at Phase 4 integration |
| Job queue | `JobQueue` | BullMQ + Redis | Could swap to Railway-native jobs if BullMQ adds complexity |
| Streaming | `StreamTransport` | SSE | WebSockets if bidirectional comms ever needed |

## Monorepo / Project Structure
```
cert-prep/
├── app/              # Next.js frontend (App Router)
│   ├── (auth)/       # Clerk-protected routes (Phase 4)
│   ├── session/      # Session screen
│   ├── dashboard/    # Dashboard
│   └── onboarding/   # Onboarding flow
├── agents/           # Python LangGraph backend
│   ├── graphs/       # Parent graph + subgraphs
│   ├── nodes/        # Individual node implementations
│   ├── state.py      # AppState TypedDict
│   └── prompts/      # Agent system prompts
├── lib/              # Shared utilities
├── docs/             # Build-ready docs (this directory)
└── ...
```

*Note: Python backend runs as a separate Railway service. Next.js calls it via internal API. In Phase 1, the Python backend may not exist — raw OpenRouter calls from Next.js API routes first.*

## Local Dev Setup

```
# Prerequisites
- Node.js 20+
- Python 3.11+
- Docker (for local Postgres + Redis)

# Setup
git clone <repo>
cp .env.example .env.local          # fill in OPENROUTER_API_KEY
docker compose up -d                # starts Postgres + Redis
cd agents && pip install -r requirements.txt
npm install
npm run dev                         # Next.js on :3000
cd agents && python -m uvicorn main:app --reload  # LangGraph API on :8000
```

**Phase 1 exception:** no Docker needed — Phase 1 is a single Next.js page with raw OpenRouter calls. Full setup above applies from Phase 2 onwards.

**Required env vars:**
- `OPENROUTER_API_KEY` — from Phase 1
- `DATABASE_URL` — from Phase 2
- `REDIS_URL` — from Phase 2
- `CLERK_SECRET_KEY` + `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` — from Phase 4

## One-Way Doors
Decisions that are costly to reverse — confirmed deliberately:

| Decision | Why irreversible |
|----------|-----------------|
| LangGraph as orchestration layer | State typing, checkpointer, and graph structure deeply coupled by Phase 2. Migration = rewrite of entire agent layer. |
| Postgres as primary DB | LangGraph checkpointer is Postgres-coupled. Swapping DB means replacing checkpointer too. |
| Card-based session UI | The product's UX identity. Pivot to chat/quiz = product redesign, not refactor. |
| SSE for streaming | Switching to WebSockets mid-build requires changes on both server and client. |

## Two-Way Doors
Decisions that can be swapped cheaply later:

| Decision | Why swappable |
|----------|--------------|
| OpenRouter vs direct Anthropic/OpenAI | Single config change behind `LLMProvider` |
| Tavily vs Serper | Swap `SearchProvider` implementation |
| Railway vs other hosting | Infrastructure concern, no code change |
| Individual shadcn/ui components | Unstyled primitives, replaceable without cascading changes |
| Rex/Sage model choice | Prompt + model ID, easily A/B tested |

## V1 Exclusions
- Native iOS/Android apps
- pgvector / RAG pipeline
- Real-time multi-user features
- Any exam beyond DVA-C02 (Phase 3+)
- Clerk auth (Phase 4 — not Phase 1–3)
