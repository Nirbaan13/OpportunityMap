"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { OpportunityRow } from "@/components/OpportunityRow";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { api } from "@/lib/api";
import { ApiError, BookmarkItem } from "@/types/api";

const PAGE_SIZE = 20;

export default function BookmarksPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [items, setItems] = useState<BookmarkItem[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!user || !token || !user.is_premium) {
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
        const data = await api.listBookmarks(token, { page, page_size: PAGE_SIZE, status: "saved" });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
        setTotalPages(data.total_pages);
      } catch (err) {
        if (cancelled) return;
        setItems([]);
        setTotal(0);
        setTotalPages(0);
        setError(err instanceof ApiError ? err.message : "Could not load bookmarks.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [authLoading, user, token, page]);

  function onUnsave(opportunityId: number) {
    setItems((prev) => prev.filter((item) => item.opportunity.id !== opportunityId));
    setTotal((prev) => Math.max(0, prev - 1));
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
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink">Saved</h1>
          <p className="mt-4 text-ink-soft">
            <Link href="/login" className="text-accent hover:underline">
              Log in
            </Link>{" "}
            and unlock premium to save opportunities.
          </p>
        </div>
      </main>
    );
  }

  if (!user.is_premium) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)]">
        <div className="mx-auto max-w-xl px-6 py-10 sm:px-10">
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink">Saved</h1>
          <p className="mt-3 text-ink-soft">
            Saving opportunities is part of Premium along with recommendations and alerts.
          </p>
          <div className="mt-8">
            <PremiumPaywall title="Unlock Saved" />
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="atmosphere min-h-[calc(100vh-5rem)]">
      <div className="mx-auto max-w-4xl px-6 py-10 sm:px-10">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Library
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Saved
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Opportunities you bookmarked from the feed or detail pages.
        </p>

        <section className="mt-8">
          <p className="text-sm text-ink-soft">
            {loading ? "Loading…" : `${total} saved`}
          </p>

          {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}

          {!loading && !error && total === 0 ? (
            <p className="mt-8 text-ink-soft">
              Nothing saved yet.{" "}
              <Link href="/opportunities" className="text-accent hover:underline">
                Browse opportunities
              </Link>{" "}
              and tap Save on ones you want to revisit.
            </p>
          ) : null}

          <div className="mt-4">
            {items.map((item) => (
              <OpportunityRow
                key={item.opportunity.id}
                opportunity={item.opportunity}
                bookmarked
                remindMe={item.remind_me}
                onBookmarkChange={(next) => {
                  if (!next) onUnsave(item.opportunity.id);
                }}
                onRemindMeChange={(next) => {
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
