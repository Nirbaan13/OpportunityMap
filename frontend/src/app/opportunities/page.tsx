"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { OpportunityRow } from "@/components/OpportunityRow";
import { api } from "@/lib/api";
import { OPPORTUNITY_TYPES } from "@/lib/opportunity-labels";
import {
  ApiError,
  FieldOption,
  MatchItem,
  OpportunitySort,
  OpportunitySummary,
  OpportunityType,
  Profile,
} from "@/types/api";

type Mode = "browse" | "matches";

const PAGE_SIZE = 20;

export default function OpportunitiesPage() {
  const { user, token, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<Mode>("browse");
  const [fields, setFields] = useState<FieldOption[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);

  const [q, setQ] = useState("");
  const [draftQ, setDraftQ] = useState("");
  const [opportunityType, setOpportunityType] = useState<OpportunityType | "">("");
  const [field, setField] = useState("");
  const [openOnly, setOpenOnly] = useState(false);
  const [eligibleForMe, setEligibleForMe] = useState(true);
  const [sort, setSort] = useState<OpportunitySort>("deadline_asc");
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<OpportunitySummary[]>([]);
  const [matchItems, setMatchItems] = useState<MatchItem[]>([]);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<number>>(new Set());
  const [remindMeIds, setRemindMeIds] = useState<Set<number>>(new Set());
  const [doneIds, setDoneIds] = useState<Set<number>>(new Set());
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtersOpen, setFiltersOpen] = useState(false);

  const canUseMatches = Boolean(user && token && profile && user.is_premium);
  const canPersonalize = Boolean(user?.is_premium);
  const activeFilterCount =
    (opportunityType ? 1 : 0) +
    (field ? 1 : 0) +
    (openOnly ? 1 : 0) +
    (mode === "browse" && eligibleForMe && profile ? 1 : 0) +
    (mode === "browse" && sort !== "deadline_asc" ? 1 : 0) +
    (q ? 1 : 0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const fieldList = await api.listFields();
        if (!cancelled) setFields(fieldList);
      } catch {
        // filters still work without field chips
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (authLoading || !token || !user?.has_profile) {
      setProfile(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api.getProfile(token);
        if (!cancelled) setProfile(data);
      } catch {
        if (!cancelled) setProfile(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authLoading, token, user]);

  useEffect(() => {
    if (!canUseMatches && mode === "matches") {
      setMode("browse");
    }
  }, [canUseMatches, mode]);

  useEffect(() => {
    if (authLoading || !token || !user?.is_premium) {
      setBookmarkedIds(new Set());
      setRemindMeIds(new Set());
      setDoneIds(new Set());
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api.listBookmarks(token, { page: 1, page_size: 100 });
        if (cancelled) return;
        setBookmarkedIds(new Set(data.items.map((item) => item.opportunity.id)));
        setRemindMeIds(
          new Set(
            data.items.filter((item) => item.remind_me).map((item) => item.opportunity.id),
          ),
        );
        setDoneIds(
          new Set(
            data.items
              .filter((item) => item.status === "completed")
              .map((item) => item.opportunity.id),
          ),
        );
      } catch {
        if (!cancelled) {
          setBookmarkedIds(new Set());
          setRemindMeIds(new Set());
          setDoneIds(new Set());
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authLoading, token, user]);

  function setOpportunityBookmarked(opportunityId: number, bookmarked: boolean) {
    setBookmarkedIds((prev) => {
      const next = new Set(prev);
      if (bookmarked) next.add(opportunityId);
      else next.delete(opportunityId);
      return next;
    });
    if (!bookmarked) {
      setRemindMeIds((prev) => {
        const next = new Set(prev);
        next.delete(opportunityId);
        return next;
      });
      setDoneIds((prev) => {
        const next = new Set(prev);
        next.delete(opportunityId);
        return next;
      });
    }
  }

  function setOpportunityRemindMe(opportunityId: number, remindMe: boolean) {
    setRemindMeIds((prev) => {
      const next = new Set(prev);
      if (remindMe) next.add(opportunityId);
      else next.delete(opportunityId);
      return next;
    });
    if (remindMe) {
      setBookmarkedIds((prev) => new Set(prev).add(opportunityId));
    }
  }

  function setOpportunityDone(opportunityId: number, done: boolean) {
    setDoneIds((prev) => {
      const next = new Set(prev);
      if (done) next.add(opportunityId);
      else next.delete(opportunityId);
      return next;
    });
    if (done) {
      setBookmarkedIds((prev) => new Set(prev).add(opportunityId));
      setRemindMeIds((prev) => {
        const next = new Set(prev);
        next.delete(opportunityId);
        return next;
      });
    }
  }

  const profileGrade = profile?.grade_level;
  const profileCountry = profile?.country_code;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (mode === "matches") {
          if (!token) throw new ApiError(401, "Log in to see matches.");
          const data = await api.listMatches(token, {
            open_only: openOnly,
            opportunity_type: opportunityType || undefined,
            page,
            page_size: PAGE_SIZE,
          });
          if (cancelled) return;
          setMatchItems(data.items);
          setItems([]);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        } else {
          const data = await api.listOpportunities({
            q: q || undefined,
            opportunity_type: opportunityType || undefined,
            field: field || undefined,
            open_only: openOnly,
            sort,
            page,
            page_size: PAGE_SIZE,
            grade: eligibleForMe && profileGrade != null ? profileGrade : undefined,
            country: eligibleForMe && profileCountry ? profileCountry : undefined,
          });
          if (cancelled) return;
          setItems(data.items);
          setMatchItems([]);
          setTotal(data.total);
          setTotalPages(data.total_pages);
        }
      } catch (err) {
        if (cancelled) return;
        setItems([]);
        setMatchItems([]);
        setTotal(0);
        setTotalPages(0);
        setError(err instanceof ApiError ? err.message : "Could not load opportunities.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [
    mode,
    token,
    openOnly,
    opportunityType,
    page,
    q,
    field,
    sort,
    eligibleForMe,
    profileGrade,
    profileCountry,
  ]);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setPage(1);
    setQ(draftQ.trim());
  }

  function switchMode(next: Mode) {
    setMode(next);
    setPage(1);
  }

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-4xl px-4 py-6 sm:px-10 sm:py-10">
        <p className="font-display text-xs font-semibold uppercase tracking-[0.18em] text-accent sm:text-sm">
          Discover
        </p>
        <h1 className="mt-2 font-display text-2xl font-bold tracking-tight text-ink sm:mt-3 sm:text-4xl">
          Opportunities
        </h1>
        <p className="mt-2 hidden max-w-2xl text-ink-soft sm:mt-3 sm:block">
          Browse openings by type and interest, or switch to personalized matches once your
          profile is set.
        </p>

        <div className="mt-5 grid grid-cols-2 gap-2 border-b border-line pb-4 sm:mt-8 sm:flex sm:flex-wrap sm:gap-2">
          <button
            type="button"
            onClick={() => switchMode("browse")}
            className={`min-h-11 rounded-md px-3 py-2 text-sm font-medium transition ${
              mode === "browse"
                ? "bg-ink text-paper"
                : "text-ink-soft hover:bg-fog-deep/60 hover:text-ink"
            }`}
          >
            Browse all
          </button>
          <button
            type="button"
            onClick={() => {
              if (!canUseMatches) return;
              switchMode("matches");
            }}
            disabled={!canUseMatches}
            className={`min-h-11 rounded-md px-3 py-2 text-sm font-medium transition ${
              mode === "matches"
                ? "bg-ink text-paper"
                : "text-ink-soft hover:bg-fog-deep/60 hover:text-ink disabled:cursor-not-allowed disabled:opacity-45"
            }`}
            title={
              canUseMatches
                ? "Ranked for your profile"
                : "Create a profile to unlock personalized matches"
            }
          >
            For you
          </button>
          {!canUseMatches ? (
            <p className="col-span-2 pt-1 text-xs leading-relaxed text-ink-soft sm:w-full sm:pt-2 sm:text-sm">
              {!user ? (
                <>
                  <Link href="/login" className="text-accent hover:underline">
                    Log in
                  </Link>{" "}
                  and unlock premium for personalized ranking.
                </>
              ) : !user.is_premium ? (
                <>
                  <Link href="/pricing" className="text-accent hover:underline">
                    View roadmap
                  </Link>{" "}
                  for matches, profile, and alerts.
                </>
              ) : (
                <>
                  Finish your{" "}
                  <Link href="/profile" className="text-accent hover:underline">
                    profile
                  </Link>{" "}
                  to unlock ranked matches.
                </>
              )}
            </p>
          ) : null}
        </div>

        <section className="relative z-10 mt-4 space-y-3 border-b border-line pb-4 sm:mt-6 sm:space-y-4 sm:pb-6">
          {mode === "browse" ? (
            <form onSubmit={onSearch} className="flex gap-2">
              <input
                type="search"
                value={draftQ}
                onChange={(e) => setDraftQ(e.target.value)}
                placeholder="Search titles"
                className="min-h-11 flex-1 rounded-md border border-line bg-paper px-3 text-base outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20 sm:text-sm"
              />
              <button
                type="submit"
                className="shrink-0 rounded-md bg-ink px-4 text-sm font-semibold text-paper transition hover:bg-ink-soft"
              >
                Go
              </button>
            </form>
          ) : null}

          <button
            type="button"
            onClick={() => setFiltersOpen((v) => !v)}
            className="flex min-h-11 w-full items-center justify-between rounded-md border border-line bg-paper px-3 text-sm font-medium text-ink sm:hidden"
            aria-expanded={filtersOpen}
          >
            <span>
              Filters
              {activeFilterCount > 0 ? (
                <span className="ml-2 rounded-md bg-accent/15 px-2 py-0.5 text-xs font-semibold text-accent">
                  {activeFilterCount}
                </span>
              ) : null}
            </span>
            <span className="text-ink-soft">{filtersOpen ? "Hide" : "Show"}</span>
          </button>

          <div className={`space-y-4 ${filtersOpen ? "block" : "hidden sm:block"}`}>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                Type
              </p>
              <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 touch-pan-x sm:flex-wrap sm:overflow-visible">
                <button
                  type="button"
                  onClick={() => {
                    setOpportunityType("");
                    setPage(1);
                  }}
                  className={`shrink-0 rounded-md border px-3 py-2.5 text-sm font-medium transition ${
                    opportunityType === ""
                      ? "border-accent bg-accent/10 text-ink"
                      : "border-line bg-paper text-ink-soft hover:border-accent/40"
                  }`}
                >
                  All types
                </button>
                {OPPORTUNITY_TYPES.map((type) => (
                  <button
                    key={type.value}
                    type="button"
                    onClick={() => {
                      setOpportunityType(type.value);
                      setPage(1);
                    }}
                    className={`shrink-0 rounded-md border px-3 py-2.5 text-sm font-medium transition ${
                      opportunityType === type.value
                        ? "border-accent bg-accent/10 text-ink"
                        : "border-line bg-paper text-ink-soft hover:border-accent/40"
                    }`}
                  >
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {mode === "browse" ? (
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-soft">
                  Field
                </p>
                <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 touch-pan-x sm:flex-wrap sm:overflow-visible">
                  <button
                    type="button"
                    onClick={() => {
                      setField("");
                      setPage(1);
                    }}
                    className={`shrink-0 rounded-md border px-3 py-2.5 text-sm font-medium transition ${
                      field === ""
                        ? "border-warm/50 bg-warm/10 text-ink"
                        : "border-line bg-paper text-ink-soft hover:border-warm/40"
                    }`}
                  >
                    All fields
                  </button>
                  {fields.map((item) => (
                    <button
                      key={item.slug}
                      type="button"
                      onClick={() => {
                        setField(item.slug);
                        setPage(1);
                      }}
                      aria-pressed={field === item.slug}
                      className={`shrink-0 rounded-md border px-3 py-2.5 text-sm font-medium transition ${
                        field === item.slug
                          ? "border-warm/50 bg-warm/10 text-ink"
                          : "border-line bg-paper text-ink-soft hover:border-warm/40"
                      }`}
                    >
                      {item.name}
                    </button>
                  ))}
                </div>
                {fields.length === 0 ? (
                  <p className="mt-2 text-sm text-ink-soft">Loading fields…</p>
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-col gap-3 rounded-md bg-fog/40 p-3 text-sm sm:flex-row sm:flex-wrap sm:items-center sm:gap-4 sm:bg-transparent sm:p-0">
              <label className="inline-flex min-h-10 items-center gap-3 text-ink-soft">
                <input
                  type="checkbox"
                  className="h-5 w-5 accent-accent"
                  checked={openOnly}
                  onChange={(e) => {
                    setOpenOnly(e.target.checked);
                    setPage(1);
                  }}
                />
                Open deadlines only
              </label>

              {mode === "browse" && profile ? (
                <label className="inline-flex min-h-10 items-center gap-3 text-ink-soft">
                  <input
                    type="checkbox"
                    className="h-5 w-5 accent-accent"
                    checked={eligibleForMe}
                    onChange={(e) => {
                      setEligibleForMe(e.target.checked);
                      setPage(1);
                    }}
                  />
                  Eligible for my grade/country
                </label>
              ) : null}

              {mode === "browse" ? (
                <label className="inline-flex min-h-10 flex-1 items-center gap-2 text-ink-soft sm:min-w-[12rem] sm:flex-none">
                  <span className="shrink-0">Sort</span>
                  <select
                    value={sort}
                    onChange={(e) => {
                      setSort(e.target.value as OpportunitySort);
                      setPage(1);
                    }}
                    className="min-h-10 flex-1 rounded-md border border-line bg-paper px-2 py-2 text-base outline-none focus:border-accent sm:min-h-0 sm:flex-none sm:py-1.5 sm:text-sm"
                  >
                    <option value="deadline_asc">Deadline soonest</option>
                    <option value="deadline_desc">Deadline latest</option>
                    <option value="newest">Newest</option>
                    <option value="title">Title</option>
                  </select>
                </label>
              ) : null}
            </div>
          </div>
        </section>

        <section className="mt-4 sm:mt-6">
          <p className="text-sm text-ink-soft">
            {loading ? "Loading…" : `${total} result${total === 1 ? "" : "s"}`}
          </p>

          {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}

          {!loading && !error && total === 0 ? (
            <p className="mt-8 text-ink-soft">
              No opportunities match these filters
              {field ? ` for this field` : ""}. Try another field, clear filters, or turn off
              “Open deadlines only” to include year-round listings.
            </p>
          ) : null}

          <div className="mt-4 space-y-3 sm:mt-4 sm:space-y-0">
            {mode === "matches"
              ? matchItems.map((item) => (
                  <OpportunityRow
                    key={item.opportunity.id}
                    opportunity={item.opportunity}
                    score={item.score}
                    sharedFields={item.shared_fields}
                    reasons={item.reasons}
                    showBookmark={canPersonalize}
                    showRemindMe={canPersonalize}
                    showDone={canPersonalize}
                    bookmarked={bookmarkedIds.has(item.opportunity.id)}
                    remindMe={remindMeIds.has(item.opportunity.id)}
                    done={doneIds.has(item.opportunity.id)}
                    onBookmarkChange={(next) =>
                      setOpportunityBookmarked(item.opportunity.id, next)
                    }
                    onRemindMeChange={(next) =>
                      setOpportunityRemindMe(item.opportunity.id, next)
                    }
                    onDoneChange={(next) => setOpportunityDone(item.opportunity.id, next)}
                  />
                ))
              : items.map((item) => (
                  <OpportunityRow
                    key={item.id}
                    opportunity={item}
                    showBookmark={canPersonalize}
                    showRemindMe={canPersonalize}
                    showDone={canPersonalize}
                    bookmarked={bookmarkedIds.has(item.id)}
                    remindMe={remindMeIds.has(item.id)}
                    done={doneIds.has(item.id)}
                    onBookmarkChange={(next) => setOpportunityBookmarked(item.id, next)}
                    onRemindMeChange={(next) => setOpportunityRemindMe(item.id, next)}
                    onDoneChange={(next) => setOpportunityDone(item.id, next)}
                  />
                ))}
          </div>

          {totalPages > 1 ? (
            <div className="mt-8 flex items-center justify-between gap-4 border-t border-line pt-6">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="min-h-11 rounded-md border border-line px-3 py-2 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent disabled:opacity-40"
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
                className="min-h-11 rounded-md border border-line px-3 py-2 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent disabled:opacity-40"
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
