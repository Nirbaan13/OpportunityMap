"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { ApiError, type AdminOverviewResponse } from "@/types/api";

const STORAGE_KEY = "om_admin_password";

function formatWhen(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [draftPassword, setDraftPassword] = useState("");
  const [data, setData] = useState<AdminOverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem(STORAGE_KEY);
    if (stored) {
      setPassword(stored);
      setDraftPassword(stored);
    }
  }, []);

  useEffect(() => {
    if (!password) {
      setData(null);
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const overview = await api.getAdminOverview(password);
        if (!cancelled) setData(overview);
      } catch (err) {
        if (!cancelled) {
          setData(null);
          setError(err instanceof ApiError ? err.message : "Could not load admin data.");
          if (err instanceof ApiError && err.status === 401) {
            sessionStorage.removeItem(STORAGE_KEY);
            setPassword("");
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [password]);

  function onUnlock(event: FormEvent) {
    event.preventDefault();
    const next = draftPassword.trim();
    if (!next) return;
    sessionStorage.setItem(STORAGE_KEY, next);
    setPassword(next);
  }

  function onLock() {
    sessionStorage.removeItem(STORAGE_KEY);
    setPassword("");
    setDraftPassword("");
    setData(null);
    setError(null);
  }

  async function onRefresh() {
    if (!password) return;
    setLoading(true);
    setError(null);
    try {
      setData(await api.getAdminOverview(password));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not refresh.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-5xl px-4 py-10 sm:px-10 sm:py-12">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Founder
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Admin
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Private dashboard for signups, premium members, and payments. Bookmark{" "}
          <span className="font-medium text-ink">/admin</span> — it is not linked in the public
          nav.
        </p>

        {!password ? (
          <form onSubmit={onUnlock} className="mt-10 max-w-md space-y-4 border-t border-line pt-8">
            <label className="block">
              <span className="text-sm font-medium text-ink">Admin password</span>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={draftPassword}
                onChange={(e) => setDraftPassword(e.target.value)}
                className="mt-2 w-full rounded-md border border-line bg-paper px-3 py-2.5 text-sm text-ink outline-none transition focus:border-accent"
              />
            </label>
            {error ? <p className="text-sm text-danger">{error}</p> : null}
            <button
              type="submit"
              className="rounded-md bg-ink px-4 py-2.5 text-sm font-semibold text-paper transition hover:bg-ink-soft"
            >
              Unlock
            </button>
            <p className="text-xs text-ink-soft">
              Set <code className="text-ink">ADMIN_PASSWORD</code> on the backend (Vercel API env).
            </p>
          </form>
        ) : (
          <div className="mt-8 space-y-8">
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => void onRefresh()}
                disabled={loading}
                className="rounded-md border border-line px-3 py-2 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent disabled:opacity-50"
              >
                {loading ? "Refreshing…" : "Refresh"}
              </button>
              <button
                type="button"
                onClick={onLock}
                className="rounded-md border border-line px-3 py-2 text-sm font-semibold text-ink-soft transition hover:text-ink"
              >
                Lock
              </button>
              <Link href="/" className="text-sm text-ink-soft hover:text-accent">
                Home
              </Link>
            </div>

            {error ? <p className="text-sm text-danger">{error}</p> : null}

            {data ? (
              <>
                <section className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
                  {[
                    ["Users", data.totals.users],
                    ["Premium", data.totals.premium_users],
                    ["With profile", data.totals.users_with_profile],
                    ["Signups (7d)", data.totals.signups_last_7_days],
                    ["Signups (30d)", data.totals.signups_last_30_days],
                    ["Paid payments", data.totals.payments_paid],
                    ["INR paid", `₹${data.totals.paid_amount_inr.toFixed(2)}`],
                    ["USD paid", `$${data.totals.paid_amount_usd.toFixed(2)}`],
                    ["Active listings", data.totals.opportunities_active],
                    ["All listings", data.totals.opportunities_total],
                  ].map(([label, value]) => (
                    <div
                      key={String(label)}
                      className="rounded-md border border-line bg-paper/80 px-4 py-3"
                    >
                      <p className="text-xs uppercase tracking-[0.14em] text-ink-soft">{label}</p>
                      <p className="mt-2 font-display text-2xl font-bold text-ink">{value}</p>
                    </div>
                  ))}
                </section>

                <section className="grid gap-6 sm:grid-cols-2">
                  <div>
                    <h2 className="font-display text-lg font-semibold text-ink">Payments by status</h2>
                    <ul className="mt-3 space-y-1 text-sm">
                      {data.payments_by_status.length === 0 ? (
                        <li className="text-ink-soft">No payments yet.</li>
                      ) : (
                        data.payments_by_status.map((row) => (
                          <li key={row.key} className="flex justify-between border-b border-line/70 py-1.5">
                            <span className="text-ink">{row.key}</span>
                            <span className="text-ink-soft">{row.count}</span>
                          </li>
                        ))
                      )}
                    </ul>
                  </div>
                  <div>
                    <h2 className="font-display text-lg font-semibold text-ink">
                      Payments by provider
                    </h2>
                    <ul className="mt-3 space-y-1 text-sm">
                      {data.payments_by_provider.length === 0 ? (
                        <li className="text-ink-soft">No payments yet.</li>
                      ) : (
                        data.payments_by_provider.map((row) => (
                          <li key={row.key} className="flex justify-between border-b border-line/70 py-1.5">
                            <span className="text-ink">{row.key}</span>
                            <span className="text-ink-soft">{row.count}</span>
                          </li>
                        ))
                      )}
                    </ul>
                  </div>
                </section>

                <section>
                  <h2 className="font-display text-lg font-semibold text-ink">Recent users</h2>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-[640px] text-left text-sm">
                      <thead className="border-b border-line text-xs uppercase tracking-[0.12em] text-ink-soft">
                        <tr>
                          <th className="py-2 pr-3 font-medium">Email</th>
                          <th className="py-2 pr-3 font-medium">Premium</th>
                          <th className="py-2 pr-3 font-medium">Profile</th>
                          <th className="py-2 font-medium">Joined</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_users.map((user) => (
                          <tr key={user.id} className="border-b border-line/60">
                            <td className="py-2.5 pr-3 text-ink">{user.email}</td>
                            <td className="py-2.5 pr-3 text-ink-soft">
                              {user.is_premium ? "Yes" : "No"}
                            </td>
                            <td className="py-2.5 pr-3 text-ink-soft">
                              {user.has_profile ? "Yes" : "No"}
                            </td>
                            <td className="py-2.5 text-ink-soft">{formatWhen(user.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>

                <section>
                  <h2 className="font-display text-lg font-semibold text-ink">Recent payments</h2>
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full min-w-[720px] text-left text-sm">
                      <thead className="border-b border-line text-xs uppercase tracking-[0.12em] text-ink-soft">
                        <tr>
                          <th className="py-2 pr-3 font-medium">User</th>
                          <th className="py-2 pr-3 font-medium">Provider</th>
                          <th className="py-2 pr-3 font-medium">Status</th>
                          <th className="py-2 pr-3 font-medium">Amount</th>
                          <th className="py-2 font-medium">When</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.recent_payments.length === 0 ? (
                          <tr>
                            <td colSpan={5} className="py-3 text-ink-soft">
                              No payments yet.
                            </td>
                          </tr>
                        ) : (
                          data.recent_payments.map((payment) => (
                            <tr key={payment.id} className="border-b border-line/60">
                              <td className="py-2.5 pr-3 text-ink">{payment.user_email}</td>
                              <td className="py-2.5 pr-3 text-ink-soft">{payment.provider}</td>
                              <td className="py-2.5 pr-3 text-ink-soft">{payment.status}</td>
                              <td className="py-2.5 pr-3 text-ink-soft">
                                {payment.currency} {payment.amount.toFixed(2)}
                              </td>
                              <td className="py-2.5 text-ink-soft">
                                {formatWhen(payment.paid_at ?? payment.created_at)}
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            ) : loading ? (
              <p className="text-ink-soft">Loading…</p>
            ) : null}
          </div>
        )}
      </div>
    </main>
  );
}
