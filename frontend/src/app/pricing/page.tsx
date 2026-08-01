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
          Everyone can browse opportunities, build a profile, and turn on free Remind me
          (website inbox ~1 month before). Premium is a{" "}
          <span className="font-medium text-ink">yearly</span> plan for personalized
          matches, Saved, email alerts, and last-week reminders.
        </p>

        <ul className="mt-8 space-y-2 text-sm text-ink-soft">
          <li>
            <span className="font-medium text-ink">Free — </span>
            Browse, profile, Remind me (inbox only, ~1 month before)
          </li>
          <li>
            <span className="font-medium text-ink">Premium — </span>
            For you matches, Saved, email alerts, 10-day / 1-day reminders
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
                  {user.auto_renew
                    ? " Renewal reminders are on."
                    : " Renewal reminders are off."}
                </p>
              ) : null}
              <div className="mt-6">
                <PremiumPaywall title="Renew membership" renew compact />
              </div>
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
