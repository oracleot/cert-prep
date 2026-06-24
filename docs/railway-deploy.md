# Railway Deployment Guide

This repo deploys to Railway as **two app services** plus **managed Postgres** and **managed Redis**:

| Service | Source | Builder | Port | Health check |
| --- | --- | --- | --- | --- |
| Next.js frontend | repo root | Nixpacks via `railway.toml` | `3000` | `GET /api/health` |
| Agents API | `agents/` | Docker via `agents/railway.toml` + `agents/Dockerfile` | `8000` | `GET /health` |
| Postgres | Railway managed DB | Railway | n/a | Railway managed |
| Redis | Railway managed Redis | Railway | n/a | Railway managed |

The frontend talks to the Python agents service over Railway internal networking through `LANGGRAPH_URL`.

## 1. What Railway should contain

Create one Railway project with these four services/resources:

1. **Frontend** — the Next.js app from the repo root
2. **Agents** — the FastAPI/LangGraph service from the same repo
3. **Postgres** — Railway managed Postgres
4. **Redis** — Railway managed Redis

Keep the app split exactly this way. The agents service is a separate HTTP service, not an in-process Next.js dependency.

## 2. Before you start

You will need:

- this GitHub repo connected to Railway
- an `OPENROUTER_API_KEY`
- Railway Postgres provisioned
- Railway Redis provisioned

Safe local reference values live in `.env.example`:

- `DATABASE_URL=postgresql://gauntlet:gauntlet@localhost:5432/gauntlet`
- `REDIS_URL=redis://localhost:6379`
- `LANGGRAPH_URL=http://localhost:8000`

## 3. Frontend service setup

Create a Railway service from this repo for the frontend.

Railway should use the repo root `railway.toml`:

- builder: `NIXPACKS`
- build command: `npm install && npm run build`
- health check: `/api/health`
- restart policy: `ON_FAILURE`
- deploy strategy: `duplicate`

### Frontend env vars

Set these on the **frontend** service:

| Variable | Required | Value |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | your OpenRouter key |
| `DATABASE_URL` | yes | Railway Postgres connection string |
| `REDIS_URL` | yes | Railway Redis connection string |
| `LANGGRAPH_URL` | yes | agents internal URL, e.g. `http://<agents-service>.railway.internal:8000` |
| `NODE_ENV` | yes | `production` |

Notes:

- `LANGGRAPH_URL` is for **Next.js → agents** calls.
- The frontend also boots the BullMQ worker through `instrumentation.ts`/`lib/queue.ts`, so it needs `REDIS_URL` too.
- `/api/health` reports `langgraph_configured` only when `DATABASE_URL` and `LANGGRAPH_URL` are both present.

## 4. Agents service setup

Create a second Railway service from the same repo for the Python agents API.

Railway should use `agents/railway.toml`:

- builder: `DOCKERFILE`
- dockerfile path: `agents/Dockerfile`
- health check: `/health`
- restart policy: `ON_FAILURE`
- deploy strategy: `duplicate`

`agents/Dockerfile` copies both `agents/` and `migrations/` into the image so startup migrations can run inside Railway.

### Agents env vars

Set these on the **agents** service:

| Variable | Required | Value |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | yes | your OpenRouter key |
| `DATABASE_URL` | yes for production | Railway Postgres connection string |

Current code does **not** require `REDIS_URL` or `LANGGRAPH_URL` on the agents service.

Notes:

- `OPENROUTER_API_KEY` is startup-critical: `agents/main.py` raises if it is missing.
- If `DATABASE_URL` is missing or broken, current code falls back to in-memory persistence. Do **not** rely on that on Railway; set the real Railway Postgres URL.
- Redis is currently consumed by the Next.js service worker, not by the agents process itself.

## 5. Managed Postgres and Redis

### Postgres

Attach Railway Postgres and copy its connection string into:

- frontend `DATABASE_URL`
- agents `DATABASE_URL`

Why both services get it:

- agents uses it for application tables and the LangGraph checkpointer
- frontend health checks expect `DATABASE_URL` to be configured

### Redis

Attach Railway Redis and copy its connection string into:

- frontend `REDIS_URL`

Why the frontend gets it:

- `lib/queue.ts` runs BullMQ inside the Next.js server process
- onboarding/background jobs depend on that worker being able to connect to Redis

## 6. Internal service-to-service URL

Set frontend `LANGGRAPH_URL` to the agents service's **internal** Railway URL, not the public URL.

Use the Railway internal hostname/port for the agents service, for example:

```text
http://<agents-service>.railway.internal:8000
```

The important rule is:

- **frontend uses `LANGGRAPH_URL` to call agents**
- **agents does not self-reference `LANGGRAPH_URL`**

You do not need to expose the agents service publicly just for frontend-to-backend calls.

## 7. Startup, migrations, and persistence behavior

On agents startup, `agents/main.py` does this in its lifespan:

1. validates `OPENROUTER_API_KEY`
2. opens the Postgres pool
3. initializes the LangGraph checkpointer
4. runs SQL migrations from `migrations/`
5. runs `setup_checkpointer_tables()`
6. seeds exam artifacts

Operationally important details:

- `run_migrations()` applies every `migrations/*.sql` file in lexical order
- migrations are intended to be idempotent
- `setup_checkpointer_tables()` is a deliberate workaround for `langgraph-checkpoint-postgres==2.0.3`
- do not remove or bypass that workaround in deploy changes

This means you do **not** need a separate Railway migration job for the current app. The agents service handles schema setup on boot.

## 8. Deploy order

Recommended order:

1. create Postgres
2. create Redis
3. deploy agents with `OPENROUTER_API_KEY` and `DATABASE_URL`
4. copy the agents internal URL into frontend `LANGGRAPH_URL`
5. deploy frontend with `OPENROUTER_API_KEY`, `DATABASE_URL`, `REDIS_URL`, and `LANGGRAPH_URL`

If the frontend comes up before `LANGGRAPH_URL` is set correctly, health stays up but app flows that proxy to the agents service will fail.

## 9. Verification checklist

After deploy, verify all of this:

### Frontend

- `GET /api/health` returns `200`
- response includes:
  - `status: "ok"`
  - `database_configured: true`
  - `langgraph_configured: true`

### Agents

- `GET /health` returns `200`
- response includes:
  - `status: "ok"`
  - `openrouter_configured: true`
  - `database_configured: true`

### Functional checks

- frontend can load without server boot errors
- an onboarding/session request that proxies through Next.js reaches the agents service successfully
- background job flows that depend on BullMQ do not fail on Redis connection errors
- agents logs do not show migration or checkpointer setup failures

## 10. Troubleshooting

### Frontend health says `langgraph_configured: false`

Usually one of these is wrong on the frontend service:

- `DATABASE_URL` missing
- `LANGGRAPH_URL` missing

### Frontend API routes fail talking to agents

Usually one of these is wrong:

- `LANGGRAPH_URL` points to the wrong host
- `LANGGRAPH_URL` uses a public URL instead of the Railway internal URL
- agents service is unhealthy

### Agents boot but persistence is degraded

If agents logs mention missing `DATABASE_URL` or Postgres connection failures, the service can fall back to in-memory state. That is not production-safe; fix the Railway Postgres wiring.

### Agents health says `openrouter_configured: false`

`OPENROUTER_API_KEY` is missing on the agents service.

### Background jobs fail

Check frontend `REDIS_URL`. The BullMQ worker lives in the Next.js process, so Redis problems show up there first.

## 11. Local parity

Local development matches the Railway shape closely:

```bash
cp .env.example .env.local
docker compose up -d
npm install
npm run dev
cd agents && pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Local defaults map to:

- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- agents URL for frontend: `http://localhost:8000`

That is the same four-part topology as Railway, just with Docker Compose instead of Railway managed services.

## 12. Release review points

Before marking a Railway deploy change ready, double-check:

- frontend and agents are still documented as separate services
- frontend `LANGGRAPH_URL` points to agents internal networking
- frontend still gets `REDIS_URL`
- both services still get `DATABASE_URL`
- agents startup migrations/checkpointer behavior is described accurately
- health endpoints match `railway.toml` and `agents/railway.toml`
