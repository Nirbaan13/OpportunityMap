"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";

export function SiteHeader() {
  const { user, token, loading, logout } = useAuth();
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [unread, setUnread] = useState(0);
  const isPremium = Boolean(user?.is_premium);

  useEffect(() => {
    if (!user || !token || !user.is_premium) {
      setUnread(0);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api.unreadNotificationCount(token);
        if (!cancelled) setUnread(data.unread_count);
      } catch {
        if (!cancelled) setUnread(0);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, token, pathname]);

  return (
    <header
      className={`relative z-20 flex items-center justify-between px-6 py-5 sm:px-10 ${
        isHome ? "text-ink" : "border-b border-line bg-paper/70 backdrop-blur-sm"
      }`}
    >
      <Link href="/" className="font-display text-xl font-bold tracking-tight sm:text-2xl">
        OpportunityMap
      </Link>

      <nav className="flex flex-wrap items-center justify-end gap-3 text-sm sm:gap-4">
        <Link
          href="/opportunities"
          className={`transition hover:text-accent ${
            pathname.startsWith("/opportunities") ? "text-accent" : "text-ink-soft"
          }`}
        >
          Opportunities
        </Link>
        {loading ? null : user ? (
          <>
            {isPremium ? (
              <>
                <Link
                  href="/bookmarks"
                  className={`transition hover:text-accent ${
                    pathname.startsWith("/bookmarks") ? "text-accent" : "text-ink-soft"
                  }`}
                >
                  Saved
                </Link>
                <Link
                  href="/notifications"
                  className={`transition hover:text-accent ${
                    pathname.startsWith("/notifications") ? "text-accent" : "text-ink-soft"
                  }`}
                >
                  Alerts
                  {unread > 0 ? (
                    <span className="ml-1.5 inline-flex min-w-[1.25rem] justify-center rounded-md bg-warm/20 px-1.5 text-xs font-semibold text-warm">
                      {unread > 99 ? "99+" : unread}
                    </span>
                  ) : null}
                </Link>
                <Link
                  href="/profile"
                  className={`transition hover:text-accent ${
                    pathname === "/profile" ? "text-accent" : "text-ink-soft"
                  }`}
                >
                  Profile
                </Link>
              </>
            ) : (
              <Link
                href="/pricing"
                className={`transition hover:text-accent ${
                  pathname.startsWith("/pricing") ? "text-accent" : "text-warm"
                }`}
              >
                Unlock
              </Link>
            )}
            <button
              type="button"
              onClick={logout}
              className="text-ink-soft transition hover:text-warm"
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link href="/login" className="text-ink-soft transition hover:text-accent">
              Log in
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center rounded-md bg-ink px-3.5 py-2 font-medium text-paper transition hover:bg-ink-soft"
            >
              Get started
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}
