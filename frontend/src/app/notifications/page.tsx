"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { api } from "@/lib/api";
import { ApiError, NotificationItem } from "@/types/api";

const PAGE_SIZE = 20;

function leadLabel(days: number | null): string | null {
  if (days == null) return null;
  if (days === 90) return "3 months out";
  if (days === 1) return "1 day left";
  return `${days} days left`;
}

export default function NotificationsPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(currentToken: string, currentPage: number) {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listNotifications(currentToken, {
        page: currentPage,
        page_size: PAGE_SIZE,
      });
      setItems(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
      setUnreadCount(data.unread_count);
    } catch (err) {
      setItems([]);
      setTotal(0);
      setTotalPages(0);
      setError(err instanceof ApiError ? err.message : "Could not load notifications.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (authLoading) return;
    if (!user || !token || !user.is_premium) {
      setItems([]);
      setLoading(false);
      return;
    }
    void load(token, page);
  }, [authLoading, user, token, page]);

  async function onMarkRead(item: NotificationItem) {
    if (!token || item.is_read) return;
    try {
      await api.markNotificationRead(token, item.id);
      setItems((prev) =>
        prev.map((row) => (row.id === item.id ? { ...row, is_read: true } : row)),
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // leave unread
    }
  }

  async function onMarkAll() {
    if (!token || unreadCount === 0) return;
    try {
      await api.markAllNotificationsRead(token);
      setItems((prev) => prev.map((row) => ({ ...row, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not mark all read.");
    }
  }

  if (authLoading) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)] px-6 py-16">
        <p className="text-ink-soft">Loading…</p>
      </main>
    );
  }

  if (!user || !token) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)]">
        <div className="mx-auto max-w-4xl px-6 py-10 sm:px-10">
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink">
            Notifications
          </h1>
          <p className="mt-4 text-ink-soft">
            <Link href="/login" className="text-accent hover:underline">
              Log in
            </Link>{" "}
            and unlock premium for deadline alerts.
          </p>
        </div>
      </main>
    );
  }

  if (!user.is_premium) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)]">
        <div className="mx-auto max-w-xl px-6 py-10 sm:px-10">
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink">
            Notifications
          </h1>
          <p className="mt-3 text-ink-soft">
            Deadline alerts (website + email) are a Premium feature.
          </p>
          <div className="mt-8">
            <PremiumPaywall title="Unlock alerts" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="atmosphere min-h-[calc(100vh-5rem)]">
      <div className="mx-auto max-w-4xl px-6 py-10 sm:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
              Inbox
            </p>
            <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Notifications
            </h1>
            <p className="mt-3 max-w-2xl text-ink-soft">
              Deadline alerts appear here and are emailed to your registered address —
              3 months and 30 days for matching interests; 10 days and 1 day when you turn
              on Remind me.
            </p>
          </div>
          {unreadCount > 0 ? (
            <button
              type="button"
              onClick={() => void onMarkAll()}
              className="rounded-md border border-line px-3 py-2 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent"
            >
              Mark all read ({unreadCount})
            </button>
          ) : null}
        </div>

        <section className="mt-8">
          <p className="text-sm text-ink-soft">
            {loading ? "Loading…" : `${total} notification${total === 1 ? "" : "s"}`}
          </p>
          {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}

          {!loading && !error && total === 0 ? (
            <p className="mt-8 text-ink-soft">
              No notifications yet. Complete your{" "}
              <Link href="/profile" className="text-accent hover:underline">
                profile
              </Link>{" "}
              for early interest alerts, and use{" "}
              <span className="text-ink">Remind me</span> on opportunities for close deadlines.
            </p>
          ) : null}

          <ul className="mt-4 divide-y divide-line border-t border-line">
            {items.map((item) => {
              const lead = leadLabel(item.reminder_lead_days);
              const href = item.opportunity
                ? `/opportunities/${item.opportunity.id}`
                : undefined;
              return (
                <li key={item.id} className="py-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
                        {item.is_read ? "Read" : "New"}
                        {lead ? (
                          <span className="ml-3 font-medium normal-case tracking-normal text-warm">
                            {lead}
                          </span>
                        ) : null}
                      </p>
                      <h2 className="mt-1.5 font-display text-lg font-semibold text-ink">
                        {href ? (
                          <Link
                            href={href}
                            className="transition hover:text-accent"
                            onClick={() => void onMarkRead(item)}
                          >
                            {item.title}
                          </Link>
                        ) : (
                          item.title
                        )}
                      </h2>
                      <p className="mt-2 text-sm text-ink-soft">{item.message}</p>
                      <p className="mt-2 text-xs text-ink-soft/80">
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!item.is_read ? (
                      <button
                        type="button"
                        onClick={() => void onMarkRead(item)}
                        className="text-sm font-medium text-ink-soft transition hover:text-accent"
                      >
                        Mark read
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>

          {totalPages > 1 ? (
            <div className="mt-8 flex items-center justify-between gap-4 border-t border-line pt-6">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-md border border-line px-3 py-2 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent disabled:opacity-40"
              >
                Previous
              </button>
              <p className="text-sm text-ink-soft">
                Page {page} of {totalPages}
              </p>
              <button
                type="button"
                disabled={page >= totalPages || loading}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-line px-3 py-2 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent disabled:opacity-40"
              >
                Next
              </button>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
