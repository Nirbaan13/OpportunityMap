"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";
import { ProfileForm } from "@/components/ProfileForm";
import { api } from "@/lib/api";
import { ApiError, type Profile } from "@/types/api";

export default function ProfilePage() {
  const { user, token, loading, refreshUser, updateUser, logout } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [editing, setEditing] = useState(false);
  const [renewing, setRenewing] = useState(false);
  const [autoRenewSaving, setAutoRenewSaving] = useState(false);
  const [autoRenewError, setAutoRenewError] = useState<string | null>(null);

  async function toggleAutoRenew(next: boolean) {
    if (!token) return;
    setAutoRenewSaving(true);
    setAutoRenewError(null);
    try {
      const updated = await api.setAutoRenew(token, next);
      updateUser(updated);
    } catch (err) {
      setAutoRenewError(
        err instanceof ApiError ? err.message : "Could not update auto-renew.",
      );
    } finally {
      setAutoRenewSaving(false);
    }
  }

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
        const data = await api.getProfile(token).catch((err) => {
          if (err instanceof ApiError && err.status === 404) return null;
          throw err;
        });
        if (!cancelled) {
          setProfile(data);
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
            and mark opportunities done for field progress.
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
            Grade, country, and interests drive eligibility and matches. Mark individual
            opportunities as done from the Opportunities page to track field progress.
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
          <h2 className="font-display text-xl font-semibold text-ink">Your field progress</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Paced from when you joined, with a higher bar in higher grades. One done early
            is fine; the same count late in your membership year means you&apos;re behind.
          </p>
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
                    {insight.completed_count} opportunit
                    {insight.completed_count === 1 ? "y" : "ies"} done this membership year
                    {insight.planned_count > 0
                      ? ` · ${insight.planned_count} saved`
                      : ""}
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
                      ? "Behind pace"
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
          <h2 className="font-display text-xl font-semibold text-ink">
            Done this membership year
          </h2>
          {(profile.completed_opportunities ?? []).length === 0 ? (
            <p className="mt-3 text-sm text-ink-soft">
              Nothing marked done in this membership year yet. Open{" "}
              <Link href="/opportunities" className="text-accent hover:underline">
                Opportunities
              </Link>{" "}
              and tap <span className="font-medium text-ink">Mark done</span> on listings you
              finished.
            </p>
          ) : (
            <ul className="mt-4 space-y-2">
              {profile.completed_opportunities.map((item) => (
                <li key={item.id}>
                  <Link
                    href={`/opportunities/${item.id}`}
                    className="block rounded-md bg-warm/10 px-3 py-2.5 text-sm text-ink transition hover:bg-warm/15"
                  >
                    <span className="font-medium">{item.title}</span>
                    {item.fields.length > 0 ? (
                      <span className="mt-1 block text-xs text-ink-soft">
                        {item.fields.map((f) => f.name).join(" · ")}
                      </span>
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          )}
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

        <section className="mt-10 border-t border-line pt-8">
          <h2 className="font-display text-xl font-semibold text-ink">Membership</h2>
          {user.premium_until ? (
            <p className="mt-1 text-sm text-ink-soft">
              Your Premium year is valid until{" "}
              <span className="font-medium text-ink">
                {new Date(user.premium_until).toLocaleDateString()}
              </span>
              .
            </p>
          ) : null}

          <label className="mt-5 flex items-start gap-3">
            <input
              type="checkbox"
              checked={user.auto_renew}
              disabled={autoRenewSaving}
              onChange={(event) => void toggleAutoRenew(event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-line text-accent focus:ring-accent"
            />
            <span className="text-sm text-ink-soft">
              <span className="font-medium text-ink">Auto-renew reminders</span>
              <br />
              We&apos;ll remind you by email and in your alerts a few days before your year
              ends. You are never charged automatically&nbsp;— renewing is a quick manual
              payment that adds another 365 days.
            </span>
          </label>
          {autoRenewError ? (
            <p className="mt-2 text-sm text-danger">{autoRenewError}</p>
          ) : null}

          <div className="mt-6">
            {renewing ? (
              <PremiumPaywall title="Renew membership" renew compact />
            ) : (
              <button
                type="button"
                onClick={() => setRenewing(true)}
                className="rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
              >
                Renew now / extend another year
              </button>
            )}
          </div>
        </section>

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
            to browse, save, and mark listings done.
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
