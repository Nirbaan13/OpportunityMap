"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
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

  useEffect(() => {
    if (authLoading) return;
    if (!user || !token) {
      setItems([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    async function loadAndMarkRead(currentToken: string, currentPage: number) {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listNotifications(currentToken, {
          page: currentPage,
          page_size: PAGE_SIZE,
        });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setTotalPages(data.total_pages);
        setUnreadCount(data.unread_count);

        // Opening Alerts counts as reading — clear unread for next visit.
        if (data.unread_count > 0) {
          try {
            await api.markAllNotificationsRead(currentToken);
            if (cancelled) return;
            setItems((prev) => prev.map((row) => ({ ...row, is_read: true })));
            setUnreadCount(0);
          } catch {
            // Keep unread state if the mark-all call fails.
          }
        }
      } catch (err) {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setError(err instanceof ApiError ? err.message : "Could not load notifications.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadAndMarkRead(token, page);
    return () => {
      cancelled = true;
    };
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
            to see deadline alerts in your inbox.
          </p>
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
              {user.is_premium
                ? "Deadline alerts appear here and are emailed to your registered address — matching interests get early notice; Remind me adds ~30-day, 10-day, and 1-day emails."
                : "Free Remind me alerts appear here about a month before the deadline (website only). Premium adds email plus earlier and last-week reminders."}
            </p>
            {user.is_premium ? (
              <p
                className="mt-4 max-w-2xl border-l-2 border-warm/70 pl-3 text-sm text-ink"
                role="status"
              >
                Reminder emails come from{" "}
                <span className="font-medium">founder.opportunitymap@gmail.com</span>.
                If you don’t see one in your inbox, check Spam or Promotions and mark it
                as not spam so future alerts land correctly.
              </p>
            ) : (
              <p className="mt-3 text-sm">
                <Link href="/pricing" className="font-medium text-accent hover:underline">
                  Unlock email alerts →
                </Link>
              </p>
            )}
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
              No notifications yet. Turn on{" "}
              <span className="text-ink">Remind me</span> on an opportunity to get a
              website alert about a month before it closes
              {user.is_premium
                ? ", or complete your profile for earlier interest matches."
                : "."}
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
                        className="inline-flex min-h-11 shrink-0 items-center rounded-md border border-line px-3 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent sm:border-0 sm:px-0"
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
