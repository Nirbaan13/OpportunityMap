# Frontend notifications (Phase 10)

Website Alerts inbox (no mobile push). Deadline reminders also go to the registered email when SMTP is configured.

## Pages / UI

| Path / control | Purpose |
|----------------|---------|
| `/notifications` | Inbox list, mark read / mark all (all logged-in users) |
| Header **Alerts** | Nav + unread count badge (desktop) |
| Mobile bottom **Alerts** | Tab + unread badge (free and premium) |
| **Remind me** | Free: ~30-day inbox. Premium: 10/1 + email |
| Opportunity detail / feed / Saved | Remind me next to Save |

## Behaviour

- **Free Remind me:** website inbox about a month before (28–30 days). No email.
- **Premium interest (~90 / ~30):** inbox + email when profile matches.
- **Premium Remind me (10 / 1):** inbox + email (2–10 day catch-up for the 10-day alert).
- Guests see “Log in for Remind me”.

## API

See [notifications-api.md](notifications-api.md).
