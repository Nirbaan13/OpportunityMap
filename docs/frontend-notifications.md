# Frontend notifications (Phase 10)

Website Alerts inbox (no mobile push). Deadline reminders also go to the registered email when SMTP is configured.

## Pages / UI

| Path / control | Purpose |
|----------------|---------|
| `/notifications` | Inbox list, mark read / mark all |
| Header **Alerts** | Nav + unread count badge |
| **Remind me** | Opt in to 10-day and 1-day reminders (inbox + email) |
| Opportunity detail / feed / Saved | Remind me next to Save |

## Behaviour

- **3 months / 30 days:** interest matches get inbox + email (daily job).
- **10 days / 1 day:** only if Remind me is on — inbox + email.
- Guests see “Log in for Remind me”.

## API

See [notifications-api.md](notifications-api.md).
