# Frontend

Vue 3, TypeScript and Vite. See the [main README](../README.md) for what the app does.

## Run

    npm ci
    npm run dev

Expects the backend on http://127.0.0.1:8000; Vite forwards `/api` there.

## Check

    npx oxlint .
    npx eslint .
    npm run test:unit -- --run
    npm run build

## Where things are

- `src/api.ts` every call to the backend, with shared error handling
- `src/time.ts` all date formatting, in the club's timezone
- `src/views/` one file per screen; `MemberLayout` and `CoordinatorLayout` check the link once
- `src/components/` pieces shared between screens
- `src/assets/main.css` design tokens and shared classes
