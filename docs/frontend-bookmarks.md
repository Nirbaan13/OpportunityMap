# Frontend bookmarks (Phase 9)

Save opportunities from the feed or detail page; review them on `/bookmarks`.

## Pages / UI

| Path / component | Purpose |
|------------------|---------|
| `/bookmarks` | Paginated list of saved opportunities (JWT) |
| `/opportunities` | Save toggle on each row when browsing / For you |
| `/opportunities/[id]` | Save / Saved control next to apply links |
| `SiteHeader` | **Saved** nav link when logged in |
| `BookmarkButton` | Shared toggle (optimistic; handles 409/404) |

## API calls

| Action | Endpoint |
|--------|----------|
| List | `GET /api/v1/bookmarks` |
| Save | `POST /api/v1/bookmarks` `{ opportunity_id }` |
| Check | `GET /api/v1/bookmarks/{opportunity_id}` |
| Remove | `DELETE /api/v1/bookmarks/{opportunity_id}` |

See [bookmarks-api.md](bookmarks-api.md).

## Behaviour

- Guests see “Log in to save” instead of a toggle.
- Feed loads up to 100 bookmark ids to mark rows as Saved.
- Unsaving on `/bookmarks` removes the row from the list immediately.

## Run

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\frontend
npm run dev
```

Open http://localhost:3000/bookmarks (must be logged in).
