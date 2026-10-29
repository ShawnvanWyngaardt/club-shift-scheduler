# Build journal

One entry per working day. Each entry: what I built, one decision and why, what went wrong, what I learned.

## Sun 18 Oct 2026: choosing and planning

- **Planning & Setup:** Started planning on project, decided what to build and why. Also made sure everything was set up correctly before I got started.
- **Built:** nothing yet, on purpose. Chose the project, wrote the plan, set up the tools and the repo.
- **Decision:** a volunteer shift scheduler for amateur sports clubs, chosen over several other ideas because the interesting part (gamification: a fair scheduling algorithm) is real Python work according to my research via Claude. FastAPI over Django, because the aim was learning Python itself, not a framework's conventions.
- **Decision:** planned before building: problem, definition of done, systems view of how people might game the points, data model, day-by-day plan with a cut list.
- **Went wrong:** small things. Git was set to my personal email for a public repo; switched to a deliberate choice before the first push.
- **Learned:** writing the "not this week" list was as useful as the plan itself.
- **Thoughts:** How I felt starting out... eager, unsure but confident, building my first real side project was daunting but seeing that I had always just worked on things within a company/business context, it was a breath of fresh air. All the other repos in my GitHub are just assessments for job applications and don't carry much weight. Looking forward to how this all works out.

## Mon 19 Oct 2026: Python basics, first API, first deploy

- **Built:** FastAPI skeleton with a health endpoint, deployed live on Render. In the afternoon spent more time on the rest of the endpoints for members, clubs and shifts. Testing still to be done on the latter. Python exercises (dataclasses, validation, comprehensions). Then the database models and endpoints for clubs, members, shift types and shifts.
- **Decision:** Root directory set to `backend` so Render finds `uv.lock` and uses uv. Also decided to lean more on claude for the backend, while I'm still learning.
- **Decision:** three models per thing (create, table, public), so clients can never set ids or see other people's tokens.
- **Decision:** build with AI assistance openly, marking code as boilerplate or must-understand, and document it in the README.
- **Snag:** uv created a package layout I didn't want, so I redid it with the app layout. VS Code used the wrong Python and showed false errors. Render's free tier wanted card verification and my bank flagged the $1 check; the card was accepted anyway.
- **Learned:** Via scratch.py >>> Dataclasses, `__post_init__` validation, comprehensions vs generators, why mutable defaults break. How to set up endpoints in Python with classes. Why `= []` as a dataclass default is a trap, how to read a traceback bottom-up, and that a terminal only sees PATH changes after a restart.
- **AI collaboration:** Made use of Claude to validate assumptions and troubleshoot where my knowledge and experience was lacking.

## Tue 20 Oct 2026: the solver

- **Built:** a greedy scheduling solver as a plain-Python module, with seven tests, and GitHub Actions running them on every push.
- **Decision:** the solver knows nothing about the database. Each hard rule is its own function, so a different rule set (for example, for businesses) can be added later without rewriting it.
- **Decision:** moved the CP-SAT solver (Thank you AI) to the stretch list after a slow start to the day.
- **Went wrong:** VS Code couldn't resolve imports in the tests until I pointed it at the backend folder.
- **Learned:** mutation testing. I changed `min` to `max` on purpose, predicted which two tests would fail, and got it right.

## Wed 21 Oct: availability, scheduling and the ledger

- **Built:** members setting availability through personal links; generate (preview) and publish (save) for schedules; recording done or no-show, with an append-only points ledger.
- **Decision:** generate and publish are separate, so the coordinator always previews before anything is saved.
- **Decision:** a status change and its ledger entry are saved in one transaction, so the ledger can never disagree with the assignments.
- **Went wrong:** lost half the day to family commitments; finished the ledger in the evening anyway.
- **Learned:** PUT requests, composite primary keys, and why 409 is the right answer to "already recorded".

## Thu 22 Oct: Postgres, security and a busy day

- **Built:** switched production to PostgreSQL on Neon; protected coordinator actions with a coordinator token; wrote a seed script for demo data.
- **Decision:** reads stay open, writes need the coordinator token. Transparency is part of the product.
- **Went wrong:** I added the database setting on Render before merging the code that understood it, and the live site went down until the merge. Lesson: ship the code that understands a setting before switching the setting on.
- **Learned:** configuration belongs in environment variables, never in git; 403 versus 422; constant-time token comparison.

## Fri 23 Oct: designing the frontend, finishing the backend

- **Built:** a frontend plan with user-flow diagrams for members and coordinators; the backend changes those flows required; API tests; the Vue project and the first real screen, the member page.
- **Decision:** designed the flows before writing any Vue. Doing that showed three things a member couldn't see (their name, their balance, their assigned shifts), which the backend then had to provide.
- **Went wrong:** tests failed on times without a timezone. Claude Code traced it and fixed it, and I added a round-trip test so it can't quietly come back.
- **Learned:** store times in UTC and convert only at the edges. The October clock change sits between the two seeded Saturdays, and a test now covers it.

## Sat 24 Oct: going live with the frontend

- **Built:** the Vue app built and served by the same Render service as the API; frontend tests and build in CI; the coordinator screens for scheduling and recording outcomes.
- **Decision:** one service and one URL. Node only runs at build time; FastAPI serves the built files.
- **Decision:** the schedule screen puts unfilled slots first, and its copy is honest that gaps can't be refilled after publishing yet.
- **Went wrong:** pasted a member token where the database connection string belonged, and ended up with several copies of the demo club. Wiped the demo data cleanly and reseeded once.
- **Learned:** the difference between a connection string and an access token, the hard way.

## Sun 25 Oct: the real test

- **Built:** no new features. Fixed deployment and ran the first real test.
- **Went wrong:** a frontend-only merge never deployed, because Render only watches the service's root directory (`backend`). Fixed with build filters for both folders.
- **Tested:** my first tester used the member page on her phone while I coordinated on the laptop; I also ran it myself on an old phone and on desktop.

### User test: what she understood straight away

- The purpose, with no explanation from me: as a member she has to take part in shifts and tell the coordinator her availability, and the app gives the coordinator "a neat (and live) oversight of which shifts has been filled by which member, and which shifts are yet to be filled."
- That the least popular shift earns the most points.

### User test: what she saw and did

- **Pre-ticked shifts read as the app's choice.** The field setup shifts were already ticked, and she read them as "automatically selected", something she would have to untick if she didn't want it. In fact they were the seed script's sample availability for her member, but the page never says that ticks are her own saved answers.
- **An assigned shift read as an order.** The youth referee shift was already assigned to her, and she took it as compulsory.
- **Assigned shifts show no points.** She could see the points for the shifts she could still choose, but not for the one she'd been given.
- **Points didn't change her choice.** The 07:00 bar shift earns the most, and it would still be "the last one that I would choose". She kept it unticked and kept the field setup shifts.

### User test: what she thought happened

- She assumed the coordinator had compared members by hand, seen that nobody chose the youth referee shift, and picked her as someone who had done the least and never volunteered for it. In reality the solver assigned it automatically, from her availability and her low points balance. **The app never explains why a shift was given to her**, so she filled the gap with a story about a person deciding.

### User test: after the outcome was recorded

- "I don't see anything different this time around." I had marked her shift done, which added points, but her page didn't make the change visible enough to notice.

### User test: her verdict

- She would change nothing.
- She would rather use the app than a WhatsApp group. She already keeps up with several group chats and apps for school and family activities, and an app for shifts means no debate about who does what, and nothing for "that one member who always complains" to complain about.

### User test: what I found

- TBD

### Takeaways

- "Nothing I would change" and the observations above say different things. She found no bugs, but four places where the app doesn't explain itself: pre-ticked answers, assignments, points on assigned shifts, and outcomes.
- Points alone didn't change her behaviour. One user isn't proof, but it questions the assumption that the reward motivates; fairness may come from the priority rule rather than from people chasing points.
- The problem is real to her: the strongest validation in the test is that she'd prefer this to the group chat.

- **Anything to fix for v0.1.0:** no. Everything worked as built; the findings are about understanding, not bugs, so they move to v0.2.0.
- **What moves to v0.2.0:**
  - Explain each assignment on the member page, for example "You said you could, and you have the fewest points."
  - Show points on assigned shifts too.
  - Show outcomes on the member page: done or no-show, and the points it added, with the new balance.
  - Make clear that ticks are the member's own saved answers.
  - Revisit whether points motivate, or whether the priority rule is the real fairness mechanism; ask the next testers.

---

## Looking back on the week

- **What I'd do differently:** TBD
- **What surprised me:** TBD

---

## Wed 28 Oct: v0.2.0 begins, and production was closer than I thought

- **Built:** started v0.2.0 with database migrations. Installed Alembic, wired it to the app's own models and database connection, and generated the first migration from an empty local database. Removed create-tables-on-startup: the schema now only changes through migrations. Also replaced the default "Vite App" page title and favicon with the app's own.
- **Decision:** migrations before any new feature, because the first v0.2.0 feature adds columns to an existing table, and create-on-startup only ever creates missing tables. Alembic replaces it (decision 11).
- **Went wrong:** the first generated migration wanted to drop a table called `playing_with_neon` and created none of mine. That made no sense for a local database, so I stopped before applying it. The cause: `database.py` silently loaded a `.env.local` file that the Neon CLI had written to the repo root, so every local command (Alembic, the seed script, the dev server) had been talking to the production database by default. Checking the terminal showed nothing, because the connection string only existed inside Python.
- **Went wrong, nearly:** `.gitignore` only ignored `.env`, which doesn't match `.env.local`. The file had never been committed, but the next `git add .` would have put the database password in a public repo.
- **Fixed:** removed the automatic loading, so local development uses SQLite unless I deliberately point a terminal at Neon; ignored all `.env.*` files; regenerated the migration against an empty local database.
- **Learned:** a convenience added by a tool can quietly change where your commands run, so check what a tool writes into your project. Read a generated migration before applying it: the strange table name was the only clue anything was wrong. And an ignore pattern only protects you from the exact names it matches.
- **To-Do** The CI check, the Neon stamp and the Render start command are for the carried over to the next day of development.
