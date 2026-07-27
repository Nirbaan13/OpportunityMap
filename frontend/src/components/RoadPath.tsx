"use client";

import Link from "next/link";

import { formatDeadline } from "@/lib/opportunity-labels";
import type { MatchItem, RoadmapStop } from "@/types/api";

type RoadPathProps = {
  stops: RoadmapStop[];
  onMoveUndated: (opportunityId: number, direction: "up" | "down") => void;
  onChangeStop: (opportunityId: number) => void;
  onPickAlternative: (opportunityId: number, match: MatchItem) => void;
  onCloseAlternatives: () => void;
  onMarkFinish: (opportunityId: number) => void;
  onUndoFinish: (opportunityId: number) => void;
  alternativesForId: number | null;
  alternatives: MatchItem[];
  alternativesLoading: boolean;
  alternativesError: string | null;
  busyId: number | null;
};

/** Winding vertical road with destination dots — gamified year path. */
export function RoadPath({
  stops,
  onMoveUndated,
  onChangeStop,
  onPickAlternative,
  onCloseAlternatives,
  onMarkFinish,
  onUndoFinish,
  alternativesForId,
  alternatives,
  alternativesLoading,
  alternativesError,
  busyId,
}: RoadPathProps) {
  if (stops.length === 0) return null;

  const rowH = 168;
  const topPad = 56;
  const bottomPad = 110;
  const height = Math.max(360, topPad + stops.length * rowH + bottomPad);
  const width = 720;
  const mid = width / 2;

  const points = stops.map((_, index) => {
    const y = topPad + index * rowH;
    const side = index % 2 === 0 ? -1 : 1;
    const x = mid + side * 170;
    return { x, y };
  });

  const last = points[points.length - 1];
  const finish = { x: mid, y: last.y + rowH * 0.72 };

  const pathD = [
    `M ${mid} 12`,
    ...points.map((point, index) => {
      if (index === 0) {
        return `C ${mid} 28, ${point.x} ${point.y - 44}, ${point.x} ${point.y}`;
      }
      const prev = points[index - 1];
      return `C ${prev.x} ${prev.y + rowH * 0.35}, ${point.x} ${point.y - rowH * 0.35}, ${point.x} ${point.y}`;
    }),
    `C ${last.x} ${last.y + rowH * 0.28}, ${finish.x} ${finish.y - 36}, ${finish.x} ${finish.y}`,
  ].join(" ");

  const undatedIds = stops.filter((s) => !s.has_deadline).map((s) => s.opportunity_id);

  return (
    <div className="relative mx-auto w-full max-w-3xl overflow-visible pb-4">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="pointer-events-none absolute inset-x-0 top-0 h-full w-full"
        aria-hidden
        preserveAspectRatio="xMidYMin meet"
      >
        <path
          d={pathD}
          fill="none"
          stroke="rgba(11, 31, 42, 0.14)"
          strokeWidth="18"
          strokeLinecap="round"
        />
        <path
          d={pathD}
          fill="none"
          stroke="#0f766e"
          strokeWidth="4"
          strokeLinecap="round"
          strokeDasharray="10 14"
          className="animate-road-dash"
        />
        {points.map((point, index) => (
          <g key={stops[index].opportunity_id}>
            <circle
              cx={point.x}
              cy={point.y}
              r="16"
              fill="#f7fbfc"
              stroke={stops[index].is_completed ? "#0f766e" : "#0f766e"}
              strokeWidth="3"
            />
            <circle
              cx={point.x}
              cy={point.y}
              r="6"
              fill={
                stops[index].is_completed
                  ? "#0f766e"
                  : stops[index].is_strong_match
                    ? "#ea580c"
                    : "#14b8a6"
              }
              className={stops[index].is_completed ? undefined : "animate-pulse-dot"}
            />
          </g>
        ))}
        <circle cx={finish.x} cy={finish.y} r="14" fill="#0f766e" />
        <circle cx={finish.x} cy={finish.y} r="5" fill="#f7fbfc" />
        <path
          d={`M ${finish.x + 10} ${finish.y - 22} L ${finish.x + 10} ${finish.y - 4} L ${finish.x + 34} ${finish.y - 13} Z`}
          fill="#ea580c"
        />
        <line
          x1={finish.x + 10}
          y1={finish.y - 22}
          x2={finish.x + 10}
          y2={finish.y + 10}
          stroke="#0b1f2a"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>

      <ol className="relative z-10 space-y-6 py-4" style={{ minHeight: height }}>
        {stops.map((stop, index) => {
          const side = index % 2 === 0 ? "left" : "right";
          const undatedIndex = undatedIds.indexOf(stop.opportunity_id);
          const canMoveUp = !stop.has_deadline && undatedIndex > 0;
          const canMoveDown =
            !stop.has_deadline && undatedIndex >= 0 && undatedIndex < undatedIds.length - 1;
          const showingAlternatives = alternativesForId === stop.opportunity_id;
          const busy = busyId === stop.opportunity_id;

          return (
            <li
              key={stop.opportunity_id}
              className={`flex ${side === "left" ? "justify-start pr-[42%]" : "justify-end pl-[42%]"}`}
              style={{ minHeight: rowH - 24 }}
            >
              <article
                className={`w-full max-w-sm rounded-md border bg-paper/90 px-4 py-3 shadow-[var(--shadow-soft)] backdrop-blur-sm ${
                  stop.is_completed ? "border-accent/40 opacity-90" : "border-line"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-display text-xs font-semibold uppercase tracking-[0.16em] text-accent">
                    Stop {index + 1}
                    {stop.is_completed
                      ? " · Finished"
                      : stop.is_strong_match
                        ? " · Strong match"
                        : ""}
                  </p>
                  <span className="rounded-md bg-fog px-2 py-0.5 text-xs font-medium text-ink-soft">
                    {stop.primary_field.name}
                  </span>
                </div>
                <Link
                  href={`/opportunities/${stop.opportunity_id}`}
                  className={`mt-2 block font-display text-lg font-semibold leading-snug transition hover:text-accent ${
                    stop.is_completed ? "text-ink-soft line-through" : "text-ink"
                  }`}
                >
                  {stop.match.opportunity.title}
                </Link>
                <p className="mt-1 text-sm text-ink-soft">
                  {stop.has_deadline
                    ? formatDeadline(stop.match.opportunity.deadline_at)
                    : "Deadline not given"}
                </p>
                {stop.match.shared_fields.length > 0 ? (
                  <p className="mt-2 text-xs text-ink-soft">
                    Matches: {stop.match.shared_fields.map((f) => f.name).join(" · ")}
                  </p>
                ) : null}

                <div className="mt-3 flex flex-wrap gap-2">
                  {!stop.is_completed ? (
                    <>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => onChangeStop(stop.opportunity_id)}
                        className="rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:text-accent disabled:opacity-40"
                      >
                        {showingAlternatives ? "Hide options" : "Change"}
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => onMarkFinish(stop.opportunity_id)}
                        className="rounded-md bg-ink px-2.5 py-1 text-xs font-semibold text-paper transition hover:bg-ink-soft disabled:opacity-40"
                      >
                        {busy ? "Saving…" : "Mark finish"}
                      </button>
                    </>
                  ) : (
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => onUndoFinish(stop.opportunity_id)}
                      className="rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:text-accent disabled:opacity-40"
                    >
                      {busy ? "Saving…" : "Undo finish"}
                    </button>
                  )}
                  {!stop.has_deadline && !stop.is_completed ? (
                    <>
                      <button
                        type="button"
                        disabled={!canMoveUp}
                        onClick={() => onMoveUndated(stop.opportunity_id, "up")}
                        className="rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:text-accent disabled:opacity-40"
                      >
                        Move earlier
                      </button>
                      <button
                        type="button"
                        disabled={!canMoveDown}
                        onClick={() => onMoveUndated(stop.opportunity_id, "down")}
                        className="rounded-md border border-line px-2.5 py-1 text-xs font-semibold text-ink transition hover:border-accent hover:text-accent disabled:opacity-40"
                      >
                        Move later
                      </button>
                    </>
                  ) : null}
                </div>

                {showingAlternatives ? (
                  <div className="mt-3 border-t border-line pt-3">
                    <div className="mb-2 flex items-center justify-between gap-2">
                      <p className="text-xs font-medium text-ink-soft">
                        Pick another For-you match
                      </p>
                      <button
                        type="button"
                        onClick={onCloseAlternatives}
                        className="text-xs text-ink-soft hover:text-accent"
                      >
                        Close
                      </button>
                    </div>
                    {alternativesLoading ? (
                      <p className="text-xs text-ink-soft">Loading options…</p>
                    ) : null}
                    {alternativesError ? (
                      <p className="text-xs text-danger">{alternativesError}</p>
                    ) : null}
                    {!alternativesLoading && !alternativesError && alternatives.length === 0 ? (
                      <p className="text-xs text-ink-soft">
                        No other For-you matches available right now.
                      </p>
                    ) : null}
                    <ul className="max-h-48 space-y-2 overflow-y-auto">
                      {alternatives.map((alt) => (
                        <li key={alt.opportunity.id}>
                          <button
                            type="button"
                            onClick={() => onPickAlternative(stop.opportunity_id, alt)}
                            className="w-full rounded-md border border-line bg-fog/40 px-3 py-2 text-left transition hover:border-accent"
                          >
                            <span className="block text-sm font-medium text-ink">
                              {alt.opportunity.title}
                            </span>
                            <span className="mt-0.5 block text-xs text-ink-soft">
                              {alt.opportunity.deadline_at
                                ? formatDeadline(alt.opportunity.deadline_at)
                                : "Deadline not given"}
                              {alt.shared_fields.length > 0
                                ? ` · ${alt.shared_fields.map((f) => f.name).join(", ")}`
                                : ""}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </article>
            </li>
          );
        })}
        <li className="flex justify-center pt-2">
          <p className="font-display text-xs font-semibold uppercase tracking-[0.18em] text-accent">
            Year finish
          </p>
        </li>
      </ol>
    </div>
  );
}
