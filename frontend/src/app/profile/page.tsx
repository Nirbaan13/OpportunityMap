"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { ProfileForm } from "@/components/ProfileForm";
import { api } from "@/lib/api";
import { ApiError, type ActivityOption, type Profile } from "@/types/api";

export default function ProfilePage() {
  const { user, token, loading, refreshUser, logout } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [catalog, setCatalog] = useState<ActivityOption[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [editing, setEditing] = useState(false);
  const [activityPending, setActivityPending] = useState<string | null>(null);
  const [activityError, setActivityError] = useState<string | null>(null);

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

    let cancelled = false;
    (async () => {
      try {
        const [data, activities] = await Promise.all([
          api.getProfile(token).catch((err) => {
            if (err instanceof ApiError && err.status === 404) return null;
            throw err;
          }),
          api.listActivities().catch(() => [] as ActivityOption[]),
        ]);
        if (!cancelled) {
          setProfile(data);
          setCatalog(activities);
          setEditing(!data);
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(err instanceof ApiError ? err.message : "Could not load profile.");
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [loading, user, token, router]);

  async function updateActivityStatus(slug: string, next: "none" | "planned" | "completed") {
    if (!token || !profile) return;
    setActivityPending(slug);
    setActivityError(null);

    const completed = new Set(profile.completed_activities.map((item) => item.slug));
    const planned = new Set(profile.planned_activities.map((item) => item.slug));
    completed.delete(slug);
    planned.delete(slug);
    if (next === "completed") completed.add(slug);
    if (next === "planned") planned.add(slug);

    try {
      const saved = await api.updateProfile(token, {
        full_name: profile.full_name,
        location: profile.location,
        grade_level: profile.grade_level,
        country_code: profile.country_code,
        research_experience: profile.research_experience,
        olympiad_experience: profile.olympiad_experience,
        interest_slugs: profile.interests.map((item) => item.slug),
        completed_activity_slugs: [...completed],
        planned_activity_slugs: [...planned],
      });
      setProfile(saved);
      await refreshUser();
    } catch (err) {
      setActivityError(err instanceof ApiError ? err.message : "Could not update activity.");
    } finally {
      setActivityPending(null);
    }
  }

  if (loading || !ready || !token) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)] px-6 py-16">
        <p className="text-ink-soft">Loading…</p>
      </main>
    );
  }

  if (!user?.is_premium) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)]">
        <div className="mx-auto max-w-xl px-4 py-12 sm:px-10">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            Premium
          </p>
          <h1 className="mt-3 font-display text-3xl font-bold text-ink">Profile is premium</h1>
          <p className="mt-3 text-ink-soft">
            You can browse opportunities free. Unlock premium to save your grade, interests,
            and experience for recommendations and alerts.
          </p>
          <div className="mt-8">
            <PremiumPaywall title="Unlock profile & recommendations" />
          </div>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="mt-8 text-sm font-medium text-ink-soft transition hover:text-warm"
          >
            Log out
          </button>
        </div>
      </main>
    );
  }

  if (!profile || editing) {
    return (
      <main className="atmosphere min-h-[calc(100dvh-4rem)]">
        <div className="mx-auto max-w-3xl px-4 py-10 sm:px-10 sm:py-12">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            Your profile
          </p>
          <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            {profile ? "Edit profile" : "Build your student profile"}
          </h1>
          <p className="mt-3 max-w-2xl text-ink-soft">
            Grade, country, interests, and activities drive eligibility filters and match
            scoring.
          </p>

          {loadError ? <p className="mt-6 text-sm text-danger">{loadError}</p> : null}

          <div className="mt-10 border-t border-line pt-10">
            <ProfileForm
              token={token}
              existing={profile}
              onCancel={profile ? () => setEditing(false) : undefined}
              onSaved={async (saved) => {
                setProfile(saved);
                setEditing(false);
                await refreshUser();
              }}
            />
          </div>
        </div>
      </main>
    );
  }

  const completedSlugs = new Set(profile.completed_activities.map((item) => item.slug));
  const plannedSlugs = new Set(profile.planned_activities.map((item) => item.slug));

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)]">
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-10 sm:py-12">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Your profile
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          {profile.full_name}
        </h1>
        <p className="mt-3 text-ink-soft">
          Grade {profile.grade_level} · {profile.location} · {profile.country_code}
        </p>
        <p className="mt-1 text-sm text-ink-soft">{user.email}</p>

        <section className="mt-10 border-t border-line pt-8">
          <h2 className="font-display text-xl font-semibold text-ink">Your activity map</h2>
          <p className="mt-3 text-ink-soft leading-relaxed">{profile.insight_summary}</p>

          {profile.field_insights.length > 0 ? (
            <ul className="mt-6 grid gap-3 sm:grid-cols-2">
              {profile.field_insights.map((insight) => (
                <li
                  key={insight.field.slug}
                  className="rounded-md border border-line bg-paper/80 px-4 py-3"
                >
                  <p className="font-medium text-ink">{insight.field.name}</p>
                  <p className="mt-1 text-sm text-ink-soft">
                    {insight.completed_count} done
                    {insight.planned_count > 0 ? ` · ${insight.planned_count} saved` : ""}
                  </p>
                  <p
                    className={`mt-2 text-xs font-semibold uppercase tracking-wide ${
                      insight.status === "short"
                        ? "text-warm"
                        : insight.status === "strong"
                          ? "text-accent"
                          : "text-ink-soft"
                    }`}
                  >
                    {insight.status === "short"
                      ? "A little short"
                      : insight.status === "strong"
                        ? "Looking strong"
                        : "On track"}
                  </p>
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section className="mt-10 border-t border-line pt-8">
          <h2 className="font-display text-xl font-semibold text-ink">Completed</h2>
          {profile.completed_activities.length === 0 ? (
            <p className="mt-3 text-sm text-ink-soft">
              Nothing marked done yet. Use Mark done on an activity below.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {profile.completed_activities.map((item) => (
                <li key={item.slug} className="rounded-md bg-warm/10 px-3 py-2.5 text-sm text-ink">
                  {item.name}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mt-8">
          <h2 className="font-display text-xl font-semibold text-ink">Saved for later</h2>
          {profile.planned_activities.length === 0 ? (
            <p className="mt-3 text-sm text-ink-soft">
              No planned activities yet. Save ones you want to do next.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {profile.planned_activities.map((item) => (
                <li
                  key={item.slug}
                  className="rounded-md bg-accent/10 px-3 py-2.5 text-sm text-ink"
                >
                  {item.name}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="mt-10 border-t border-line pt-8">
          <h2 className="font-display text-xl font-semibold text-ink">All activities</h2>
          <p className="mt-2 text-sm text-ink-soft">
            Save for later if you plan to do it. Mark done when you have completed it.
          </p>
          {activityError ? <p className="mt-3 text-sm text-danger">{activityError}</p> : null}
          <div className="mt-4 space-y-3">
            {catalog.map((activity) => {
              const status = completedSlugs.has(activity.slug)
                ? "completed"
                : plannedSlugs.has(activity.slug)
                  ? "planned"
                  : "none";
              const busy = activityPending === activity.slug;
              return (
                <div
                  key={activity.slug}
                  className="flex flex-col gap-3 rounded-md border border-line bg-paper px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <p className="text-sm font-medium text-ink">{activity.name}</p>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void updateActivityStatus(
                          activity.slug,
                          status === "planned" ? "none" : "planned",
                        )
                      }
                      className={`min-h-10 rounded-md border px-3 text-sm font-medium transition disabled:opacity-50 ${
                        status === "planned"
                          ? "border-accent bg-accent/10 text-ink"
                          : "border-line text-ink-soft hover:border-accent/40"
                      }`}
                    >
                      {status === "planned" ? "Saved for later" : "Save for later"}
                    </button>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() =>
                        void updateActivityStatus(
                          activity.slug,
                          status === "completed" ? "none" : "completed",
                        )
                      }
                      className={`min-h-10 rounded-md border px-3 text-sm font-medium transition disabled:opacity-50 ${
                        status === "completed"
                          ? "border-warm/60 bg-warm/10 text-ink"
                          : "border-line text-ink-soft hover:border-warm/40"
                      }`}
                    >
                      {status === "completed" ? "Marked done" : "Mark done"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {profile.interests.length > 0 ? (
          <section className="mt-10 border-t border-line pt-8">
            <h2 className="font-display text-xl font-semibold text-ink">Interests</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {profile.interests.map((interest) => (
                <span
                  key={interest.slug}
                  className="rounded-md border border-line bg-fog px-3 py-1.5 text-sm text-ink"
                >
                  {interest.name}
                </span>
              ))}
            </div>
          </section>
        ) : null}

        <div className="mt-12 border-t border-line pt-8">
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="inline-flex min-h-12 w-full items-center justify-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft sm:w-auto"
          >
            Edit profile
          </button>
          <p className="mt-6 text-sm text-ink-soft">
            Open{" "}
            <Link href="/opportunities" className="text-accent hover:underline">
              Opportunities
            </Link>{" "}
            and switch to <span className="font-medium text-ink">For you</span> for ranked
            matches.
          </p>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/");
            }}
            className="mt-6 text-sm font-medium text-ink-soft transition hover:text-warm"
          >
            Log out
          </button>
        </div>
      </div>
    </main>
  );
}
