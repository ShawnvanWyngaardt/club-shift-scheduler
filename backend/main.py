"""API entry point for the Club Shift Scheduler: builds the app from its routers."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models import Health
from routers import clubs, demo, members, outcomes, schedule

app = FastAPI(title="Club Shift Scheduler", version="0.1.0")

app.include_router(clubs.router)
app.include_router(members.router)
app.include_router(schedule.router)
app.include_router(outcomes.router)
app.include_router(demo.router)


@app.get("/api/health", tags=["health"])
def health() -> Health:
    """Lets us (and the host) check the server is running."""
    return Health(status="ok")


# ---------- The built Vue app ----------
# Registered last on purpose: the catch-all route below would otherwise swallow API calls.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str) -> FileResponse:
        """Every non-API URL gets the Vue app; Vue Router decides what to show."""
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file = (FRONTEND_DIST / full_path).resolve()
        if full_path and file.is_file() and FRONTEND_DIST in file.parents:
            return FileResponse(file)
        return FileResponse(FRONTEND_DIST / "index.html")
