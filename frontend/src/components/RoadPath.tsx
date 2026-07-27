"use client";

import Link from "next/link";

import { formatDeadline } from "@/lib/opportunity-labels";
import type { RoadmapStop } from "@/types/api";

type RoadPathProps = {
  stops: RoadmapStop[];
  onMoveUndated: (opportunityId: number, direction: "up" | "down") => void;
};

/** Winding vertical road with destination dots — gamified year path. */
export function RoadPath({ stops, onMoveUndated }: RoadPathProps) {
  if (stops.length === 0) return null;

  const rowH = 140;
  const height = Math.max(320, stops.length * rowH + 80);
  const width = 720;
  const mid = width / 2;

  // Snake: alternate left / right of center
  const points = stops.map((_, index) => {
    const y = 48 + index * rowH;
    const side = index % 2 === 0 ? -1 : 1;
    const x = mid + side * 170;
    return { x, y };
  });

  const pathD = points
    .map((point, index) => {
      if (index === 0) return `M ${mid} 16 C ${mid} 28, ${point.x} ${point.y - 40}, ${point.x} ${point.y}`;
      const prev = points[index - 1];
      const c1x = prev.x;
      const c1y = prev.y + rowH * 0.35;
      const c2x = point.x;
      const c2y = point.y - rowH * 0.35;
      return `C ${c1x} ${c1y}, ${c2x} ${c2y}, ${point.x} ${point.y}`;
    })
    .join(" ");

  const undatedIds = stops.filter((s) => !s.has_deadline).map((s) => s.opportunity_id);

  return (
    <div className="relative mx-auto w-full max-w-3xl overflow-hidden">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="pointer-events-none absolute inset-0 h-full w-full"
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
            <circle cx={point.x} cy={point.y} r="16" fill="#f7fbfc" stroke="#0f766e" strokeWidth="3" />
            <circle
              cx={point.x}
              cy={point.y}
              r="6"
              fill={stops[index].is_strong_match ? "#ea580c" : "#14b8a6"}
              className="animate-pulse-dot"
            />
          </g>
        ))}
      </svg>

      <ol className="relative z-10 space-y-6 py-4" style={{ minHeight: height }}>
        {stops.map((stop, index) => {
          const side = index % 2 === 0 ? "left" : "right";
          const undatedIndex = undatedIds.indexOf(stop.opportunity_id);
          const canMoveUp = !stop.has_deadline && undatedIndex > 0;
          const canMoveDown =
            !stop.has_deadline && undatedIndex >= 0 && undatedIndex < undatedIds.length - 1;

          return (
            <li
              key={stop.opportunity_id}
              className={`flex ${side === "left" ? "justify-start pr-[42%]" : "justify-end pl-[42%]"}`}
              style={{ minHeight: rowH - 24 }}
            >
              <article className="w-full max-w-sm rounded-md border border-line bg-paper/90 px-4 py-3 shadow-[var(--shadow-soft)] backdrop-blur-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-display text-xs font-semibold uppercase tracking-[0.16em] text-accent">
                    Stop {index + 1}
                    {stop.is_strong_match ? " · Strong match" : ""}
                  </p>
                  <span className="rounded-md bg-fog px-2 py-0.5 text-xs font-medium text-ink-soft">
                    {stop.primary_field.name}
                  </span>
                </div>
                <Link
                  href={`/opportunities/${stop.opportunity_id}`}
                  className="mt-2 block font-display text-lg font-semibold leading-snug text-ink transition hover:text-accent"
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
                {!stop.has_deadline ? (
                  <div className="mt-3 flex gap-2">
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
                  </div>
                ) : null}
              </article>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
