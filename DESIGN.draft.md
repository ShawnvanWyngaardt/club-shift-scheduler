---
version: alpha
name: Club Shift Scheduler
description: Two palettes in one app. Member side (plum and orange, global tokens in main.css) and coordinator side (Ghost, scoped under .coord in coordinator.css).
colors:
  primary: "#F34213"
  # Member side (main.css, :root)
  color-bg: "#FCF7FF"
  color-surface: "#FCF7FF"
  color-ink: "#15171C"
  color-muted: "#4A515C"
  color-border: "#D9DDE0"
  color-accent: "#0B6E69"
  color-ok: "#067647"
  color-error: "#B42318"
  color-warning: "#B54708"
  color-warning-surface: "#FFFAEB"
  color-text: "#273E47"
  color-shadow: "#909CC281"
  color-text-light: "#FCF7FF"
  color-text-accent: "#F58A07"
  color-text-muted: "#909CC2"
  color-pill-bg-accent: "#F58A0721"
  color-accent-primary: "#5DFDCB"
  color-accent-secondary: "#F34213"
  color-cta-gradient-mid: "#FF7A18"
  color-member-dark-1: "#210124"
  color-member-dark-2: "#750D37"
  color-border-dark: "#21012433"
  # Coordinator side (coordinator.css, .coord)
  navy: "#084887"
  sky: "#39A0ED"
  ink: "#1F2A30"
  muted: "#626E78"
  green: "#0CDA9A"
  green-ink: "#067A57"
  go: "#078760"
  go-hover: "#066F4F"
  alert: "#F34213"
  mint-surface: "#E5FCF5"
  bg: "#F7F8FA"
  surface: "#FFFFFF"
  line: "#E4E8EC"
  chip: "#EEF1F4"
  on-navy: "#FFFFFF"
  danger: "#C62828"
typography:
  body:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.5
  page-title:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: 800
  card-title:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 600
  secondary:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
  secondary-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: 400
  label-sm:
    fontFamily: Roboto Mono
    fontSize: 11px
    fontWeight: 600
    letterSpacing: 0.08em
  label-md:
    fontFamily: Roboto Mono
    fontSize: 12px
    fontWeight: 600
    letterSpacing: 0.06em
  time:
    fontFamily: Montserrat
    fontSize: 14px
    fontWeight: 600
  hero:
    fontFamily: Titan One
    fontSize: 48px
    fontWeight: 400
rounded:
  r: 8px
  r-lg: 16px
  full: 999px
spacing:
  space-1: 4px
  space-2: 8px
  space-3: 12px
  space-4: 16px
  space-6: 24px
  space-7: 32px
  space-8: 48px
  wrap: 1120px
  wrap-narrow: 640px
---

# Design

How Club Shift Scheduler looks, reads and behaves, so a new screen fits without guessing. Written for people and for AI coding tools: follow it as rules, and when something here disagrees with the code, the code wins and this file needs fixing.

The coordinator side follows the reviewed prototype (Ghost scheme). The reasons behind most rules are in `docs/journal.md`, 17 and 18 Nov.

## Principles

1. **Each page answers one question.** Overview: what needs me? Week: is this week covered? Check-in: who did their shift? Members & shifts: who and what?
2. **Neutral surfaces, colour for meaning.** Colour marks actions and states, never decoration.
3. **Colour goes to what went well.** Done and full are green; missed is grey. Nobody should feel told off.
4. **Copy is accurate before it is friendly.** Don't promise what the app doesn't do. Don't show a number the API can't back.
5. **Final actions get a review step.** Anything that writes points is marked first, then saved.
6. **The interface shows the rules.** If the API will refuse something, the screen disables it and says why, instead of letting the request fail.

## Two sides, two palettes

| | Member side | Coordinator side |
| --- | --- | --- |
| Who | Volunteers, on a phone, through a personal link | One coordinator, on a laptop |
| Layout | Phone first | Laptop first; works on a phone, not designed for it yet |
| Palette | Plum and orange (`main.css`) | Ghost: white and ghost white, navy, sky, green (`coordinator.css`) |
| Scope | Global tokens in `:root` | Everything under `.coord`, set on the layout's outer element |

Never mix them: no plum or orange gradients on coordinator screens, no navy buttons on member screens. The one shared colour is the orange (`#F34213`) of the Check-in count, borrowed on purpose because it's the one thing people wait on.

A coordinator page outside `CoordinatorLayout` (like Start a club) imports `@/assets/coordinator.css` and wraps itself in `<div class="coord">`.

## Coordinator tokens

Use the variable, never the hex value.

| Token | Value | Use |
| --- | --- | --- |
| `--navy` | `#084887` | Primary buttons, links, the active tab, headings in tables |
| `--sky` | `#39A0ED` | Indicators: tab bar, focus ring, empty slots, "new" in a preview |
| `--ink` / `--heading` | `#1F2A30` | Body text, headings |
| `--muted` | `#626E78` | Secondary text, and anything missed |
| `--green` | `#0CDA9A` | Full, done: edges, fills, the notice icon |
| `--green-ink` | `#067A57` | Green as text |
| `--go` / `--go-hover` | `#078760` / `#066F4F` | Schedule actions with white text (the darkest green that passes 4.5:1) |
| `--whatsapp` | `#078760` | WhatsApp outline buttons |
| `--alert` | `#F34213` | The Check-in count only |
| `--mint-surface` | `#E5FCF5` | Notice bar, published pill, "available" cells |
| `--bg` | `#F7F8FA` | Page background |
| `--surface` | `#FFFFFF` | Cards |
| `--line` | `#E4E8EC` | Borders, dividers, input outlines |
| `--chip` | `#EEF1F4` | Name chips, grey pills |
| `--shadow` | `0 2px 10px -4px rgba(20,30,40,.14)` | Every card |
| `--r` / `--r-lg` | `8px` / `16px` | Card corners; the grid's card |

Red (`#C62828`) appears in one place: the Check-in cross button, tinted at rest and solid when pressed.

## Type

| Variable | Font | Use |
| --- | --- | --- |
| (body) | Inter | Everything by default |
| `--font-time` | Montserrat | Dates and times: week dates, shift times |
| `--font-mono` | Roboto Mono | Small uppercase labels (eyebrows, section titles, column heads), member codes |
| `--font-hero` | Titan One | Landing page hero only |

Coordinator sizes: page title 26px / 800, card title 16px / 600 to 700, body 15px, secondary 13 to 14px, labels 11 to 13px uppercase mono with 0.06 to 0.08em letter spacing.

## Layout

- **Page width:** `.coord .wrap` is 1120px with a 16px gutter. Single-task pages narrow it (Start a club: 640px).
- **Page header:** `.page-head` holds the h1, one line of muted text, and at most one action on the right.
- **Section titles:** `.section-title` goes above a group of cards, outside the card.
- **Cards:** white, `--r` corners, `--shadow`, padding 14 to 20px. A **3px right edge** carries the card's state, the same pattern as the member side:

| Edge | Means |
| --- | --- |
| Green | Full or done |
| Sky | Has an empty slot, needs filling, or is an open form |
| Navy | Needs the coordinator ("Needs you" cards with a navy button) |
| Go green | The next schedule step ("Needs you" cards with a green button) |
| Grey | Not published, nothing planned |

- **Spacing:** gaps of 8, 12, 16, 20, 24 or 32px. 12px between cards in a list, 24 to 32px between sections.
- **Breakpoints:** 900px (two columns become one) and 600px (rows stack). Nothing may make the page scroll sideways; wide content, like the availability grid, scrolls inside its own card.

## Buttons

Classes on `.btn`. **No grey buttons**: grey reads as disabled.

| Class | Looks | For |
| --- | --- | --- |
| `btn-primary` | Navy fill, white text | The one next thing to do |
| `btn-go` | Green fill, white text | Schedule actions: Generate preview, Publish, Fill slots, Save a check-in |
| `btn-secondary` | Light sky tint, navy text | Useful, not urgent: Add shift, Assign |
| `btn-ghost` | Sky outline, navy text | Small or reversible: Cancel, Copy link, Edit type |
| `btn-whatsapp` | Green outline | Send through WhatsApp |
| `btn-edit` | No border, optional pencil | Quiet edits in long lists |
| `btn-icon` | 32px square, icon only | Must have an `aria-label`; `aria-pressed` for toggles |

- **Corners:** 4px, with the top right and bottom left at 14px (12px on `btn-small`). Applied to every button; it's the coordinator side's signature.
- **Sizes:** 40px tall by default, 32px with `btn-small`. Buttons doing the same job in a column share a width (112px in "Needs you" and Check-in Save).
- **One main action per place.** If a page header has the action, a message elsewhere links to it in text instead of repeating the button.
- **Disabled** is 45% opacity, and always explained nearby when the reason isn't obvious.

## States and status

| State | Treatment |
| --- | --- |
| Full, published, done | Green edge, `pill.published` (mint), solid green outline on a saved check-in |
| Empty slot, gap | Blue: dashed sky box with a reason inside, `pill.empty` |
| Not published, nothing planned | Grey edge, `pill.unpublished` |
| Missed | Grey text and numbers; red only on the cross button |
| Marked, not saved yet | Dashed outline (green for done, grey for missed) |
| Preview | Sky "Preview" pill; added people as outlined chips labelled **new** |
| Started shift | Dimmed, no edit buttons, a note that it can't change |

Separators in running text are pipes: `Published | 2 empty`, `07:00 – 09:00 | 2 people`. Never a middle dot.

## Components

| Component | Where | Notes |
| --- | --- | --- |
| Tabs with sliding bar | `CoordinatorLayout`, `useSlidingTabBar` | One bar under the active tab, animated; jumps instead with reduced motion. A child page keeps its parent tab lit. |
| Notice bar | `NoticeBar`, `useNotice` | One message at a time, under the tabs, full width. Closes after 60 seconds or on ×. Its `role="status"` element is always in the page. Use it after every save: what happened, then what it means. |
| Waiting count | `useWaitingCount` | The orange number on Check-in. Update it straight after a save. |
| Demo card | `DemoPanel` | In the header during a demo; its two lists open as menus over the page, one at a time, closed by a click outside or Escape. |
| Empty slot | Week page | Dashed sky box saying why it's empty ("Anna is available", "Nobody is available"), plus Assign. |
| Availability grid | Week page | Members down, shifts across. Cells: ✓ on the shift (navy), ✓ new (sky outline), ● available (mint), · not available. Every cell has screen-reader text. Names stay visible while it scrolls. |
| Check-in card | `CheckInShift` | Tinted tick and cross per person, Save per shift. Only the chosen result stays after saving. |
| Member row | `MemberList` | Chevron and name (opens the history), Next tag, points, hidden code (dots of the same length), actions. |
| Shift type group | `ShiftList` | Header with Edit type and Add shift; one form open at a time, under the type, with a sky edge. |
| Inputs | Everywhere | 40px tall, 1.5px `--line` border, 12px corners, our own select chevron 12px from the edge, `box-sizing: border-box`. |

## Words

One word per idea, the same on both sides.

| Use | Not |
| --- | --- |
| Available, Who is available | Said yes, could do this |
| Check-in, check in | Record outcomes |
| Did the shift / Done | Completed, attended |
| Missed | No-show |
| Members & shifts | Setup |
| Overview | Dashboard |
| Publish week 48 | Publish schedule |
| Fill slots, Fill empty slots | Generate (on its own) |

- Say what happens and what it means: "2 checks saved for Bar. 1 did the shift, 1 missed it."
- Explain locked things in place: "2 people are on this shift, so its time is fixed."
- No em dashes in any copy. Use a colon, a comma or a new sentence.
- British spelling (colour, organise).

## Interaction rules

- **Review before final.** Check-ins are marked, then saved per shift, all or nothing. Destructive actions use an inline confirm (Remove / Keep), never `window.confirm`.
- **One open form at a time.** Opening another closes the first.
- **State that should survive a refresh lives in the URL** (`?view=available`, `?section=shifts`), not in memory.
- **Show the API's rules up front:** disable what would be refused, say why, and still show the server's message if it refuses anyway.
- **Motion:** short (200 to 300ms), and none with `prefers-reduced-motion`.

## Accessibility

- Focus ring: 3px `--sky`, 2px offset, on everything focusable.
- Click targets at least 32px; text buttons 40px.
- White text only on `--navy` or `--go` or darker. `--green` and `--sky` are for edges, fills and icons, not for small text.
- Icon-only buttons need `aria-label`; toggles use `aria-pressed`; disclosures use `aria-expanded`.
- Symbols (✓ ● ·, tick and cross) are `aria-hidden` with a text label next to them in `.sr-only`.
- Links that open a new tab say so to screen readers.

## Code conventions

- **Logic in plain TypeScript, not in components.** What a screen shows is worked out in modules like `overview.ts`, `week.ts`, `checkin.ts`, `members.ts`, `shifts.ts`, each with a spec in `src/__tests__`. Components display the result.
- **Shared coordinator styles** (tokens, buttons, page header, pills, tick and cross) live in `coordinator.css`. Everything else is scoped to its component.
- **Times:** the club's clock is Europe/Amsterdam (`CLUB_TIMEZONE`). Use the helpers in `time.ts`; never format a date with the browser's own time zone.
- **Week ranges** are Monday 00:00 to the next Monday 00:00, club time, `to` exclusive.
- Code that a test imports must type-check under `tsconfig.vitest.json`.

## Don't

- Don't add a fourth coordinator tab. A new need goes into an existing page first.
- Don't use red for anything except the Check-in cross.
- Don't use grey for a button.
- Don't show placeholder or invented numbers in the real app.
- Don't hard-code hex values in components.
- Don't let a phone screen scroll sideways.
