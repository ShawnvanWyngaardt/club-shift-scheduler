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

## Thu 29 Oct: from migrations to a demo anyone can try

- **Built:** finished the move to Alembic: CI now checks that models and migrations agree, Neon was stamped at the current version, and Render runs migrations on every deploy. Then four sessions in one day: a landing page at the root URL, `main.py` split into routers, a demo sandbox backend, and the "Try the demo" button with a step-by-step guide on the coordinator screen.
- **Decision:** built the landing page before the router split, swapping two planned sessions. It needed no backend work and fixed the first thing every visitor saw: "Page not found".
- **Decision:** every visitor gets their own sandbox club, deleted after 24 hours, with a member called "You" who starts with nothing ticked. A shared demo would break the moment one visitor published a schedule. Starting "You" with no answers also responds to the first user test, where pre-ticked shifts read as the app's choice.
- **Decision:** logged decisions 11 (Alembic migrations, replacing tables-on-startup) and 12 (times stored timezone-aware, shown in Amsterdam time), and put snapshots of all three plans and their diagrams into `docs/`.
- **Went wrong:** saved the new Render start command before merging the code that installed Alembic, so the deploy failed until the merge. The same lesson as on 22 October: ship the code before the setting that depends on it.
- **Went wrong, caught in time:** the generated migration set a boolean default as the number `0`. SQLite accepts that, Postgres doesn't, so it would have passed every local test and failed on deploy. Changed it to `sa.false()`, which each database writes its own way.
- **Went wrong:** a cleanup test failed because SQLite reused a deleted club's id for the next club, so the test found the new club and thought the old one survived. Postgres never reuses ids. Fixed the test to look the club up by its token, which is also why stale links can never open someone else's club.
- **Learned:** how Python packages and imports work across files, FastAPI routers, `server_default` for adding columns to tables that already have rows, and that SQLite and Postgres differ in ways local tests can't show.

## Fri 30 Oct: real clubs without the seed script

- **Built:** "Start a club" from the landing page, with a one-time screen to save the coordinator link, and a Setup tab where coordinators add members and send each one their link with Copy or Share on WhatsApp. Behind it, a coordinator-only endpoint that lists members with their links.
- **Decision:** member tokens only appear behind the coordinator token, never in the public members list. A test checks both sides of that boundary.
- **Decision:** no accounts means no way to recover a lost coordinator link, so the app says so plainly at the one moment it matters, with a copy button and an "I've saved it" step.
- **Decision:** split the session into a backend and a frontend pull request, so a busy day could stop after either one without leaving work half-done.
- **Tidied:** one file for all link builders, and deleted old merged branches locally and on GitHub.
- **Noticed:** VS Code's Problems tab had a mix of real issues and false alarms, and nothing enforced code style. The plan had listed Ruff since day one, but it was never set up; it's the next thing to add.

## Mon 2 Nov: setup complete, and linting that bites

- **Built:** Ruff for the backend and oxlint plus ESLint for the frontend, now enforced in CI. Then the rest of the Setup tab: shift types with their points, and shifts that can repeat weekly. The backend gained safe deletes for members, shifts and shift types.
- **Decision:** linting runs in CI without auto-fixing, so a problem fails the build instead of being quietly changed. The one-off formatting pass went into its own commit, so it doesn't hide real changes.
- **Decision:** weekly shifts repeat in Amsterdam time, not UTC, so a 07:00 shift stays 07:00 after the clocks change. A test pins it to the real dates around 25 October.
- **Decision:** deletes refuse instead of cascading. A member with points stays, because the ledger is append-only; a scheduled shift stays, because someone was told to turn up. Each refusal returns a reason.
- **Decision:** split the Setup page into three components (members, shift types, shifts). The page loads the shift types once and passes them down; the sections tell it when something changed.
- **Went wrong, caught by the linter:** VS Code had auto-imported `server` from the TypeScript package into the Vite config when I typed a `server:` setting. Unused, and the first thing oxlint flagged.
- **Went wrong:** successful deletes looked like errors, because the frontend tried to read a response body from a 204 reply that has none. Fixed in the shared request function, which now also shows readable validation messages.
- **Learned:** never build shift times with the browser's own timezone: a visitor in London would create shifts an hour off. The frontend now converts from Amsterdam time explicitly, with a test on both sides of the clock change.
- **Noticed for the UX review:** the browser's confirm dialogs don't belong to the app's interface, and "Remove this type's shifts first" says what the system refuses but not why or what to do. Parked in `docs/v2-ideas.md` for the redesign.
- **TBD:** Add `docs/v2-ideas.md`...

## Tue 3 Nov: the member side answers back

- **Built:** session 8, refill only the open slots of a partly filled shift, and hide past shifts from members and the solver. Existing assignments now count towards overlaps and load, so a refill never double-books anyone.
- **Built:** session 9, the schedule screen shows who already holds each shift, what still needs people, and a preview that marks the newly added people.
- **Built:** session 10, member tabs straight from the user test findings: "My answers" (availability), "My shifts" (coming up, past outcomes, how the points were earned) and "Club points".
- **Built:** rewrote the "How this was built" section of the README.

### From finding to fix

| What my first tester saw                                | What changed                                                                                                       |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Saved ticks read as "automatically selected"            | The tab is now "My answers", with copy saying these are her answers, not a schedule                                |
| An assigned shift read as an order from the coordinator | Each upcoming shift says "Why you: you said you could do this shift, and members with the fewest points go first." |
| Assigned shifts showed no points                        | Points shown on every shift, assigned or not                                                                       |
| "I don't see anything different" after an outcome       | Past shifts show done or no-show with the points, plus the ledger entries behind the balance                       |

- **Decision:** "Why you" states the rule, not a claim about this one decision. The solver also weighs load within a round, so "you had the fewest points" isn't always literally true. Interface copy has to be accurate, not just friendly.
- **Decision:** club points are listed alphabetically, not by points. Sorted by points, the same list becomes a leaderboard, which rewards collecting points instead of sharing the work.
- **Decision:** an invalid member link shows the shared NotFound page, rendered in place rather than redirected, so the URL stays visible to copy to the coordinator. It carries one extra line: ask your coordinator for a new link. A server failure keeps its own "Something went wrong" with Try again, because retrying can fix that one.
- **Decision:** no release tag yet. The coordinator override (remove or reassign someone on an upcoming shift) comes before session 11 and `v0.2.0`, because a coordinator who can't replace a sick volunteer is the first gap a real club would hit.
- **Went wrong:** frontend-only merges stopped deploying again. The `backend/**` and `frontend/**` build filters had disappeared from the Render settings. Re-added them and confirmed with a frontend-only push. Still planned: a deploy job in GitHub Actions, so deploys only follow green CI and don't depend on those filters.
- **Learned:** the difference between a table model and a response model. `Assignment` stores ids and a status; `MyAssignment` is the shape the member's screen needs, built from the assignment, its shift and its shift type in one query.
- **Learned:** a view is just a component. The router decides which URL shows it, but a layout can render it too, which keeps the URL intact.
- **Noted:** the generated UI works, but it isn't how I build frontends. That is the v0.3.0 redesign, after the flows are complete, so I don't restyle screens that are still changing.

## Wed 4 Nov: v0.2.0 out, and a privacy gap closed

- **Built:** session 12, the coordinator override. Remove someone from an upcoming shift, or give it to someone else from a list the server prepares: people who said yes first, fewest points on top, anyone on an overlapping shift greyed out. The inline confirm replaced `window.confirm` on these actions.
- **Built:** session 11, a Points tab for the coordinator, the version bump to 0.2.0, README updates, release notes, and short READMEs for the `backend` and `frontend` folders in place of the scaffold text.
- **Released:** `v0.2.0` tagged and published on GitHub.

- **Decision:** removing someone also clears their "I could do this" for that shift. Without it, remove followed by refill hands the shift straight back to the same person. Caught in planning, proven by a test.
- **Decision:** the server decides who is busy, for both the dropdown and the reassign check, so the screen and the rule can't disagree. The server still checks again on reassign, because a dropdown can be out of date.
- **Decision:** assignments with an outcome, or on shifts that have started, are locked. A planned shift can change; a done or no-show shift is history, and the append-only ledger depends on that.
- **Decision:** no ledger entry for a removal or reassignment. Points only move on outcomes, so there is nothing to record.
- **Decision:** the same points, sorted for the reader. The coordinator sees lowest first, to know who is next in line; members see them alphabetically, so the list doesn't become a contest.
- **Decision:** members see everyone's balance but only their own history. Before the fix, any member could read everyone else's no-shows.
- **Decision:** the privacy fix shipped as one PR. Backend and frontend deploy from the same commit on Render, so the breaking API change and the screens that use it had to land together.

- **Found:** anyone who guessed a club id could read that club's member names, assignments and points. Ids count up from 1, so "guessed" means "tried 1, 2, 3". Harmless with demo data, not with a real club. Listed it honestly as a known limitation in the v0.2.0 release and fixed it as the first patch.
- **Went wrong:** checked a new tab on port 8000 and couldn't find it. Port 8000 serves the last `npm run build`; the dev server on 5173 shows the current code. Now I use 5173 while building, and a fresh build on 8000 as a production check before merging.
- **Went wrong:** while adding coordinator headers to the tests, `headers=headers` slipped inside a URL f-string. Ruff caught it as invalid syntax.
- **Learned:** Ruff's pyupgrade rules prefer `datetime.UTC` over `timezone.utc`. Same object, newer name.
- **Learned:** after locking endpoints down, the existing tests failing was the proof the fix worked. If none had broken, the tests never checked access at all. Fixed them by sending the right headers, not by loosening the endpoints.
- **Learned:** a tag is a promise about one commit, so the version bump goes in before tagging.

- **Next:** before and after screenshots of every screen, then updated user-flow diagrams, then the v0.3.0 redesign in my own frontend style.

## Thu 5 Nov: v0.2.1 live, and a look at what's next

- **Released:** `v0.2.1` tagged and published. Checked live: member names, assignments and points now need the coordinator link, unauthenticated calls get a `detail` error instead of data, and every member and coordinator view still works.
- **Built:** updated diagrams for v0.2.1, in `docs/images/v0.2.1/` so the original planning diagrams stay as they were: a screen map with an id for every screen (L1 to L3, M1 to M3, C1 to C4, X1), the first visit, member and coordinator flows, and a proposed onboarding checklist drawn as "not built".
- **Built:** a screenshot plan, `docs/screenshots.md`: 32 shots in an order where each step creates the data the next one needs, named by screen id so the redesign's "after" set pairs up automatically.
- **Reviewed:** security beyond the privacy fix. Found that one script could use up the 200-demo limit and lock every visitor out for a day, that creating real clubs has no limit at all, and that there are no security headers.
- **Decision:** none of these block the redesign. Abuse limits and security headers come in one hardening session before the link goes public. The Content-Security-Policy is written after the redesign, so it lists the final fonts and assets instead of blocking them mid-redesign.
- **Decision:** keep `/docs` public on purpose. It shows the API to reviewers, and it's a choice, not an oversight.
- **Planned:** Dependabot alerts, security updates, and secret scanning with push protection.
- **Learned:** a review of what's _still_ exposed after a fix is part of the fix.

## Tue 10 Nov: into the redesign

- **Decided (6 Nov):** Docker only where it solves a real problem, since I'm moving towards full stack: Postgres locally through Docker Compose and in CI, because SQLite already hid two Postgres differences from me, then one Dockerfile for local, CI and Render. Not a Dockerfile just to have one.
- **Captured (7 Nov):** the full "before" screenshot set for v0.2.1.
- **Built (7 Nov):** a Figma file with 19 screens at phone and desktop width, imported from the live app as editable layers instead of screenshots, so the redesign starts from the real screens.
- **Found (7 Nov):** the first requests to the database after a quiet spell took about 40 seconds, while the health check answered in under 2. The free tiers explain the database sleeping; whether they explain all of the delay is still to test.
- **Found (7 Nov):** "+1 points" and "1 pts". Planned fix: one plural helper for every count, using `Intl.PluralRules`, so Dutch comes with the right rules later. Reminders for this, a leftover starter CSS block and a box with empty space are marked on the Figma frames.
- **Redesigned:** the member header. [What changed and why.]
- **Fixed:** the demo guide showed up in a newly started club. Locally, SQLite gave the new club the id of a deleted demo, so the remembered demo matched by id alone. The panel now also has to match the coordinator token, which is random and never reused. It was worse than it looked: the panel listed member links from a different club.
- **Idea:** members who belong to several clubs. The hard part isn't tabs; it's that the app has no "person" separate from a membership. The most valuable part would be avoiding clashes across clubs, with each club only seeing "busy" for the others. Added to v2 ideas.
- **Decision:** a deliberate v1.0 line. Redesign, a second user test with a coordinator, hardening, the Docker and Postgres track, season reset and Dutch. Everything else stays in v2 ideas.
- **Learned:** an id says which row, not which thing. Anything remembered across visits needs something that can't be reused.

## Wed 11 Nov: a user test with several people finds a real bug

- **Tested:** a full round with several people: a new club, members and shifts across four weeks, links sent out, answers saved, a schedule generated with gaps on purpose, published, answers changed, generated and published again.
- **Found:** after members changed their answers, generating again filled nothing new. Reproduced it on the live app: first in a demo club, where refilling worked, then in a new club built like the test, where it didn't.
- **Cause:** the solver allowed at most 2 shifts per member, counted across every upcoming shift instead of per week. Since session 8, refilling counts shifts people already hold, so anyone given 2 shifts in the first round could never be picked again, for any week. The preview gave no reason, so it looked as if the new answers were ignored.
- **Decision:** remove the maximum instead of making it per week. The fairness order already spreads the work; the maximum only changed the outcome when the one willing member was capped, and then it left empty a slot they had offered to fill. Clubs with several matches or events a week would hit any fixed number anyway. A limit each member sets for themselves is a later feature.
- **Decision:** not "forget earlier assignments and redo everything" on regenerate. People who already have their shift would get a different one, and it wouldn't have helped, because the maximum would still apply.
- **Planned (session 13):** remove the maximum; the preview explains every empty slot ("nobody said yes", "said yes, but already has a shift at that time"); the coordinator can assign someone to an empty slot by hand. The solver tests already pass with the change, and a new test fails on the old solver, so it proves the bug.
- **Redesigned:** the member availability screen. The tab is now "My availability", the button "Save my availability", with a count of how many shifts you're available for. Small styling changes implemented. Redesign still in progress.
- **Noted:** the new member copy says the fewest-points rule exists "to better their scoring chances". The rule is there to share the work fairly; the copy should say so.
- **Idea:** a coordinator view of everyone's availability, as a grid of members by shifts, which would also show at a glance why a slot is empty. For the coordinator redesign.
- **Left behind:** a test club, "Repro test (delete me)", in the live database.
- **Learned:** the old maximum had a passing test. The test proved the rule did what it said, not that the rule was right. Real people across four weeks found what a three-shift unit test couldn't.
