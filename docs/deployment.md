# Deployment — Option A (free): Vercel + Neon

**Goal:** $0 hosting (optional paid domain). Frontend on Vercel never “sleeps.”  
API also runs on **Vercel** (serverless FastAPI) + **Neon** Postgres.  
Scrapers every 2–3 days via **GitHub Actions** (free).

| Piece | Service | Sleep? |
|-------|---------|--------|
| Website | Vercel (project: frontend) | No |
| API | Vercel (project: backend) | Short cold start (~1–3s), not a 1‑min Render sleep |
| Database | Neon free | Auto-wakes in ~0.5–2s |
| Scrapers / reminders | GitHub Actions | N/A (scheduled) |

You will create **two Vercel projects** from the same GitHub repo (different Root Directories).

---

## Part 1 — GitHub

1. Push this repo to GitHub (if not already).
2. Keep the repo URL handy.

---

## Part 2 — Neon (database)

1. Sign up: [https://neon.tech](https://neon.tech) (GitHub login is fine).
2. **Create project** → name e.g. `opportunitymap`.
3. Open **Dashboard** → **Connect** / connection string.
4. Copy the URI (pooled is fine). Example:

```text
postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```

5. Save it — you will paste into Vercel + GitHub Secrets. Never commit it.

---

## Part 3 — Run migrations once

Neon starts empty. Apply schema with GitHub Actions:

1. GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secret `DATABASE_URL` = your Neon URI  
3. Add secret `SECRET_KEY` = any long random string (same one you’ll use on the API)
4. **Actions** → **Database migrations** → **Run workflow**

Or locally (with Docker/local Python):

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require"
alembic upgrade head
```

---

## Part 4 — Vercel API (backend)

1. [vercel.com](https://vercel.com) → sign up with GitHub.
2. **Add New** → **Project** → import `OpportunityMap`.
3. Configure:

| Setting | Value |
|---------|--------|
| Project Name | `opportunitymap-api` (or similar) |
| **Root Directory** | `backend` |
| Framework | Other / FastAPI (auto if detected) |

4. **Environment Variables** (Production):

| Name | Value |
|------|--------|
| `DATABASE_URL` | Neon URI |
| `SECRET_KEY` | long random string |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `ALLOW_DEV_PREMIUM_UNLOCK` | `false` |
| `CORS_ORIGINS` | temporary `http://localhost:3000` — update after frontend deploys |
| `FRONTEND_URL` | temporary same |
| `PREMIUM_PRICE_INR` | `299` |
| `RAZORPAY_KEY_ID` | Razorpay test/live Key ID |
| `RAZORPAY_KEY_SECRET` | matching private API secret |
| `RAZORPAY_WEBHOOK_SECRET` | separate secret configured for the API webhook |

5. **Deploy**.
6. Copy the API URL, e.g. `https://opportunitymap-api.vercel.app`
7. Test: `https://YOUR-API.vercel.app/api/v1/health` → `{"status":"ok"}`
8. Add a Razorpay webhook pointing to
   `https://YOUR-API.vercel.app/api/v1/payments/webhooks/razorpay` for captured,
   failed, refunded, and refund-processed events.

---

## Part 5 — Vercel website (frontend)

1. Vercel → **Add New** → **Project** → same repo again.
2. Configure:

| Setting | Value |
|---------|--------|
| Project Name | `opportunitymap` |
| **Root Directory** | `frontend` |
| Framework | Next.js |

3. Environment variable:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | API URL from Part 4 — **must include `https://`**, no trailing slash (e.g. `https://opportunitymap-api.vercel.app`) |

4. **Deploy**.
5. Copy site URL, e.g. `https://opportunitymap.vercel.app`

### Wire CORS

Back to **opportunitymap-api** project → Settings → Environment Variables:

| Name | Value |
|------|--------|
| `CORS_ORIGINS` | your frontend Vercel URL |
| `FRONTEND_URL` | same |

Redeploy the **API** project.

---

## Part 6 — Scrapers (every 2–3 days)

GitHub → **Settings** → **Secrets** (same as migrate):

| Secret | Value |
|--------|--------|
| `DATABASE_URL` | Neon URI |
| `SECRET_KEY` | same as API |
| `FRONTEND_URL` | frontend Vercel URL |
| SMTP_* | optional (email reminders) |

Edit `.github/workflows/scrape-opportunities.yml` cron if you want every 2–3 days, e.g.:

```yaml
- cron: "0 1 */3 * *"   # every 3 days at 01:00 UTC
```

**Actions** → **Scrape opportunities** → **Run workflow** once to fill data.

---

## Part 7 — Optional domain

Buy a domain → Vercel frontend project → **Settings** → **Domains** → add it.  
Point DNS as Vercel instructs. Free SSL included.

---

## Checklist

- [ ] Neon project created  
- [ ] Migrations ran (`Database migrations` workflow)  
- [ ] API `/api/v1/health` OK on Vercel  
- [ ] Frontend loads and can call API  
- [ ] Scrape workflow ran once  
- [ ] CORS updated to frontend URL  

---

## What “no sleep” means here

- **Pages** on Vercel: always available.  
- **API**: serverless — may take **1–3 seconds** on a cold start, then fast. Not a full minute offline like free Render.  
- **Neon**: brief wake if idle.  

That’s the best free UX you can get without a paid always-on server.

---

## Local vs production

```powershell
# Local API still works as before
cd backend
.\.venv\Scripts\Activate.ps1
# optional: use Neon from .env
uvicorn app.main:app --reload --port 8000

cd frontend
# .env.local → NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
