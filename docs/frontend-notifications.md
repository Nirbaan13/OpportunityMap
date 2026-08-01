# Frontend notifications (Phase 10)

Website Alerts inbox (no mobile push). Deadline reminders also go to the registered email when SMTP is configured.

## Pages / UI

| Path / control | Purpose |
|----------------|---------|
| `/notifications` | Inbox list, mark read / mark all |
| Header **Alerts** | Nav + unread count badge (desktop) |
| Mobile bottom **Alerts** | Premium tab + unread badge |
| **Remind me** | Opt in to 10-day and 1-day reminders (inbox + email) |
| Opportunity detail / feed / Saved | Remind me next to Save |

## Behaviour

- **~90 / ~30 days:** interest matches (premium) get inbox + email. Catch-up if the daily job missed the exact day (88–90 and 28–30).
- **10 days / 1 day:** only if Remind me is on — inbox + email (2–10 day catch-up for the 10-day alert).
- Guests see “Log in for Remind me”.

## API

See [notifications-api.md](notifications-api.md).
