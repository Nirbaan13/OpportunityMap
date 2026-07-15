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

  return (
    <article className="border-b border-line py-6 first:pt-0 last:border-b-0">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">
            {formatOpportunityType(opportunity.opportunity_type)}
            {score != null ? (
              <span className="ml-3 font-medium normal-case tracking-normal text-warm">
                Match {score}
              </span>
            ) : null}
          </p>
          <h2 className="mt-1.5 font-display text-xl font-semibold tracking-tight text-ink">
            <Link href={href} className="transition hover:text-accent">
              {opportunity.title}
            </Link>
          </h2>

          {/* Desktop: compact middot line; mobile: stacked meta */}
          <p className="mt-2 hidden text-sm text-ink-soft sm:block">
            Deadline {formatDeadline(opportunity.deadline_at)}
            <span className="mx-2 text-line">·</span>
            {gradeLabel}
            <span className="mx-2 text-line">·</span>
            {countries}
          </p>
          <dl className="mt-3 grid gap-2 text-sm text-ink-soft sm:hidden">
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-ink-soft/80">
                Deadline
              </dt>
              <dd className="mt-0.5 text-ink">{formatDeadline(opportunity.deadline_at)}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-ink-soft/80">
                Grades
              </dt>
              <dd className="mt-0.5 text-ink">{gradeLabel}</dd>
            </div>
            <div>
              <dt className="text-xs font-semibold uppercase tracking-wide text-ink-soft/80">
                Countries
              </dt>
              <dd className="mt-0.5 text-ink">{countries}</dd>
            </div>
          </dl>

          {opportunity.fields.length > 0 ? (
            <p className="mt-2 text-sm text-ink-soft">
              {(sharedFields ?? opportunity.fields).map((field) => field.name).join(" · ")}
            </p>
          ) : null}
          {reasons && reasons.length > 0 ? (
            <p className="mt-2 text-xs text-ink-soft/90">{reasons.join(" · ")}</p>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-2 sm:flex sm:w-auto sm:shrink-0 sm:flex-col sm:items-stretch sm:gap-2">
          <Link
            href={href}
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-line px-3 text-sm font-medium text-accent transition hover:border-accent sm:justify-end sm:border-0 sm:px-0 sm:hover:underline"
          >
            Details
          </Link>
          <a
            href={applyUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-line px-3 text-sm font-medium text-ink-soft transition hover:border-accent hover:text-accent sm:justify-end sm:border-0 sm:px-0"
          >
            Apply / source
          </a>
          {showBookmark || onBookmarkChange ? (
            <BookmarkButton
              opportunityId={opportunity.id}
              bookmarked={bookmarked}
              onChange={onBookmarkChange}
              className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-line px-3 sm:w-auto sm:justify-end sm:border-0 sm:px-0"
            />
          ) : null}
          {showRemindMe || onRemindMeChange ? (
            <RemindMeButton
              opportunityId={opportunity.id}
              remindMe={remindMe}
              onChange={onRemindMeChange}
              className="inline-flex min-h-11 w-full items-center justify-center rounded-md border border-line px-3 sm:w-auto sm:justify-end sm:border-0 sm:px-0"
            />
          ) : null}
        </div>
      </div>
    </article>
  );
}
