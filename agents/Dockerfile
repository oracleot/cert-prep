# Agents service — FastAPI + LangGraph
# Build context is the repo root so we can COPY both agents/ and migrations/.

FROM python:3.11-slim

WORKDIR /app/agents



# Install Python deps
COPY agents/requirements.txt /app/agents/requirements.txt
RUN pip install --no-cache-dir -r /app/agents/requirements.txt

# Copy agents source
COPY agents/ /app/agents/

# Copy migrations so agents/db.py:run_migrations() can apply them.
# agents/db.py resolves MIGRATIONS_DIR = PROJECT_ROOT / "migrations"
# where PROJECT_ROOT = Path(__file__).resolve().parent.parent
COPY migrations/ /app/migrations/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
