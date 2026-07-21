import Link from "next/link";

import { BookmarkButton } from "@/components/BookmarkButton";
import { MarkDoneButton } from "@/components/MarkDoneButton";
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
  done?: boolean;
  onBookmarkChange?: (bookmarked: boolean) => void;
  onRemindMeChange?: (remindMe: boolean) => void;
  onDoneChange?: (done: boolean) => void;
  showBookmark?: boolean;
  showRemindMe?: boolean;
  showDone?: boolean;
};

export function OpportunityRow({
  opportunity,
  score,
  sharedFields,
  reasons,
  bookmarked = false,
  remindMe = false,
  done = false,
  onBookmarkChange,
  onRemindMeChange,
  onDoneChange,
  showBookmark = false,
  showRemindMe = false,
  showDone = false,
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
  const displayFields = sharedFields ?? opportunity.fields;
  const showActions =
    showBookmark ||
    onBookmarkChange ||
    showRemindMe ||
    onRemindMeChange ||
    showDone ||
    onDoneChange;

  return (
    <article className="rounded-lg border border-line bg-paper/70 px-3 py-4 sm:border-0 sm:border-b sm:bg-transparent sm:px-0 sm:py-6 sm:first:pt-0 sm:last:border-b-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <p className="text-[0.65rem] font-semibold uppercase tracking-[0.14em] text-accent sm:text-xs">
              {formatOpportunityType(opportunity.opportunity_type)}
            </p>
            {score != null ? (
              <span className="rounded-md bg-warm/15 px-1.5 py-0.5 text-[0.65rem] font-semibold text-warm sm:text-xs">
                Match {score}
              </span>
            ) : null}
            {done ? (
              <span className="rounded-md bg-accent/10 px-1.5 py-0.5 text-[0.65rem] font-semibold text-accent sm:text-xs">
                Done
              </span>
            ) : null}
          </div>

          <h2 className="mt-1.5 font-display text-base font-semibold leading-snug tracking-tight text-ink sm:text-xl">
            <Link href={href} className="transition hover:text-accent">
              {opportunity.title}
            </Link>
          </h2>

          <p className="mt-2 text-sm text-ink-soft">
            <span className="font-medium text-ink">{formatDeadline(opportunity.deadline_at)}</span>
            <span className="mx-1.5 text-line">·</span>
            <span>{gradeLabel}</span>
          </p>
          <p className="mt-1 line-clamp-1 text-xs text-ink-soft sm:text-sm">{countries}</p>

          {displayFields.length > 0 ? (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {displayFields.slice(0, 4).map((field) => (
                <span
                  key={field.slug}
                  className="rounded-md bg-fog px-2 py-0.5 text-[0.65rem] font-medium text-ink-soft sm:text-xs"
                >
                  {field.name}
                </span>
              ))}
              {displayFields.length > 4 ? (
                <span className="rounded-md bg-fog px-2 py-0.5 text-[0.65rem] font-medium text-ink-soft sm:text-xs">
                  +{displayFields.length - 4}
                </span>
              ) : null}
            </div>
          ) : null}

          {reasons && reasons.length > 0 ? (
            <p className="mt-2 hidden text-xs text-ink-soft/90 sm:block">{reasons.join(" · ")}</p>
          ) : null}
        </div>

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
          {showDone || onDoneChange ? (
            <MarkDoneButton
              opportunityId={opportunity.id}
              done={done}
              onChange={onDoneChange}
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

      <div className="mt-3 flex flex-wrap gap-2 sm:hidden">
        <a
          href={applyUrl}
          target="_blank"
          rel="noreferrer"
          className="inline-flex min-h-10 flex-1 items-center justify-center rounded-md bg-ink px-3 text-sm font-semibold text-paper"
        >
          Apply
        </a>
        <Link
          href={href}
          className="inline-flex min-h-10 items-center justify-center rounded-md border border-line px-3 text-sm font-medium text-ink-soft"
        >
          Details
        </Link>
        {showActions ? (
          <>
            {showBookmark || onBookmarkChange ? (
              <BookmarkButton
                opportunityId={opportunity.id}
                bookmarked={bookmarked}
                onChange={onBookmarkChange}
                className="inline-flex min-h-10 items-center justify-center rounded-md border border-line px-3 text-sm"
              />
            ) : null}
            {showDone || onDoneChange ? (
              <MarkDoneButton
                opportunityId={opportunity.id}
                done={done}
                onChange={onDoneChange}
                className="inline-flex min-h-10 items-center justify-center rounded-md border border-line px-3 text-sm"
              />
            ) : null}
            {showRemindMe || onRemindMeChange ? (
              <RemindMeButton
                opportunityId={opportunity.id}
                remindMe={remindMe}
                onChange={onRemindMeChange}
                className="inline-flex min-h-10 w-full items-center justify-center rounded-md border border-line px-3 text-sm"
              />
            ) : null}
          </>
        ) : null}
      </div>
    </article>
  );
}
