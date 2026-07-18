"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { ApiError } from "@/types/api";

type MarkDoneButtonProps = {
  opportunityId: number;
  done: boolean;
  onChange?: (done: boolean) => void;
  className?: string;
};

/** Mark an opportunity as completed (counts toward profile field insights). */
export function MarkDoneButton({
  opportunityId,
  done,
  onChange,
  className = "",
}: MarkDoneButtonProps) {
  const { user, token } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || !token) {
    return (
      <Link
        href="/login"
        className={`inline-flex min-h-11 items-center text-sm font-medium text-ink-soft transition hover:text-accent ${className}`}
      >
        Log in to mark done
      </Link>
    );
  }

  if (!user.is_premium) {
    return (
      <Link
        href="/pricing"
        className={`inline-flex min-h-11 items-center text-sm font-medium text-warm transition hover:text-accent ${className}`}
      >
        Unlock to mark done
      </Link>
    );
  }

  async function toggle() {
    if (pending) return;
    setPending(true);
    setError(null);
    const next = !done;
    onChange?.(next);
    try {
      await api.setBookmarkStatus(token!, opportunityId, next ? "completed" : "saved");
    } catch (err) {
      onChange?.(!next);
      setError(err instanceof ApiError ? err.message : "Could not update.");
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
          done ? "text-warm hover:text-ink" : "text-ink-soft hover:text-accent"
        } ${className}`}
        aria-pressed={done}
        title="Mark this opportunity as done — counts toward your field progress"
      >
        {pending ? "Updating…" : done ? "Marked done" : "Mark done"}
      </button>
      {error ? <p className="mt-1 text-xs text-danger">{error}</p> : null}
    </span>
  );
}
