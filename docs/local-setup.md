# Local Setup Guide (Phase 2)

This guide walks you through setting up the Gauntlet application locally, specifically testing the Phase 2 LangGraph integration.

## Prerequisites
- Node.js 20+
- Python 3.10+
- Docker & Docker Compose
- An OpenRouter API Key

## 1. Environment Setup

Copy the example environment file:
```bash
cp .env.example .env.local
```

Open `.env.local` and add your OpenRouter API Key:
```env
OPENROUTER_API_KEY=your_key_here
```
*(Leave the `DATABASE_URL` and `REDIS_URL` as they are, they map to the local docker containers).*

## 2. Infrastructure Setup (Postgres & Redis)

Start the local database and redis queue using Docker Compose:
```bash
docker compose up -d
```

Verify that both containers are running and healthy:
```bash
docker compose ps
```

## 3. Python LangGraph Backend Setup

The AI logic is now driven by a Python FastAPI service running LangGraph.

1. Navigate to the `agents/` directory:
```bash
cd agents
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install the Python dependencies:
```bash
pip install -r requirements.txt
```

4. Apply the database migrations:
*(Make sure you are still in the `agents/` directory with the venv activated)*
```bash
python -c "import asyncio; from db import init_pool, run_migrations; asyncio.run(init_pool()); asyncio.run(run_migrations())"
```
*(Note: `main.py` automatically runs migrations and sets up LangGraph checkpointer tables on startup).*

5. Start the LangGraph API:
```bash
python -m uvicorn main:app --reload
```
The backend should now be running at `http://localhost:8000`. You can verify it by hitting `http://localhost:8000/health`.

## 4. Next.js Frontend Setup

1. Open a new terminal window at the root of the project.
2. Install Node dependencies:
```bash
npm install
```

3. Start the Next.js development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## 5. Testing the Application

1. Open `http://localhost:3000` in your browser.
2. The UI will automatically reach out to the Next.js API, which proxies to the LangGraph backend (`/session/start`) to generate a challenge.
3. Once the challenge appears, read the scenario and type your answer in the text box.
4. Click **Submit**.
   - Behind the scenes, Next.js calls `/api/session/submit`, proxying the answer to LangGraph.
   - LangGraph evaluates your answer and conditionally routes to the Sage agent.
   - The Sage response is streamed back in real-time using Server-Sent Events (SSE).
5. Review the Evaluation outcome and Sage's in-depth explanation or correction.
6. Click **Next Challenge** to run the next cycle in the loop.

Enjoy your learning session!
