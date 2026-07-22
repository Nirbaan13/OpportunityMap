# Premium paywall (pre-deployment)

Browse opportunities is **free**. Profile, recommendations (“For you”), Saved, Remind me, and deadline notifications require a **yearly** premium membership.

Default price: **₹299 / year** — change with `PREMIUM_PRICE_INR` in `backend/.env` (no code change).

Membership lasts **365 days** from payment (`users.premium_until`). Paying again after expiry starts a new year (or extends from remaining time if you renew early).

## What is free vs paid

| Free | Premium (yearly) |
|------|------------------|
| `/` and browse `/opportunities` | Profile create/edit |
| Opportunity detail (read) | For you matches |
| Register / login | Saved bookmarks |
| | Remind me (10-day / 1-day alerts) |
| | Notifications inbox + reminder emails |

## Payment (Razorpay)

1. Create an account at [Razorpay](https://razorpay.com/)
2. Copy **test** Key ID + Key Secret into `backend/.env`:

```env
PREMIUM_PRICE_INR=299
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
```

3. Configure Razorpay's webhook URL as
   `https://YOUR-API/api/v1/payments/webhooks/razorpay` for
   `payment.captured`, `payment.failed`, `payment.refunded`, and `refund.processed`.
4. Frontend `/pricing` opens Razorpay Checkout. Premium is granted only after
   Razorpay confirms that the payment is captured; webhooks recover payments if
   the browser closes before verification completes.

### Local testing without Razorpay

The test unlock is disabled by default. It requires `ENVIRONMENT=development`,
`DEBUG=true`, `ALLOW_DEV_PREMIUM_UNLOCK=true`, and empty Razorpay keys. It is
never mounted in production.

## API

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| `GET` | `/payments/config` | public | yearly price, whether Razorpay is on |
| `POST` | `/payments/create-order` | JWT | starts checkout (renew extends +365 days) |
| `POST` | `/payments/verify` | JWT | verify signature → +365 days |
| `GET` | `/payments/status/{order_id}` | JWT | reconcile interrupted checkout |
| `POST` | `/payments/webhooks/razorpay` | Razorpay signature | captured/failed/refunded events |
| `POST` | `/payments/dev-unlock` | JWT | explicit local development only |

Paid routes return **403** if premium has expired: profiles, matches, bookmarks, notifications.

`GET /auth/me` includes `is_premium` and `premium_until`.

## Migration

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```
