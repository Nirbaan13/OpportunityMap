# OpportunityMap Backend

FastAPI REST API for OpportunityMap.

## Prerequisites

- Python 3.12+
- PostgreSQL running locally (see root `docker-compose.yml`)

## Setup

From the `backend/` directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[postgres]"
copy .env.example .env
```

## Run

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

Health check: http://localhost:8000/api/v1/health

Auth endpoints: http://localhost:8000/docs (register, login, me)

Opportunity listing: `GET /api/v1/opportunities` (search/filter) — see [docs/opportunities-api.md](../docs/opportunities-api.md)

Personalized matches: `GET /api/v1/matches` (JWT + profile) — see [docs/matching-api.md](../docs/matching-api.md)

## Database Migrations

Migrations are managed with Alembic.

```powershell
# Apply all migrations (requires PostgreSQL running)
alembic upgrade head

# Create a new migration (after models change)
alembic revision --autogenerate -m "description"
```

Schema documentation: [docs/database-schema.md](../docs/database-schema.md)

## Project Structure

```
app/
├── main.py          # FastAPI app entry point
├── config.py        # Environment settings
├── database.py      # SQLAlchemy engine and session
├── api/v1/          # HTTP route handlers
├── models/          # Database table definitions
├── schemas/         # Request/response validation
├── services/        # Business logic
└── core/            # Auth and security (future)
```

## Environment Variables

See `.env.example` for all required variables.
