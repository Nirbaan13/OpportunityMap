# Frontend auth & profile (Phase 7)

Student-facing pages for registration, login, and profile create/edit.

## Pages

| Path | Purpose |
|------|---------|
| `/` | Landing hero |
| `/register` | Create account |
| `/login` | Log in |
| `/profile` | Create or edit student profile (requires login) |

## Auth flow

1. Register or login → JWT stored in `localStorage` as `opportunitymap_token`.
2. `AuthProvider` loads `GET /api/v1/auth/me` on startup.
3. Protected pages send `Authorization: Bearer <token>`.
4. After register/login, user is sent to `/profile`.

## Profile form

Loads option lists from:

- `GET /api/v1/fields`
- `GET /api/v1/activities`

Then creates or updates via:

- `POST /api/v1/profiles/me` (first time)
- `PUT /api/v1/profiles/me` (edits)

## Run locally

Backend must be on port 8000 (or set `NEXT_PUBLIC_API_URL`).

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\frontend
npm run dev
```

Open http://localhost:3000
