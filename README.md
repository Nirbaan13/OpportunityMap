# OpportunityMap

Help ambitious high school students discover opportunities they are eligible for — without spending hours searching the internet.

Students create a profile with their grade, country, interests, and experience. The platform collects opportunities from many websites (olympiads, hackathons, research programs, summer schools, competitions, scholarships, fellowships), matches them to each student, and sends deadline reminders.

## Architecture

```
┌─────────────────┐     HTTPS/JSON      ┌─────────────────┐
│   Frontend      │ ──────────────────► │    Backend      │
│   (Next.js)     │ ◄────────────────── │   (FastAPI)     │
│   Vercel        │                     │  Railway/Render │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │   PostgreSQL    │
                                        └────────▲────────┘
                                                 │
                                        ┌────────┴────────┐
                                        │    Scraper      │
                                        │  (Playwright)   │
                                        │  Cron / Actions │
                                        └─────────────────┘
```

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | React + Next.js (App Router) | Modern React framework with routing, SSR, and easy Vercel deployment |
| Backend | Python FastAPI | Fast to build, auto-generated API docs, strong typing with Pydantic |
| Database | PostgreSQL | Reliable relational DB for structured opportunity and user data |
| ORM | SQLAlchemy 2.0 + Alembic | Industry-standard Python ORM with version-controlled migrations |
| Scraper | Playwright + BeautifulSoup | Handles both static HTML and JavaScript-rendered pages |
| Styling | Tailwind CSS | Utility-first CSS for rapid UI development |
| Version control | GitHub | Standard for team collaboration and CI/CD |
| Frontend hosting | Vercel | Zero-config Next.js deployment |
| Backend hosting | Railway or Render | Simple Python deployment with managed Postgres |

## Repository Structure

```
OpportunityMap/
├── README.md                 # This file
├── docker-compose.yml        # Local PostgreSQL
├── docs/                     # Extended documentation (updated per feature)
│   ├── architecture.md       # Data flow, matching logic, auth
│   ├── api-conventions.md    # REST naming, error format
│   ├── authentication.md     # JWT register / login
│   ├── profile-api.md        # Student profile CRUD
│   ├── opportunities-api.md  # List / search / filter
│   ├── matching-api.md       # Personalized match feed
│   ├── bookmarks-api.md      # Save / list / remove bookmarks
│   ├── notifications-api.md  # Deadline reminders + inbox
│   ├── premium.md            # Free browse vs paid unlock
│   ├── frontend-auth-profile.md  # Auth + profile UI
│   ├── frontend-opportunity-feed.md  # Opportunity feed UI
│   ├── frontend-bookmarks.md # Saved opportunities UI
│   ├── frontend-notifications.md # Alerts inbox UI
│   └── deployment.md         # Vercel + Railway checklist
├── frontend/                 # Next.js web app
│   └── src/
│       ├── app/              # Pages and routing
│       ├── components/       # Reusable UI components
│       ├── lib/              # API client, utilities
│       ├── hooks/            # Custom React hooks
│       └── types/            # TypeScript types
├── backend/                  # FastAPI REST API
│   └── app/
│       ├── main.py           # App entry point
│       ├── config.py         # Environment settings
│       ├── database.py       # SQLAlchemy setup
│       ├── api/v1/           # HTTP route handlers
│       ├── models/           # Database tables
│       ├── schemas/          # Request/response validation
│       ├── services/         # Business logic
│       └── core/             # Auth and security (future)
└── scraper/                  # Web scraping workers
    └── scraper/
        ├── main.py           # CLI entry point
        ├── sources/          # One module per website
        └── parsers/          # Shared parsing utilities
```

Each subfolder (`frontend/`, `backend/`, `scraper/`) has its own README with folder-specific setup instructions.

## Prerequisites

Install these before starting:

| Tool | Version | Purpose |
|------|---------|---------|
| [Node.js](https://nodejs.org/) | 20 LTS | Frontend dev server and build |
| [Python](https://www.python.org/) | 3.12 or 3.13 (recommended) | Backend API and scraper. Python 3.14 is not yet supported by PostgreSQL drivers. |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Latest | Local PostgreSQL database |
| [Git](https://git-scm.com/) | Latest | Version control |

Verify installations:

```powershell
node --version
python --version
docker --version
git --version
```

## Local Development Setup

### 1. Clone the repository

```powershell
git clone <your-repo-url>
cd OpportunityMap
```

### 2. Start PostgreSQL

Docker runs a PostgreSQL container on your machine. You only need to do this once per session.

```powershell
docker compose up -d
```

Verify it is running:

```powershell
docker compose ps
```

Default credentials (development only):

- Host: `localhost`
- Port: `5432`
- User: `opportunitymap`
- Password: `opportunitymap_dev`
- Database: `opportunitymap`

### 3. Backend

Open a terminal:

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[postgres]"
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

> Use `py -3.12` to ensure Python 3.12 (required for PostgreSQL drivers). If you only have one Python install, `python -m venv .venv` also works.

Verify:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health

### 4. Frontend

Open a **second** terminal:

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open http://localhost:3000 — you should see the OpportunityMap placeholder page.

### 5. Scraper

```powershell
cd scraper
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[postgres]"
playwright install   # only needed for competition_sciences
copy .env.example .env

# Devpost — online beginner-friendly hackathons (recommended for competitions)
python -m scraper.main --source devpost --max-items 20

# Pathways to Science — high-school research internships only
python -m scraper.main --source pathways_to_science --max-items 20

# Global high-school olympiads & competitions (curated seed)
python -m scraper.main --source global_competitions
```

See `docs/scraper-pathways-to-science.md` for details.

## Environment Variables

### Backend (`backend/.env`)

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://opportunitymap:opportunitymap_dev@localhost:5432/opportunitymap` | PostgreSQL connection string |
| `SECRET_KEY` | `change-me-in-production` | Secret for signing tokens (change in production) |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed frontend URLs |
| `APP_NAME` | `OpportunityMap API` | Display name in API docs |
| `DEBUG` | `true` | Enable debug mode (disable in production) |

### Frontend (`frontend/.env.local`)

| Variable | Example | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

### Scraper (`scraper/.env`)

| Variable | Example | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+psycopg://opportunitymap:opportunitymap_dev@localhost:5432/opportunitymap` | PostgreSQL connection string |
| `API_URL` | *(optional)* | Backend API URL (Phase 2+ strategy) |
| `API_KEY` | *(optional)* | API key for protected endpoints |

Copy each `.env.example` to `.env` (or `.env.local` for frontend) before running.

## Development Workflow

1. **One feature at a time.** Each phase in the roadmap below is a separate unit of work.
2. **Branch naming:** `feature/bookmarks`, `fix/scraper-timeout`
3. **Update docs:** When you add a feature, update the relevant file in `docs/`.
4. **Keep layers separate:**
   - Frontend calls the API — it never talks to the database directly.
   - Backend handles business logic in `services/`, not in route handlers.
   - Scraper writes to the database (or calls an admin API later).

## Development Roadmap

| Phase | Feature | Depends on | Status |
|-------|---------|------------|--------|
| 0 | Project scaffold | — | **Done** |
| 1 | Database schema: users, profiles, opportunities | Phase 0 | **Done** |
| 2 | User registration + login (JWT) | Phase 1 | **Done** |
| 3 | Profile CRUD (grade, country, interests, experience, activities) | Phase 2 | **Done** |
| 4 | Opportunity listing + search/filter API | Phase 1 | **Done** |
| 5 | First scraper + seed data pipeline | Phase 1 | **Done** |
| 6 | Matching engine (eligibility + interests) | Phase 3, 4 | **Done** |
| 7 | Frontend: auth pages + profile form | Phase 2, 3 | **Done** |
| 8 | Frontend: opportunity feed + filters | Phase 4, 7 | **Done** |
| 9 | Bookmarks | Phase 4, 7 | **Done** |
| 10 | Deadline notifications (website inbox + email) | Phase 9 | **Done** |
| 10b | Freemium paywall (₹299/year, Razorpay) | Phase 10 | **Done** |
| 11 | Deployment (Vercel + Neon free) | Phase 7+ | **Ready** (docs/deployment.md Option A) |
| 12 | Additional scrapers (one source at a time) | Phase 5 | Planned |

Each completed phase gets a short update in [docs/architecture.md](docs/architecture.md).

## Deployment Overview

**Free stack (Option A):** two Vercel projects + Neon Postgres + GitHub Actions.  
Guide: [docs/deployment.md](docs/deployment.md).

| Component | Free platform | Root |
|-----------|---------------|------|
| Frontend | Vercel | `frontend/` |
| Backend API | Vercel (FastAPI) | `backend/` |
| Database | Neon | — |
| Scraper + reminders | GitHub Actions | schedule every 2–3 days |

Optional: buy only a **domain** and attach it in Vercel.

## Scraper Strategy

**Phase 1 (current plan):** The scraper writes directly to PostgreSQL using the same SQLAlchemy models as the backend.

**Phase 2 (optional):** The scraper posts to a protected admin API endpoint. This simplifies database access but adds API authentication complexity. We will defer this until needed.

## Contributing

This project is under active development. When contributing:

1. Pick a phase from the roadmap.
2. Create a feature branch.
3. Implement the feature with tests where appropriate.
4. Update documentation in `docs/`.
5. Open a pull request.

## License

TBD
