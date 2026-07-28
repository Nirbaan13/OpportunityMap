"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { RoadPath } from "@/components/RoadPath";
import { api } from "@/lib/api";
import {
  ApiError,
  type MatchItem,
  type OpportunitySummary,
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

function stopFromOpportunity(
  opportunity: OpportunitySummary,
  primaryField: RoadmapStop["primary_field"],
  order: number,
): RoadmapStop {
  const shared = opportunity.fields.filter((f) => f.slug === primaryField.slug);
  return {
    order,
    opportunity_id: opportunity.id,
    match: {
      opportunity,
      score: 0,
      shared_fields: shared,
      reasons: [],
    },
    has_deadline: opportunity.deadline_at != null,
    primary_field: primaryField,
    is_strong_match: shared.length > 0,
    is_completed: false,
  };
}

/** Finished stops stay at the front (covered road); open stops keep deadline order. */
function arrangeStops(stops: RoadmapStop[]): RoadmapStop[] {
  const done = stops.filter((s) => s.is_completed);
  const open = stops.filter((s) => !s.is_completed);
  const dated = open
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
  const undated = open.filter((s) => !s.has_deadline);
  return [...done, ...dated, ...undated].map((stop, i) => ({ ...stop, order: i + 1 }));
}

export default function RoadmapPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
  const [stops, setStops] = useState<RoadmapStop[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [changePanelForId, setChangePanelForId] = useState<number | null>(null);
  const [manualOptions, setManualOptions] = useState<OpportunitySummary[]>([]);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualQuery, setManualQuery] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [progressPulseKey, setProgressPulseKey] = useState(0);

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
          setStops(arrangeStops(data.stops));
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

  function closeChangePanel() {
    setChangePanelForId(null);
    setManualOptions([]);
    setManualError(null);
    setManualQuery("");
  }

  function moveUndated(opportunityId: number, direction: "up" | "down") {
    setStops((current) => {
      const done = current.filter((s) => s.is_completed);
      const open = current.filter((s) => !s.is_completed);
      const dated = open.filter((s) => s.has_deadline);
      const undated = open.filter((s) => !s.has_deadline);
      const index = undated.findIndex((s) => s.opportunity_id === opportunityId);
      if (index < 0) return current;
      const swapWith = direction === "up" ? index - 1 : index + 1;
      if (swapWith < 0 || swapWith >= undated.length) return current;
      const next = [...undated];
      [next[index], next[swapWith]] = [next[swapWith], next[index]];
      return [...done, ...dated, ...next].map((stop, i) => ({ ...stop, order: i + 1 }));
    });
  }

  async function loadManualOptions(excludeIds: number[], query = "") {
    setManualLoading(true);
    setManualError(null);
    try {
      const data = await api.listOpportunities({
        q: query || undefined,
        open_only: false,
        sort: "deadline_asc",
        page: 1,
        page_size: 40,
      });
      const exclude = new Set(excludeIds);
      setManualOptions(data.items.filter((item) => !exclude.has(item.id)));
    } catch (err) {
      setManualOptions([]);
      setManualError(err instanceof ApiError ? err.message : "Could not load openings.");
    } finally {
      setManualLoading(false);
    }
  }

  async function onOpenChangePanel(opportunityId: number) {
    if (changePanelForId === opportunityId) {
      closeChangePanel();
      return;
    }
    setChangePanelForId(opportunityId);
    setManualQuery("");
    await loadManualOptions(
      stops.map((s) => s.opportunity_id),
      "",
    );
  }

  async function onManualSearch(event: FormEvent) {
    event.preventDefault();
    if (changePanelForId == null) return;
    await loadManualOptions(
      stops.map((s) => s.opportunity_id),
      manualQuery.trim(),
    );
  }

  async function onChangeAuto(opportunityId: number) {
    if (!token) return;
    const stop = stops.find((s) => s.opportunity_id === opportunityId);
    if (!stop) return;

    setBusyId(opportunityId);
    setError(null);
    try {
      let data = await api.getRoadmapAlternatives(token, {
        excludeIds: stops.map((s) => s.opportunity_id),
        fieldSlug: stop.primary_field.slug,
      });
      if (data.items.length === 0) {
        data = await api.getRoadmapAlternatives(token, {
          excludeIds: stops.map((s) => s.opportunity_id),
        });
      }
      const pick = data.items[0];
      if (!pick) {
        setError("No other For-you matches available to swap in automatically.");
        return;
      }
      const interestCount = roadmap?.field_plans.length ?? 0;
      setStops((current) =>
        arrangeStops(
          current.map((s) =>
            s.opportunity_id === opportunityId
              ? stopFromMatch(pick, s.primary_field, s.order, interestCount)
              : s,
          ),
        ),
      );
      closeChangePanel();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not auto-change this stop.");
    } finally {
      setBusyId(null);
    }
  }

  function onPickManual(opportunityId: number, opportunity: OpportunitySummary) {
    setStops((current) =>
      arrangeStops(
        current.map((s) =>
          s.opportunity_id === opportunityId
            ? stopFromOpportunity(opportunity, s.primary_field, s.order)
            : s,
        ),
      ),
    );
    closeChangePanel();
  }

  async function onMarkFinish(opportunityId: number) {
    if (!token) return;
    setBusyId(opportunityId);
    try {
      await api.setBookmarkStatus(token, opportunityId, "completed");
      setStops((current) => {
        const marked = current.map((stop) =>
          stop.opportunity_id === opportunityId ? { ...stop, is_completed: true } : stop,
        );
        // Keep prior finished order; place newly finished right after the last done before
        const previouslyDone = marked.filter(
          (s) => s.is_completed && s.opportunity_id !== opportunityId,
        );
        const justDone = marked.find((s) => s.opportunity_id === opportunityId)!;
        const open = marked.filter((s) => !s.is_completed);
        const dated = open
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
        const undated = open.filter((s) => !s.has_deadline);
        return [...previouslyDone, justDone, ...dated, ...undated].map((stop, i) => ({
          ...stop,
          order: i + 1,
        }));
      });
      setProgressPulseKey((k) => k + 1);
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
        arrangeStops(
          current.map((stop) =>
            stop.opportunity_id === opportunityId ? { ...stop, is_completed: false } : stop,
          ),
        ),
      );
      setProgressPulseKey((k) => k + 1);
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
              Finished stops move to the covered part of the road. Change automatically swaps in
              another For-you match, or pick manually from all openings.
            </p>
            <RoadPath
              stops={stops}
              onMoveUndated={moveUndated}
              onChangeAuto={onChangeAuto}
              onOpenManual={onOpenChangePanel}
              onPickManual={onPickManual}
              onCloseChangePanel={closeChangePanel}
              onMarkFinish={onMarkFinish}
              onUndoFinish={onUndoFinish}
              changePanelForId={changePanelForId}
              manualOptions={manualOptions}
              manualLoading={manualLoading}
              manualError={manualError}
              manualQuery={manualQuery}
              onManualQueryChange={setManualQuery}
              onManualSearch={onManualSearch}
              busyId={busyId}
              progressPulseKey={progressPulseKey}
            />
          </div>
        ) : null}
      </div>
    </main>
  );
}
