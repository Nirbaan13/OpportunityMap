import Link from "next/link";

import { BookmarkButton } from "@/components/BookmarkButton";
import { RemindMeButton } from "@/components/RemindMeButton";
import {
  formatDeadline,
  formatGradeRange,
  formatOpportunityType,
} from "@/lib/opportunity-labels";
import type { FieldOption, OpportunitySummary } from "@/types/api";

type OpportunityRowProps = {
  opportunity: OpportunitySummary;
  score?: number;
  sharedFields?: FieldOption[];
  reasons?: string[];
  bookmarked?: boolean;
  remindMe?: boolean;
  onBookmarkChange?: (bookmarked: boolean) => void;
  onRemindMeChange?: (remindMe: boolean) => void;
  showBookmark?: boolean;
  showRemindMe?: boolean;
};

export function OpportunityRow({
  opportunity,
  score,
  sharedFields,
  reasons,
  bookmarked = false,
  remindMe = false,
  onBookmarkChange,
  onRemindMeChange,
  showBookmark = false,
  showRemindMe = false,
}: OpportunityRowProps) {
  const href = `/opportunities/${opportunity.id}`;
  const applyUrl = opportunity.application_url || opportunity.source_url;
  const countries = opportunity.eligible_countries?.length
    ? opportunity.eligible_countries.join(", ")
    : "Worldwide";
  const gradeLabel = formatGradeRange(
    opportunity.grade_min,
    opportunity.grade_max,
    opportunity.grade_eligibility,
  );
  const showActions = showBookmark || onBookmarkChange || showRemindMe || onRemindMeChange;

  return (
    <article className="border-b border-line py-5 first:pt-0 last:border-b-0 sm:py-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
            {formatOpportunityType(opportunity.opportunity_type)}
            {score != null ? (
              <span className="ml-3 font-medium normal-case tracking-normal text-warm">
                Match {score}
              </span>
            ) : null}
          </p>
          <h2 className="mt-1.5 font-display text-lg font-semibold tracking-tight text-ink sm:text-xl">
            <Link href={href} className="transition hover:text-accent">
              {opportunity.title}
            </Link>
          </h2>

          <p className="mt-2 text-sm leading-relaxed text-ink-soft">
            <span className="text-ink">Due {formatDeadline(opportunity.deadline_at)}</span>
            <span className="mx-1.5 text-line">·</span>
            <span>{gradeLabel}</span>
          </p>
          <p className="mt-1 line-clamp-2 text-sm text-ink-soft sm:line-clamp-none">
            {countries}
          </p>

          {opportunity.fields.length > 0 ? (
            <p className="mt-2 line-clamp-1 text-sm text-ink-soft sm:line-clamp-none">
              {(sharedFields ?? opportunity.fields).map((field) => field.name).join(" · ")}
            </p>
          ) : null}
          {reasons && reasons.length > 0 ? (
            <p className="mt-2 hidden text-xs text-ink-soft/90 sm:block">{reasons.join(" · ")}</p>
          ) : null}
        </div>

        {/* Desktop side actions */}
        <div className="hidden shrink-0 flex-col gap-2 sm:flex sm:items-end">
          <Link
            href={href}
            className="text-sm font-medium text-accent transition hover:underline"
          >
            Details
          </Link>
          <a
            href={applyUrl}
            target="_blank"
            rel="noreferrer"
            className="text-sm font-medium text-ink-soft transition hover:text-warm"
          >
            Apply / source
          </a>
          {showBookmark || onBookmarkChange ? (
            <BookmarkButton
              opportunityId={opportunity.id}
              bookmarked={bookmarked}
              onChange={onBookmarkChange}
            />
          ) : null}
          {showRemindMe || onRemindMeChange ? (
            <RemindMeButton
              opportunityId={opportunity.id}
              remindMe={remindMe}
              onChange={onRemindMeChange}
            />
          ) : null}
        </div>
      </div>

      {/* Mobile actions: primary CTA + optional save/remind */}
      <div className="mt-4 flex flex-col gap-2 sm:hidden">
        <Link
          href={href}
          className="inline-flex min-h-12 items-center justify-center rounded-md bg-ink px-4 text-sm font-semibold text-paper"
        >
          View details
        </Link>
        <a
          href={applyUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-11 items-center justify-center rounded-md border border-line px-4 text-sm font-medium text-ink-soft"
        >
          Apply / source
        </a>
        {showActions ? (
          <div className="grid grid-cols-2 gap-2">
            {showBookmark || onBookmarkChange ? (
              <BookmarkButton
                opportunityId={opportunity.id}
                bookmarked={bookmarked}
                onChange={onBookmarkChange}
                className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-line px-3"
              />
            ) : null}
            {showRemindMe || onRemindMeChange ? (
              <RemindMeButton
                opportunityId={opportunity.id}
                remindMe={remindMe}
                onChange={onRemindMeChange}
                className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-line px-3"
              />
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}
