# Railway Deployment Guide

## Services

| Service | Builder | Port | Health endpoint |
|---------|---------|------|-----------------|
| Next.js frontend | Nixpacks (root `railway.toml`) | 3000 | `GET /api/health` |
| Agents LangGraph API | Dockerfile (`agents/Dockerfile`) | 8000 | `GET /health` |

Both services are provisioned as independent Railway services sharing managed Postgres and Redis instances.

## Provisioning Steps

1. Create a Railway project.
2. Add a **Postgres** database (note the connection string).
3. Add a **Redis** instance (note the connection string).
4. Connect the repo and add each service:
   - **Next.js**: repo root, Railway auto-detects Nixpacks → select the root `railway.toml`.
   - **Agents**: repo root, Railway auto-detects the `dockerfilePath = "agents/Dockerfile"` from `agents/railway.toml` and uses it automatically.
5. Set environment variables on each service (see below).
6. Deploy both services.

## Required Environment Variables

### Next.js (Frontend)

| Variable | Source | Notes |
|----------|--------|-------|
| `OPENROUTER_API_KEY` | OpenRouter dashboard | Required. Phase 1 needs this; without it the LLM calls fail. |
| `DATABASE_URL` | Railway Postgres | Required from Phase 2. Format: `postgresql://user:pass@host:5432/db`. |
| `LANGGRAPH_URL` | Railway internal | Agents service internal URL, e.g. `http://cert-prep-agents.railway.internal:8000`. Next.js uses this to proxy to `/api/sage`, `/api/rex`, etc. |
| `NODE_ENV` | Railway (auto) | Set to `production`. |
| `NEXT_PUBLIC_APP_URL` | Railway (manual) | Public URL of the Next.js service, e.g. `https://cert-prep-nextjs.up.railway.app`. Used for CORS origins. |

### Agents (FastAPI / LangGraph)

| Variable | Source | Notes |
|----------|--------|-------|
| `DATABASE_URL` | Railway Postgres | Same connection string as above. Agents raises `RuntimeError` at startup if absent. |
| `REDIS_URL` | Railway Redis | Format: `redis://user:pass@host:6379`. Used by BullMQ in Phase 2.5. |
| `OPENROUTER_API_KEY` | OpenRouter dashboard | Required for all agent LLM calls. |
| `LANGGRAPH_URL` | — | Not used by the agents service. Next.js sets this for its own internal routing to agents. |

## Service-to-Service Communication

On Railway, internal service URLs follow the pattern:
```
http://<service-name>.<project-name>.railway.internal:<port>
```

Next.js proxies agent requests to the internal `LANGGRAPH_URL`. No public exposure of port 8000 is required.

## Database Migrations

The agents service runs migrations automatically on startup via `agents/db.py:run_migrations()`. The `migrations/` directory is baked into the Docker image at build time (see `agents/Dockerfile`). Migrations use `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` for idempotency.

## Health Checks

- **Next.js**: `GET /api/health` returns `200` with `{"status": "ok", "database_configured": bool, "langgraph_configured": bool}`.
- **Agents**: `GET /health` returns `{"status": "ok", "openrouter_configured": bool, "database_configured": bool}`.

Both endpoints are used by Railway for liveness probing.

## Local Development with Railway Services

```bash
# Start managed Postgres + Redis via Docker Compose
docker compose up -d

# Copy env and fill in values
cp .env.example .env.local

# Override LANGGRAPH_URL for local agents
# LANGGRAPH_URL=http://localhost:8000

npm run dev         # Next.js on :3000
cd agents && python -m uvicorn main:app --reload  # Agents on :8000
```

## Rollback

Railway retains deploy history. To roll back a service, use the Railway dashboard or CLI:
```bash
railway up --service cert-prep-nextjs
railway rollback --deployment <id>
```
