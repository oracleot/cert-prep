# cert-prep

AI certification prep app (working name: Gauntlet). Phase 9 shipped; Phase 2 LangGraph + state persistence is long complete.

## Stack
- Next.js (App Router, shadcn/ui) on `:3000`
- Python LangGraph service (FastAPI) on `:8000`
- Postgres + Redis via Docker Compose

## Quick start

### 1. Env vars
```bash
cp .env.example .env.local
```
Fill in `OPENROUTER_API_KEY`. The defaults for `DATABASE_URL` and `REDIS_URL` match the compose stack.

### 2. Start Postgres + Redis
```bash
docker compose up -d
```
- Postgres → `localhost:5432` (db: `gauntlet`, user: `gauntlet`, pass: `gauntlet`)
- Redis → `localhost:6379`

Check health: `docker compose ps` (both should show `healthy`).

### 3. Install + run
```bash
# Frontend
npm install
npm run dev                                  # :3000

# Backend (in another shell)
cd agents
pip install -r requirements.txt
python -m uvicorn main:app --reload          # :8000
```

### 4. DB migrations
Migrations live in `migrations/` and are applied automatically by the agents service on startup, along with LangGraph checkpointer table setup.

No manual `psql` step is required for normal local or Railway boot.

## Endpoints
- `GET http://localhost:3000` — Next.js UI
- `GET http://localhost:8000/health` — LangGraph service health
