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

/** Opt in to deadline reminders. Free: ~30-day inbox. Premium: 10/1 + email. */
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
        className={`inline-flex min-h-11 items-center text-sm font-medium text-ink-soft transition hover:text-accent ${className}`}
        title="Log in to get a website reminder about a month before the deadline"
      >
        Log in for Remind me
      </Link>
    );
  }

  const isPremium = Boolean(user.is_premium);
  const tip = isPremium
    ? "Get email + website reminders 10 days and 1 day before the deadline"
    : "Free: website inbox alert about a month before the deadline (no email). Premium adds email and 10/1-day alerts.";

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
    <span className="inline-flex w-full flex-col items-stretch sm:w-auto sm:items-end">
      <button
        type="button"
        onClick={() => void toggle()}
        disabled={pending}
        className={`inline-flex min-h-11 items-center text-sm font-medium transition disabled:opacity-50 ${
          remindMe ? "text-accent hover:text-ink" : "text-ink-soft hover:text-accent"
        } ${className}`}
        aria-pressed={remindMe}
        title={tip}
      >
        {pending ? "Updating…" : remindMe ? "Remind me on" : "Remind me"}
      </button>
      {!isPremium && remindMe ? (
        <p className="mt-1 max-w-[14rem] text-xs text-ink-soft sm:text-right">
          Inbox ~1 month before · upgrade for email + last-week alerts
        </p>
      ) : null}
      {error ? <p className="mt-1 text-xs text-danger">{error}</p> : null}
    </span>
  );
}
