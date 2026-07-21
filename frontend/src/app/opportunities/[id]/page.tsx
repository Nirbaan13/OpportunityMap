"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { BookmarkButton } from "@/components/BookmarkButton";
import { MarkDoneButton } from "@/components/MarkDoneButton";
import { RemindMeButton } from "@/components/RemindMeButton";
import { api } from "@/lib/api";
import {
  formatDeadline,
  formatGradeRange,
  formatOpportunityType,
} from "@/lib/opportunity-labels";
import { ApiError, OpportunityDetail } from "@/types/api";

export default function OpportunityDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { user, token, loading: authLoading } = useAuth();
  const [opportunity, setOpportunity] = useState<OpportunityDetail | null>(null);
  const [bookmarked, setBookmarked] = useState(false);
  const [remindMe, setRemindMe] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!Number.isFinite(id) || id <= 0) {
      setError("Opportunity not found.");
      setLoading(false);
      return;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getOpportunity(id);
        if (!cancelled) setOpportunity(data);
      } catch (err) {
        if (!cancelled) {
          setOpportunity(null);
          setError(err instanceof ApiError ? err.message : "Could not load opportunity.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (authLoading || !user || !token || !Number.isFinite(id) || id <= 0) {
      setBookmarked(false);
      setRemindMe(false);
      setDone(false);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const bookmark = await api.getBookmark(token, id);
        if (!cancelled) {
          setBookmarked(true);
          setRemindMe(bookmark.remind_me);
          setDone(bookmark.status === "completed");
        }
      } catch (err) {
        if (!cancelled) {
          setBookmarked(false);
          setRemindMe(false);
          setDone(false);
          if (!(err instanceof ApiError && err.status === 404)) {
            // ignore non-404; bookmark control still works
          }
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [authLoading, user, token, id]);

  if (loading) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)] px-4 py-12 sm:px-6 sm:py-16">
        <p className="text-ink-soft">Loading…</p>
      </main>
    );
  }

  if (error || !opportunity) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)] px-4 py-12 sm:px-6 sm:py-16">
        <p className="text-danger">{error ?? "Opportunity not found."}</p>
        <Link href="/opportunities" className="mt-4 inline-block text-accent hover:underline">
          Back to opportunities
        </Link>
      </main>
    );
  }

  const applyUrl = opportunity.application_url || opportunity.source_url;

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-3xl px-4 py-6 pb-28 sm:px-10 sm:py-10 sm:pb-10">
        <Link href="/opportunities" className="text-sm text-accent hover:underline">
          ← All opportunities
        </Link>

        <p className="mt-6 text-xs font-semibold uppercase tracking-[0.14em] text-accent sm:mt-8">
          {formatOpportunityType(opportunity.opportunity_type)}
        </p>
        <h1 className="mt-2 font-display text-2xl font-bold leading-snug tracking-tight text-ink sm:mt-3 sm:text-4xl">
          {opportunity.title}
        </h1>

        <dl className="mt-6 grid gap-3 rounded-lg border border-line bg-paper/70 p-4 text-sm sm:mt-8 sm:grid-cols-2 sm:gap-4 sm:border-y sm:bg-transparent sm:p-0 sm:py-6">
          <div>
            <dt className="text-xs uppercase tracking-wide text-ink-soft">Deadline</dt>
            <dd className="mt-1 font-medium text-ink">{formatDeadline(opportunity.deadline_at)}</dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-ink-soft">Grade</dt>
            <dd className="mt-1 font-medium text-ink">
              {formatGradeRange(
                opportunity.grade_min,
                opportunity.grade_max,
                opportunity.grade_eligibility,
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-ink-soft">Countries</dt>
            <dd className="mt-1 font-medium text-ink">
              {opportunity.eligible_countries?.length
                ? opportunity.eligible_countries.join(", ")
                : "Worldwide"}
            </dd>
          </div>
          <div>
            <dt className="text-xs uppercase tracking-wide text-ink-soft">Source</dt>
            <dd className="mt-1 font-medium text-ink">{opportunity.source_name}</dd>
          </div>
        </dl>

        {opportunity.fields.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-1.5 sm:mt-6">
            {opportunity.fields.map((field) => (
              <span
                key={field.slug}
                className="rounded-md bg-fog px-2 py-1 text-xs font-medium text-ink-soft"
              >
                {field.name}
              </span>
            ))}
          </div>
        ) : null}

        {opportunity.description ? (
          <section className="mt-6 sm:mt-8">
            <h2 className="font-display text-lg font-semibold text-ink">About</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-soft sm:text-base">
              {opportunity.description}
            </p>
          </section>
        ) : null}

        {opportunity.experience_requirements ? (
          <section className="mt-6 sm:mt-8">
            <h2 className="font-display text-lg font-semibold text-ink">Experience</h2>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-ink-soft sm:text-base">
              {opportunity.experience_requirements}
            </p>
          </section>
        ) : null}

        <div className="mt-8 hidden flex-wrap items-center gap-3 sm:flex">
          <a
            href={applyUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-12 items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft"
          >
            Open application / source
          </a>
          <a
            href={opportunity.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-12 items-center justify-center rounded-md border border-line px-5 py-3 text-sm font-semibold text-ink-soft transition hover:border-accent hover:text-accent"
          >
            Source page
          </a>
          <BookmarkButton
            opportunityId={opportunity.id}
            bookmarked={bookmarked}
            onChange={(next) => {
              setBookmarked(next);
              if (!next) {
                setRemindMe(false);
                setDone(false);
              }
            }}
            className="inline-flex min-h-12 items-center justify-center rounded-md border border-line px-5 py-3"
          />
          <MarkDoneButton
            opportunityId={opportunity.id}
            done={done}
            onChange={(next) => {
              setDone(next);
              if (next) {
                setBookmarked(true);
                setRemindMe(false);
              }
            }}
            className="inline-flex min-h-12 items-center justify-center rounded-md border border-line px-5 py-3"
          />
          <RemindMeButton
            opportunityId={opportunity.id}
            remindMe={remindMe}
            onChange={(next) => {
              setRemindMe(next);
              if (next) setBookmarked(true);
            }}
            className="inline-flex min-h-12 items-center justify-center rounded-md border border-line px-5 py-3"
          />
        </div>
        <p className="mt-3 hidden text-xs text-ink-soft sm:block">
          Mark done counts this opportunity toward your profile field progress. Remind me
          emails your registered address and adds a website alert 10 days and 1 day before
          the deadline.
        </p>
      </div>

      <div
        className="fixed inset-x-0 bottom-[calc(3.25rem+env(safe-area-inset-bottom))] z-20 border-t border-line bg-paper/95 px-3 py-2 backdrop-blur-md sm:hidden"
      >
        <div className="flex flex-wrap gap-2">
          <a
            href={applyUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-10 flex-1 items-center justify-center rounded-md bg-ink px-3 text-sm font-semibold text-paper"
          >
            Apply
          </a>
          <BookmarkButton
            opportunityId={opportunity.id}
            bookmarked={bookmarked}
            onChange={(next) => {
              setBookmarked(next);
              if (!next) {
                setRemindMe(false);
                setDone(false);
              }
            }}
            className="inline-flex min-h-10 items-center justify-center rounded-md border border-line px-3 text-sm"
          />
          <MarkDoneButton
            opportunityId={opportunity.id}
            done={done}
            onChange={(next) => {
              setDone(next);
              if (next) {
                setBookmarked(true);
                setRemindMe(false);
              }
            }}
            className="inline-flex min-h-10 items-center justify-center rounded-md border border-line px-3 text-sm"
          />
          <RemindMeButton
            opportunityId={opportunity.id}
            remindMe={remindMe}
            onChange={(next) => {
              setRemindMe(next);
              if (next) setBookmarked(true);
            }}
            className="inline-flex min-h-10 flex-1 items-center justify-center rounded-md border border-line px-3 text-sm"
          />
        </div>
      </div>
    </main>
  );
}
