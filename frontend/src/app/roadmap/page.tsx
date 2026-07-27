"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { RoadPath } from "@/components/RoadPath";
import { api } from "@/lib/api";
import {
  ApiError,
  type MatchItem,
  type RoadmapResponse,
  type RoadmapStop,
} from "@/types/api";

function stopFromMatch(
  match: MatchItem,
  primaryField: RoadmapStop["primary_field"],
  order: number,
  interestCount: number,
): RoadmapStop {
  return {
    order,
    opportunity_id: match.opportunity.id,
    match,
    has_deadline: match.opportunity.deadline_at != null,
    primary_field: primaryField,
    is_strong_match: interestCount > 0 && match.shared_fields.length >= interestCount,
    is_completed: false,
  };
}

function reorderStops(stops: RoadmapStop[]): RoadmapStop[] {
  const dated = stops
    .filter((s) => s.has_deadline)
    .sort((a, b) => {
      const aTs = a.match.opportunity.deadline_at
        ? new Date(a.match.opportunity.deadline_at).getTime()
        : 0;
      const bTs = b.match.opportunity.deadline_at
        ? new Date(b.match.opportunity.deadline_at).getTime()
        : 0;
      return aTs - bTs;
    });
  const undated = stops.filter((s) => !s.has_deadline);
  return [...dated, ...undated].map((stop, i) => ({ ...stop, order: i + 1 }));
}

export default function RoadmapPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [stops, setStops] = useState<RoadmapStop[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [alternativesForId, setAlternativesForId] = useState<number | null>(null);
  const [alternatives, setAlternatives] = useState<MatchItem[]>([]);
  const [alternativesLoading, setAlternativesLoading] = useState(false);
  const [alternativesError, setAlternativesError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user || !token) {
      router.replace("/login");
      return;
    }
    if (!user.is_premium) {
      setReady(true);
      return;
    }
    if (!user.has_profile) {
      setReady(true);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const data = await api.getRoadmap(token);
        if (!cancelled) {
          setRoadmap(data);
          setStops(data.stops);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load your roadmap.");
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [loading, user, token, router]);

  function moveUndated(opportunityId: number, direction: "up" | "down") {
    setStops((current) => {
      const dated = current.filter((s) => s.has_deadline);
      const undated = current.filter((s) => !s.has_deadline);
      const index = undated.findIndex((s) => s.opportunity_id === opportunityId);
      if (index < 0) return current;
      const swapWith = direction === "up" ? index - 1 : index + 1;
      if (swapWith < 0 || swapWith >= undated.length) return current;
      const next = [...undated];
      [next[index], next[swapWith]] = [next[swapWith], next[index]];
      return [...dated, ...next].map((stop, i) => ({ ...stop, order: i + 1 }));
    });
  }

  async function onChangeStop(opportunityId: number) {
    if (!token) return;
    if (alternativesForId === opportunityId) {
      setAlternativesForId(null);
      setAlternatives([]);
      setAlternativesError(null);
      return;
    }

    const stop = stops.find((s) => s.opportunity_id === opportunityId);
    if (!stop) return;

    setAlternativesForId(opportunityId);
    setAlternatives([]);
    setAlternativesError(null);
    setAlternativesLoading(true);
    try {
      const data = await api.getRoadmapAlternatives(token, {
        excludeIds: stops.map((s) => s.opportunity_id),
        fieldSlug: stop.primary_field.slug,
      });
      setAlternatives(data.items);
      if (data.items.length === 0) {
        // Fall back to any For-you match not on the road
        const broader = await api.getRoadmapAlternatives(token, {
          excludeIds: stops.map((s) => s.opportunity_id),
        });
        setAlternatives(broader.items);
      }
    } catch (err) {
      setAlternativesError(
        err instanceof ApiError ? err.message : "Could not load alternatives.",
      );
    } finally {
      setAlternativesLoading(false);
    }
  }

  function onPickAlternative(opportunityId: number, match: MatchItem) {
    const interestCount = roadmap?.field_plans.length ?? 0;
    setStops((current) => {
      const next = current.map((stop) => {
        if (stop.opportunity_id !== opportunityId) return stop;
        return stopFromMatch(match, stop.primary_field, stop.order, interestCount);
      });
      return reorderStops(next);
    });
    setAlternativesForId(null);
    setAlternatives([]);
    setAlternativesError(null);
  }

  async function onMarkFinish(opportunityId: number) {
    if (!token) return;
    setBusyId(opportunityId);
    try {
      await api.setBookmarkStatus(token, opportunityId, "completed");
      setStops((current) =>
        current.map((stop) =>
          stop.opportunity_id === opportunityId ? { ...stop, is_completed: true } : stop,
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not mark as finished.");
    } finally {
      setBusyId(null);
    }
  }

  async function onUndoFinish(opportunityId: number) {
    if (!token) return;
    setBusyId(opportunityId);
    try {
      await api.setBookmarkStatus(token, opportunityId, "saved");
      setStops((current) =>
        current.map((stop) =>
          stop.opportunity_id === opportunityId ? { ...stop, is_completed: false } : stop,
        ),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not undo finish.");
    } finally {
      setBusyId(null);
    }
  }

  if (loading || !ready) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)] px-6 py-16">
        <p className="text-ink-soft">Loading your roadmap…</p>
      </main>
    );
  }

  if (!user?.is_premium) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)]">
        <div className="mx-auto max-w-xl px-4 py-12 sm:px-10">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            Roadmap
          </p>
          <h1 className="mt-3 font-display text-3xl font-bold text-ink">Your year on a map</h1>
          <p className="mt-3 text-ink-soft">
            Premium builds a winding year-long road from your strongest For-you matches — sized by
            grade and interests, ordered by deadline.
          </p>
          <div className="mt-8">
            <PremiumPaywall title="Unlock your roadmap" />
          </div>
        </div>
      </main>
    );
  }

  if (!user.has_profile) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)]">
        <div className="mx-auto max-w-xl px-4 py-12 sm:px-10">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            Roadmap
          </p>
          <h1 className="mt-3 font-display text-3xl font-bold text-ink">Build your profile first</h1>
          <p className="mt-3 text-ink-soft">
            We need your grade and interests to place the right stops on your road.
          </p>
          <Link
            href="/profile"
            className="mt-8 inline-flex min-h-12 items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft"
          >
            Go to profile
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-4xl px-4 py-10 sm:px-10 sm:py-12">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Roadmap
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Your year on the road
        </h1>
        {roadmap ? (
          <>
            <p className="mt-3 max-w-2xl text-ink-soft">{roadmap.summary}</p>
            <ul className="mt-6 flex flex-wrap gap-2">
              {roadmap.field_plans.map((plan) => (
                <li
                  key={plan.field.slug}
                  className="rounded-md border border-line bg-paper/80 px-3 py-1.5 text-sm text-ink"
                >
                  <span className="font-medium">{plan.field.name}</span>
                  <span className="text-ink-soft">
                    {" "}
                    · {plan.selected_count}/{plan.yearly_target}
                  </span>
                </li>
              ))}
            </ul>
          </>
        ) : null}

        {error ? <p className="mt-6 text-sm text-danger">{error}</p> : null}

        {!error && stops.length === 0 ? (
          <div className="mt-10 border-t border-line pt-8">
            <p className="text-ink-soft">
              Not enough strong For-you matches yet to fill your road. Browse opportunities and
              check back as new listings appear.
            </p>
            <Link
              href="/opportunities"
              className="mt-6 inline-flex min-h-12 items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft"
            >
              Open For you
            </Link>
          </div>
        ) : null}

        {stops.length > 0 ? (
          <div className="mt-10 border-t border-line pt-8">
            <p className="mb-6 text-sm text-ink-soft">
              Dated stops stay in deadline order. Use Change to swap a stop for another For-you
              match, or Mark finish when you complete it.
            </p>
            <RoadPath
              stops={stops}
              onMoveUndated={moveUndated}
              onChangeStop={onChangeStop}
              onPickAlternative={onPickAlternative}
              onCloseAlternatives={() => {
                setAlternativesForId(null);
                setAlternatives([]);
                setAlternativesError(null);
              }}
              onMarkFinish={onMarkFinish}
              onUndoFinish={onUndoFinish}
              alternativesForId={alternativesForId}
              alternatives={alternatives}
              alternativesLoading={alternativesLoading}
              alternativesError={alternativesError}
              busyId={busyId}
            />
          </div>
        ) : null}
      </div>
    </main>
  );
}
