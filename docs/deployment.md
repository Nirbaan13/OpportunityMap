# Deployment Guide (Phase 11)

Deploy **Frontend → Vercel**, **Backend + Postgres → Railway**, **Scraper + reminders → GitHub Actions**.

## Architecture (production)

```
Browser  →  Vercel (Next.js)  →  Railway (FastAPI)
                                      ↓
                               Railway Postgres
                                      ↑
                         GitHub Actions (scraper + reminders)
```

## 0. Put the code on GitHub

This repo must be on GitHub before Vercel/Railway can deploy it.

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject
git status
# If you have not committed yet, create the first commit, then:

# Create a new empty repo on github.com (do not add README), then:
git remote add origin https://github.com/YOUR_USERNAME/OpportunityMap.git
git branch -M main
git push -u origin main
```

## 1. Railway — database + API

### 1a. Postgres

1. Go to [railway.app](https://railway.app) → **New Project** → **Provision PostgreSQL**
2. Open the Postgres service → **Variables** → copy `DATABASE_URL`  
   (or use **Connect** → public URL). The API auto-normalizes `postgres://` → `postgresql+psycopg://`.

### 1b. Backend service

1. In the same project: **New** → **GitHub Repo** → select `OpportunityMap`
2. Set **Root Directory** to `backend`
3. Railway will use `backend/Dockerfile` + `backend/railway.toml`
4. Start command (already in Dockerfile): migrations then `uvicorn`

### 1c. Backend environment variables

Set these on the **backend** Railway service (Variables):

| Variable | Example / notes |
|----------|-----------------|
| `DATABASE_URL` | Reference from Postgres service (`${{Postgres.DATABASE_URL}}`) |
| `SECRET_KEY` | Long random string (not `change-me-in-production`) |
| `DEBUG` | `false` |
| `CORS_ORIGINS` | Your Vercel URL, e.g. `https://opportunitymap.vercel.app` |
| `FRONTEND_URL` | Same as Vercel URL (used in reminder emails) |
| `PREMIUM_PRICE_INR` | `299` |
| `RAZORPAY_KEY_ID` | **Live** key when going live (`rzp_live_…`) |
| `RAZORPAY_KEY_SECRET` | Matching live secret |
| `SMTP_HOST` | e.g. `smtp.gmail.com` (optional but needed for email alerts) |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | Your SMTP user |
| `SMTP_PASSWORD` | App password / SMTP key |
| `SMTP_FROM` | e.g. `OpportunityMap <you@gmail.com>` |
| `SMTP_USE_TLS` | `true` |

Generate `SECRET_KEY`:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 1d. Deploy & verify

1. Deploy the backend service
2. Open the public URL Railway gives you, e.g. `https://opportunitymap-api-production.up.railway.app`
3. Check: `https://YOUR_API_URL/api/v1/health` → `{"status":"ok"}`
4. Docs: `https://YOUR_API_URL/docs`

Migrations run automatically on each container start (`alembic upgrade head`).

## 2. Vercel — frontend

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → import the GitHub repo
2. **Root Directory**: `frontend`
3. Framework: Next.js (auto)
4. Environment variable:

| Name | Value |
|------|--------|
| `NEXT_PUBLIC_API_URL` | Railway API origin **without** trailing slash, e.g. `https://opportunitymap-api-production.up.railway.app` |

5. Deploy
6. Copy the Vercel URL (e.g. `https://opportunitymap.vercel.app`)
7. Back on Railway, set `CORS_ORIGINS` and `FRONTEND_URL` to that Vercel URL, then **redeploy** the backend

### Local frontend pointing at production API (optional)

`frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=https://YOUR_API_URL
```

## 3. GitHub Actions — scraper + daily reminders

In the GitHub repo: **Settings → Secrets and variables → Actions** → add:

| Secret | Value |
|--------|--------|
| `DATABASE_URL` | Same production Postgres URL as Railway (public URL if Actions run outside Railway network) |
| `SECRET_KEY` | Same as backend |
| `FRONTEND_URL` | Vercel URL |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_FROM` / `SMTP_USE_TLS` | Same as backend |

Workflows (already in the repo):

- `.github/workflows/scrape-opportunities.yml` — daily scrape
- `.github/workflows/deadline-reminders.yml` — daily inbox + email reminders

Run manually: **Actions** → select workflow → **Run workflow**.

> Postgres on Railway: enable a **public** TCP URL (or use Railway’s “TCP Proxy”) so GitHub Actions can connect. Prefer a dedicated public `DATABASE_URL` secret.

## 4. Razorpay (production)

1. Switch from test to **live** keys in Razorpay Dashboard
2. Put live keys on Railway (`RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`)
3. Keep `DEBUG=false` so `/payments/dev-unlock` is disabled

## 5. Post-deploy checklist

- [ ] `GET /api/v1/health` → 200
- [ ] Vercel site loads
- [ ] Browse opportunities on the live site
- [ ] Register / login works
- [ ] CORS not blocked (browser console clean)
- [ ] Premium checkout works with Razorpay test or live keys
- [ ] GitHub Action “Scrape opportunities” succeeds once
- [ ] GitHub Action “Deadline reminders” succeeds once (or dry-run)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Frontend “Failed to fetch” | Wrong `NEXT_PUBLIC_API_URL`, or Railway service sleeping/down |
| CORS error | Set `CORS_ORIGINS` to exact Vercel origin (https, no trailing slash) and redeploy API |
| DB connection from Actions | Use Railway **public** Postgres URL in `DATABASE_URL` secret |
| `sslmode` errors | Append `?sslmode=require` to `DATABASE_URL` if the host requires TLS |
| Migrations fail on boot | Check Railway logs; ensure `DATABASE_URL` is set on the **API** service |
| Payments stuck on “not configured” | Set both Razorpay keys on Railway |

## Platforms summary

| Piece | Platform | Root / notes |
|-------|----------|--------------|
| Frontend | Vercel | `frontend/` |
| API | Railway | `backend/` + Dockerfile |
| Database | Railway Postgres | Plug into API via `DATABASE_URL` |
| Scraper | GitHub Actions | `scraper/` |
| Reminders | GitHub Actions | `backend/` job module |
