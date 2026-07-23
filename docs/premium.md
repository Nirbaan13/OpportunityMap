# Premium paywall (pre-deployment)

Browse opportunities is **free**. Profile, recommendations (“For you”), Saved, Remind me, and deadline notifications require a **yearly** premium membership.

Default price: **₹299 / year** (India via Razorpay, one-time annual purchase).
International buyers use a **Polar yearly subscription** (price set in Polar, not
shown on-site). Change INR with `PREMIUM_PRICE_INR`.

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
PREMIUM_PRICE_USD=3.99
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
POLAR_ACCESS_TOKEN=...
POLAR_PRODUCT_ID=...
POLAR_WEBHOOK_SECRET=...
POLAR_API_BASE=https://api.polar.sh/v1
```

3. Configure Razorpay's webhook URL as
   `https://YOUR-API/api/v1/payments/webhooks/razorpay` for
   `payment.captured`, `payment.failed`, `payment.refunded`, and `refund.processed`.
4. In Polar, create a **yearly subscription** product (set $3.99 there), then webhook:
   `https://YOUR-API/api/v1/payments/webhooks/polar` for
   `order.paid`, `subscription.canceled`, `subscription.uncanceled`, and
   `subscription.revoked`.
5. Frontend `/pricing` opens Razorpay for India and Polar for outside India.
   Premium is granted after payment is confirmed; webhooks recover payments if
   the browser closes before verification completes. Polar renewals extend another year.

### Local testing without Razorpay

The test unlock is disabled by default. It requires `ENVIRONMENT=development`,
`DEBUG=true`, `ALLOW_DEV_PREMIUM_UNLOCK=true`, and empty Razorpay keys. It is
never mounted in production.

## API

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| `GET` | `/payments/config` | public | yearly price, whether Razorpay/Polar is on |
| `POST` | `/payments/create-order` | JWT | starts Razorpay checkout (INR) |
| `POST` | `/payments/polar/create-checkout` | JWT | starts Polar international checkout |
| `POST` | `/payments/verify` | JWT | verify Razorpay signature → +365 days |
| `GET` | `/payments/status/{order_id}` | JWT | reconcile interrupted Razorpay checkout |
| `POST` | `/payments/webhooks/razorpay` | Razorpay signature | captured/failed/refunded events |
| `POST` | `/payments/webhooks/polar` | Polar signature | paid renewals + cancel/revoke |
| `POST` | `/payments/dev-unlock` | JWT | explicit local development only |

Paid routes return **403** if premium has expired: profiles, matches, bookmarks, notifications.

`GET /auth/me` includes `is_premium` and `premium_until`.

## Migration

```powershell
cd C:\Users\ASUS\OneDrive\Desktop\PassionProject\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```
