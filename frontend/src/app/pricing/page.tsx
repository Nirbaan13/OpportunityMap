"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";
import { PremiumPaywall } from "@/components/PremiumPaywall";

export default function PricingPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  return (
    <main className="atmosphere min-h-[calc(100dvh-4rem)] sm:min-h-[calc(100vh-5rem)]">
      <div className="mx-auto max-w-xl px-4 py-8 sm:px-10 sm:py-10">
        <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
          Premium
        </p>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Unlock your map
        </h1>
        <p className="mt-3 text-ink-soft">
          Everyone can browse opportunities free from the main menu. Premium is a{" "}
          <span className="font-medium text-ink">yearly</span> plan for your saved profile,
          personalized recommendations, Remind me, and deadline alerts (website + email).
        </p>

        <ul className="mt-8 space-y-2 text-sm text-ink-soft">
          <li>
            <span className="font-medium text-ink">Free — </span>
            Browse and open any opportunity
          </li>
          <li>
            <span className="font-medium text-ink">Premium — </span>
            Profile, For you matches, Saved, Remind me, Alerts
          </li>
        </ul>

        <div className="mt-8">
          {loading ? (
            <p className="text-ink-soft">Loading…</p>
          ) : user?.is_premium ? (
            <div>
              <p className="text-accent">Your Premium year is active.</p>
              {user.premium_until ? (
                <p className="mt-2 text-sm text-ink-soft">
                  Valid until {new Date(user.premium_until).toLocaleDateString()}.
                </p>
              ) : null}
              <Link href="/profile" className="mt-4 inline-block text-sm text-accent hover:underline">
                Go to profile →
              </Link>
            </div>
          ) : (
            <PremiumPaywall title="Yearly membership" />
          )}
        </div>

        <p className="mt-8 text-sm text-ink-soft">
          <Link href="/opportunities" className="text-accent hover:underline">
            ← Keep browsing free
          </Link>
        </p>

        {user ? (
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
        ) : null}
      </div>
    </main>
  );
}
