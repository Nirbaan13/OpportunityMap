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

  return (
    <article className="border-b border-line py-6 first:pt-0 last:border-b-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
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
          <p className="mt-2 text-sm text-ink-soft">
            Deadline {formatDeadline(opportunity.deadline_at)}
            <span className="mx-2 text-line">·</span>
            {formatGradeRange(
              opportunity.grade_min,
              opportunity.grade_max,
              opportunity.grade_eligibility,
            )}
            <span className="mx-2 text-line">·</span>
            {opportunity.eligible_countries?.length
              ? opportunity.eligible_countries.join(", ")
              : "Worldwide"}
          </p>
          {opportunity.fields.length > 0 ? (
            <p className="mt-2 text-sm text-ink-soft">
              {(sharedFields ?? opportunity.fields).map((field) => field.name).join(" · ")}
            </p>
          ) : null}
          {reasons && reasons.length > 0 ? (
            <p className="mt-2 text-xs text-ink-soft/90">{reasons.join(" · ")}</p>
          ) : null}
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:items-end">
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
    </article>
  );
}
