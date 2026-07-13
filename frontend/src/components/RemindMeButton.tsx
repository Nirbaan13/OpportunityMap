"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { ApiError } from "@/types/api";

type RemindMeButtonProps = {
  opportunityId: number;
  remindMe: boolean;
  onChange?: (remindMe: boolean) => void;
  className?: string;
};

/** Opt in to 10-day and 1-day website deadline reminders for this opportunity. */
export function RemindMeButton({
  opportunityId,
  remindMe,
  onChange,
  className = "",
}: RemindMeButtonProps) {
  const { user, token } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || !token) {
    return (
      <Link
        href="/login"
        className={`text-sm font-medium text-ink-soft transition hover:text-accent ${className}`}
        title="Log in to get 10-day and 1-day deadline reminders"
      >
        Log in for Remind me
      </Link>
    );
  }

  if (!user.is_premium) {
    return (
      <Link
        href="/pricing"
        className={`text-sm font-medium text-warm transition hover:text-accent ${className}`}
        title="Premium unlocks Remind me, recommendations, and alerts"
      >
        Unlock Remind me
      </Link>
    );
  }

  async function toggle() {
    if (pending) return;
    setPending(true);
    setError(null);
    const next = !remindMe;
    onChange?.(next);
    try {
      await api.setRemindMe(token!, opportunityId, next);
    } catch (err) {
      onChange?.(!next);
      setError(err instanceof ApiError ? err.message : "Could not update reminder.");
    } finally {
      setPending(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start sm:items-end">
      <button
        type="button"
        onClick={() => void toggle()}
        disabled={pending}
        className={`text-sm font-medium transition disabled:opacity-50 ${
          remindMe ? "text-accent hover:text-ink" : "text-ink-soft hover:text-accent"
        } ${className}`}
        aria-pressed={remindMe}
        title="Get email + website reminders 10 days and 1 day before the deadline"
      >
        {pending ? "Updating…" : remindMe ? "Remind me on" : "Remind me"}
      </button>
      {error ? <p className="mt-1 text-xs text-danger">{error}</p> : null}
    </span>
  );
}
