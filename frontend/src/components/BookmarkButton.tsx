"use client";

import Link from "next/link";
import { useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";
import { ApiError } from "@/types/api";

type BookmarkButtonProps = {
  opportunityId: number;
  bookmarked: boolean;
  onChange?: (bookmarked: boolean) => void;
  className?: string;
};

export function BookmarkButton({
  opportunityId,
  bookmarked,
  onChange,
  className = "",
}: BookmarkButtonProps) {
  const { user, token } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user || !token) {
    return (
      <Link
        href="/login"
        className={`inline-flex min-h-11 items-center text-sm font-medium text-ink-soft transition hover:text-accent ${className}`}
      >
        Log in to save
      </Link>
    );
  }

  if (!user.is_premium) {
    return (
      <Link
        href="/pricing"
        className={`inline-flex min-h-11 items-center text-sm font-medium text-warm transition hover:text-accent ${className}`}
      >
        Unlock to save
      </Link>
    );
  }

  async function toggle() {
    if (pending) return;
    setPending(true);
    setError(null);
    const next = !bookmarked;
    onChange?.(next);
    try {
      if (next) {
        await api.addBookmark(token!, opportunityId);
      } else {
        await api.removeBookmark(token!, opportunityId);
      }
    } catch (err) {
      onChange?.(!next);
      if (err instanceof ApiError && err.status === 409 && next) {
        onChange?.(true);
        return;
      }
      if (err instanceof ApiError && err.status === 404 && !next) {
        onChange?.(false);
        return;
      }
      setError(err instanceof ApiError ? err.message : "Could not update bookmark.");
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
          bookmarked
            ? "text-warm hover:text-ink"
            : "text-ink-soft hover:text-accent"
        } ${className}`}
        aria-pressed={bookmarked}
      >
        {pending ? "Saving…" : bookmarked ? "Saved" : "Save"}
      </button>
      {error ? <p className="mt-1 text-xs text-danger">{error}</p> : null}
    </span>
  );
}
