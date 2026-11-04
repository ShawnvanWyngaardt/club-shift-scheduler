# Backend

FastAPI, SQLModel and Alembic. See the [main README](../README.md) for what the app does and how to run everything together.

## Run

    uv sync
    uv run alembic upgrade head
    uv run python seed.py      # optional: a demo club with links
    uv run fastapi dev main.py

Uses SQLite (`local.db`) unless `DATABASE_URL` is set. API docs at http://127.0.0.1:8000/docs.

## Check

    uv run ruff check .
    uv run ruff format --check .
    uv run pytest

## Where things are

- `main.py` builds the app and serves the built frontend
- `routers/` one file per area: clubs, members, schedule, outcomes, demo
- `solver.py` the greedy scheduler, pure Python with no database
- `scheduling.py` turns database rows into a solver problem and back
- `sandbox.py` demo clubs: creation, expiry and the cap
- `migrations/` Alembic; after changing `models.py`, run `uv run alembic revision --autogenerate -m "..."`
