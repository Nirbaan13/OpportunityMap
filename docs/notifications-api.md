# Notifications & deadline reminders (Phase 10)

Website **Alerts** inbox **and** email to the student's **registered account email**.

## Reminder schedule

| When | Who receives it |
|------|-----------------|
| **~3 months** (90 days) before deadline | Students with **overlapping interests** (and grade/country eligibility) |
| **30 days** before | Same interest-overlap audience |
| **10 days** before | Only students who turned on **Remind me** for that opportunity |
| **1 day** before | Only students who turned on **Remind me** |

Each new reminder is written to `notifications` **and** emailed to `users.email` when SMTP is configured.

## Remind me

Stored on `bookmarks.remind_me`.

- `PATCH /api/v1/bookmarks/{opportunity_id}` with `{ "remind_me": true }`  
  Creates a bookmark if none exists.
- Turning Remind me **off** keeps the bookmark but stops 10-day / 1-day alerts.
- Deleting the bookmark also clears Remind me.

UI: **Remind me** on opportunity detail, feed rows, and Saved.

## In-site notifications API

All require `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/notifications` | Paginated inbox (`unread_only`, `page`, `page_size`) |
| `GET` | `/api/v1/notifications/unread-count` | Badge count |
| `POST` | `/api/v1/notifications/{id}/read` | Mark one read |
| `POST` | `/api/v1/notifications/read-all` | Mark all read |

Each deadline reminder stores `reminder_lead_days` (`90`, `30`, `10`, or `1`) and links to the opportunity when still available.

Dedup: one row per `(user, opportunity, lead_days)` for `deadline_reminder` (covers both inbox + email).

## Email

Sent to the address used at registration (`users.email`) whenever a new deadline reminder is created.

Configure in `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `SMTP_HOST` | e.g. `smtp.gmail.com` (empty = skip email) |
| `SMTP_PORT` | Default `587` |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP auth |
| `SMTP_FROM` | From header, e.g. `OpportunityMap <you@gmail.com>` |
| `SMTP_USE_TLS` | Default `true` |
| `FRONTEND_URL` | Links in the email body |

Without SMTP, the daily job still creates inbox alerts; emails are skipped and the CLI prints a note.

## Daily job

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\backend
.\.venv\Scripts\Activate.ps1
python -m app.jobs.run_deadline_reminders
```

Matching uses calendar days until `deadline_at` (UTC date). Re-running the same day skips already-sent rows (no duplicate mail).

## Frontend

| Path | Role |
|------|------|
| `/notifications` | Inbox (mark read) |
| Header **Alerts** | Link + unread badge |
| Opportunity detail / feed | **Remind me** toggle |

See [frontend-notifications.md](frontend-notifications.md).
