"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { OpportunityRow } from "@/components/OpportunityRow";
import { api } from "@/lib/api";
import { loginHref } from "@/lib/auth-redirect";
import { ApiError, BookmarkItem } from "@/types/api";

const PAGE_SIZE = 20;

export default function RemindersPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [items, setItems] = useState<BookmarkItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !token) {
      setItems([]);
      setTotal(0);
      setTotalPages(0);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.listRemindMe(token, { page, page_size: PAGE_SIZE });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch (err) {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setError(err instanceof ApiError ? err.message : "Could not load reminders.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [authLoading, user, token, page]);

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
            Reminders
          </h1>
          <p className="mt-4 text-ink-soft">
            <Link href={loginHref("/reminders")} className="text-accent hover:underline">
              Log in
            </Link>{" "}
            to see opportunities you turned Remind me on for.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-10 sm:py-10">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Remind me
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Your reminders
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          {user.is_premium
            ? "Website + email alerts 10 days and 1 day before these deadlines."
            : "Free website inbox alert about a month before each deadline. Premium adds email and last-week reminders."}
        </p>
        {!user.is_premium ? (
          <p className="mt-2 text-sm">
            <Link href="/pricing" className="font-medium text-accent hover:underline">
              Unlock email alerts →
            </Link>
          </p>
        ) : null}

        <section className="mt-8">
          <p className="text-sm text-ink-soft">
            {loading ? "Loading…" : `${total} reminder${total === 1 ? "" : "s"}`}
          </p>

          {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}

          {!loading && !error && total === 0 ? (
            <div className="mt-8 space-y-3 text-ink-soft">
              <p>
                No reminders yet. Open an opportunity and turn on{" "}
                <span className="text-ink">Remind me</span>.
              </p>
              <p className="text-sm">
                <Link
                  href="/opportunities"
                  className="font-medium text-accent hover:underline"
                >
                  Browse opportunities
                </Link>
              </p>
            </div>
          ) : null}

          <div className="mt-4 space-y-3">
            {items.map((item) => (
              <OpportunityRow
                key={item.opportunity.id}
                opportunity={item.opportunity}
                showRemindMe
                showBookmark={Boolean(user.is_premium)}
                bookmarked={user.is_premium}
                remindMe={item.remind_me}
                onRemindMeChange={(next) => {
                  if (!next) {
                    setItems((prev) =>
                      prev.filter((row) => row.opportunity.id !== item.opportunity.id),
                    );
                    setTotal((prev) => Math.max(0, prev - 1));
                    return;
                  }
                  setItems((prev) =>
                    prev.map((row) =>
                      row.opportunity.id === item.opportunity.id
                        ? { ...row, remind_me: next }
                        : row,
                    ),
                  );
                }}
              />
            ))}
          </div>

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
