"""API entry point for the Club Shift Scheduler."""
from fastapi import FastAPI

app = FastAPI(title="Club Shift Scheduler")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Lets us (and the host) check the server is running."""
    return {"status": "ok"}
