# Club Shift Scheduler

Amateur sports clubs in the Netherlands depend on members to volunteer their time during the season, on match days, at practices and at social events. That means helping with setup, transport, the bar and horeca at the clubhouse, and even organising children's games.

Work in progress, started week of 19 October 2026. Built with Python (FastAPI), Vue 3 and the support of many hot and cold beverages.

**Live demo:** https://club-shift-scheduler.onrender.com The free hosting tier sleeps when idle, so the first visit can take about a minute to load.

## The Problem

Today, coordinators mostly rely on WhatsApp groups and outdated Excel sheets, which means nobody really knows what's going on except the coordinator. And the same few members end up carrying the brunt of the work, while others skate by doing little or nothing.

## How it works

1. The coordinator posts shifts for the coming weeks. Each shift type has a weight from 1 to 3; unpopular shifts, like the early Saturday bar, weigh more.
2. Members open a personal link, with no account or password, and tick the shifts they can do. Each shift shows the points it earns.
3. The coordinator generates a schedule. A solver assigns shifts fairly: members with the fewest points this season go first. Unfilled slots are shown first, so the coordinator knows who to chase.
4. After the shifts happen, the coordinator marks each one done or no-show. That writes an entry in a points ledger.
5. The next schedule uses the new balances. People who take on the unpopular shifts earn priority later; people who skip them don't.

## Tech stack

| Layer        | Choice                                                    | Why                                                                  |
| ------------ | --------------------------------------------------------- | -------------------------------------------------------------------- |
| Backend      | Python, FastAPI, Pydantic                                 | Small and explicit; type hints give validation and API docs for free |
| Database     | SQLModel; SQLite locally, PostgreSQL (Neon) in production | Same models in both places                                           |
| Scheduling   | Plain-Python greedy solver with pluggable rules           | Testable without a database; each rule is its own function           |
| Frontend     | Vue 3, TypeScript, Vite, Vue Router                       | No component library: own design tokens and components               |
| Tests and CI | pytest, Vitest, GitHub Actions                            | Backend and frontend tests run on every push                         |
| Hosting      | Render (one service serves the API and the built Vue app) | One deploy, one URL                                                  |

## Key decisions

- **FastAPI over Django:** the goal was learning Python itself, and Vue owns the interface, so Django's templates and admin would have gone unused.
- **Personal links instead of accounts:** authentication would have taken the whole week. The trade-off: anyone with a link can use it.
- **Append-only points ledger:** balances are calculated from entries, never stored, so every balance can be explained line by line.
- **Times stored in UTC, shown in Amsterdam time:** caught by tests around the October clock change.

## Run it locally

You need Python 3.12 or newer, [uv](https://docs.astral.sh/uv/) and Node.js 24.

**Backend**, in one terminal:

```bash
cd backend
uv sync
uv run python seed.py          # creates a demo club and prints its links
uv run fastapi dev main.py     # API on http://127.0.0.1:8000, docs at /docs
```

**Frontend**, in a second terminal:

```bash
cd frontend
npm ci
npm run dev                    # app on http://localhost:5173
```

Open the links the seed printed:

- Member: `http://localhost:5173/m/<member token>`
- Coordinator: `http://localhost:5173/c/<club id>/<coordinator token>`

**Tests:** `uv run pytest` in `backend`, and `npm run test:unit -- --run` in `frontend`.

## Known limitations (on 25 October 2026)

- No setup screen yet: clubs, members and shifts are created with the seed script or the API.
- Gaps left open when a schedule is published can't be refilled through the app yet.
- Links work like passwords: anyone holding one can use it.
- No notifications; links are shared by hand, for example in WhatsApp.

## What's next

- Expand on the functionality and remove limitations
- Improve on the overall design and user experience in the coming week/s
- Make it possible to send links from the coordinator screen
- Shared scoreboard screen for members
- ....any suggestions welcome

### How this was built

Built over one week in October 2026 as a hands-on way to learn Python, with AI assistance (Claude and Claude Code) for explanations, code review and debugging. Every design decision is written down in [`docs/plan.md`](docs/plan.md), and the day-by-day progress, including what went wrong, is in [`docs/journal.md`](docs/journal.md).
