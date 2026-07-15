"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { BookmarkButton } from "@/components/BookmarkButton";
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
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const bookmark = await api.getBookmark(token, id);
        if (!cancelled) {
          setBookmarked(true);
          setRemindMe(bookmark.remind_me);
        }
      } catch (err) {
        if (!cancelled) {
          setBookmarked(false);
          setRemindMe(false);
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
      <main className="atmosphere min-h-[calc(100vh-5rem)] px-6 py-16">
        <p className="text-ink-soft">Loading…</p>
      </main>
    );
  }

  if (error || !opportunity) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)] px-6 py-16">
        <p className="text-danger">{error ?? "Opportunity not found."}</p>
        <Link href="/opportunities" className="mt-4 inline-block text-accent hover:underline">
          Back to opportunities
        </Link>
      </main>
    );
  }

  const applyUrl = opportunity.application_url || opportunity.source_url;

  return (
    <main className="atmosphere min-h-[calc(100vh-5rem)]">
      <div className="mx-auto max-w-3xl px-6 py-10 sm:px-10">
        <Link href="/opportunities" className="text-sm text-accent hover:underline">
          ← All opportunities
        </Link>

        <p className="mt-8 text-xs font-semibold uppercase tracking-[0.14em] text-accent">
          {formatOpportunityType(opportunity.opportunity_type)}
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          {opportunity.title}
        </h1>

        <dl className="mt-8 grid gap-4 border-y border-line py-6 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-ink-soft">Deadline</dt>
            <dd className="mt-1 font-medium text-ink">{formatDeadline(opportunity.deadline_at)}</dd>
          </div>
          <div>
            <dt className="text-ink-soft">Grade</dt>
            <dd className="mt-1 font-medium text-ink">
              {formatGradeRange(
                opportunity.grade_min,
                opportunity.grade_max,
                opportunity.grade_eligibility,
              )}
            </dd>
          </div>
          <div>
            <dt className="text-ink-soft">Countries</dt>
            <dd className="mt-1 font-medium text-ink">
              {opportunity.eligible_countries?.length
                ? opportunity.eligible_countries.join(", ")
                : "Worldwide"}
            </dd>
          </div>
          <div>
            <dt className="text-ink-soft">Source</dt>
            <dd className="mt-1 font-medium text-ink">{opportunity.source_name}</dd>
          </div>
        </dl>

        {opportunity.fields.length > 0 ? (
          <p className="mt-6 text-sm text-ink-soft">
            Fields: {opportunity.fields.map((field) => field.name).join(" · ")}
          </p>
        ) : null}

        {opportunity.description ? (
          <section className="mt-8">
            <h2 className="font-display text-lg font-semibold text-ink">About</h2>
            <p className="mt-3 whitespace-pre-wrap text-ink-soft leading-relaxed">
              {opportunity.description}
            </p>
          </section>
        ) : null}

        {opportunity.experience_requirements ? (
          <section className="mt-8">
            <h2 className="font-display text-lg font-semibold text-ink">Experience</h2>
            <p className="mt-3 whitespace-pre-wrap text-ink-soft leading-relaxed">
              {opportunity.experience_requirements}
            </p>
          </section>
        ) : null}

        <div className="mt-10 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
          <a
            href={applyUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-12 w-full items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft sm:w-auto"
          >
            Open application / source
          </a>
          <a
            href={opportunity.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-12 w-full items-center justify-center rounded-md border border-line px-5 py-3 text-sm font-semibold text-ink-soft transition hover:border-accent hover:text-accent sm:w-auto"
          >
            Source page
          </a>
          <BookmarkButton
            opportunityId={opportunity.id}
            bookmarked={bookmarked}
            onChange={(next) => {
              setBookmarked(next);
              if (!next) setRemindMe(false);
            }}
            className="inline-flex min-h-12 w-full items-center justify-center rounded-md border border-line px-5 py-3 sm:w-auto"
          />
          <RemindMeButton
            opportunityId={opportunity.id}
            remindMe={remindMe}
            onChange={(next) => {
              setRemindMe(next);
              if (next) setBookmarked(true);
            }}
            className="inline-flex min-h-12 w-full items-center justify-center rounded-md border border-line px-5 py-3 sm:w-auto"
          />
        </div>
        <p className="mt-3 text-xs text-ink-soft">
          Remind me emails your registered address and adds a website alert 10 days
          and 1 day before the deadline. Earlier (3 months / 30 days) alerts go
          automatically to students with matching interests.
        </p>
      </div>
    </main>
  );
}
