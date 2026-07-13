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
  const { user, token, loading, refreshUser } = useAuth();
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

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
        const data = await api.getProfile(token);
        if (!cancelled) setProfile(data);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          if (!cancelled) setProfile(null);
        } else if (!cancelled) {
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
      <main className="atmosphere min-h-[calc(100vh-5rem)] px-6 py-16">
        <p className="text-ink-soft">Loading…</p>
      </main>
    );
  }

  if (!user?.is_premium) {
    return (
      <main className="atmosphere min-h-[calc(100vh-5rem)]">
        <div className="mx-auto max-w-xl px-6 py-12 sm:px-10">
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
        </div>
      </main>
    );
  }

  return (
    <main className="atmosphere min-h-[calc(100vh-5rem)]">
      <div className="mx-auto max-w-3xl px-6 py-12 sm:px-10">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Your profile
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          {profile ? "Edit your student profile" : "Build your student profile"}
        </h1>
        <p className="mt-3 max-w-2xl text-ink-soft">
          Grade, country, interests, and experience drive eligibility filters and match
          scoring. Signed in as <span className="font-medium text-ink">{user?.email}</span>.
        </p>

        {loadError ? (
          <p className="mt-6 text-sm text-danger">{loadError}</p>
        ) : (
          <div className="mt-10 border-t border-line pt-10">
            <ProfileForm
              token={token}
              existing={profile}
              onSaved={async (saved) => {
                setProfile(saved);
                await refreshUser();
              }}
            />
          </div>
        )}

        <p className="mt-12 text-sm text-ink-soft">
          After saving, open{" "}
          <Link href="/opportunities" className="text-accent hover:underline">
            Opportunities
          </Link>{" "}
          and switch to <span className="font-medium text-ink">For you</span> for ranked
          matches.{" "}
          <Link href="/" className="text-accent hover:underline">
            Back home
          </Link>
        </p>
      </div>
    </main>
  );
}
