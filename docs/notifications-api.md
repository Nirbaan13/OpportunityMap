# Notifications & deadline reminders (Phase 10)

Website **Alerts** inbox for all logged-in users. **Email** goes to the student's
registered address for **premium** reminders only (when SMTP is configured).

## Reminder schedule

Matching uses UTC calendar days until `deadline_at`.

| When | Who | Channel |
|------|-----|---------|
| **~90 days** (88–90) | Premium + interest overlap | Inbox + email |
| **~30 days** (28–30) | Premium + interest overlap | Inbox + email |
| **~30 days** (28–30) | Free + **Remind me** | **Inbox only** (no email) |
| **10 days** (2–10) | Premium + **Remind me** | Inbox + email |
| **1 day** | Premium + **Remind me** | Inbox + email |

## Remind me

Stored on `bookmarks.remind_me`. Available to **all logged-in users**.

- `PUT /api/v1/bookmarks/{opportunity_id}/remind-me` with `{ "remind_me": true }`
- Free: website inbox ~1 month before deadline
- Premium: email + website at 10 days and 1 day (plus interest 90/30 when profile matches)

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

Premium deadline reminders are emailed to `users.email` when SMTP is configured.
Free Remind me alerts are **inbox only** (no email).

Configure in `backend/.env`:

| Variable | Purpose |
|----------|---------|
| `SMTP_HOST` | `smtp.gmail.com` (empty = skip email) |
| `SMTP_PORT` | Default `587` |
| `SMTP_USERNAME` | `founder.opportunitymap@gmail.com` |
| `SMTP_PASSWORD` | Gmail **App Password** (not the normal login password) |
| `SMTP_FROM` | `OpportunityMap <founder.opportunitymap@gmail.com>` |
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
