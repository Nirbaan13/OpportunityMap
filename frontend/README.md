# OpportunityMap Frontend

Next.js web application for OpportunityMap.

## Prerequisites

- Node.js 20 LTS
- npm

## Setup

From the `frontend/` directory:

```powershell
npm install
copy .env.example .env.local
```

## Run

```powershell
npm run dev
```

Open http://localhost:3000

Phase 7 pages: `/` (landing), `/register`, `/login`, `/profile` — see [docs/frontend-auth-profile.md](../docs/frontend-auth-profile.md).

Phase 8 pages: `/opportunities`, `/opportunities/[id]` — see [docs/frontend-opportunity-feed.md](../docs/frontend-opportunity-feed.md).

## Project Structure

```
src/
├── app/           # Pages and routing (App Router)
├── components/    # Reusable UI components
├── lib/           # API client and utilities
├── hooks/         # Custom React hooks
└── types/         # TypeScript type definitions
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL (default: `http://localhost:8000`) |

## Build for Production

```powershell
npm run build
npm start
```

Deployed to Vercel with root directory set to `frontend/`.
