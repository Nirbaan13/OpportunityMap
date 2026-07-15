"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { UserMenu } from "@/components/UserMenu";
import { api } from "@/lib/api";

export function SiteHeader() {
  const { user, token, loading, logout } = useAuth();
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [unread, setUnread] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);
  const mobileMenuId = useId();
  const isPremium = Boolean(user?.is_premium);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [mobileOpen]);

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
      className={`relative z-20 flex items-center justify-between gap-4 px-5 py-4 sm:px-10 sm:py-5 ${
        isHome ? "text-ink" : "border-b border-line bg-paper/70 backdrop-blur-sm"
      }`}
    >
      <Link href="/" className="font-display text-xl font-bold tracking-tight sm:text-2xl">
        OpportunityMap
      </Link>

      {/* Desktop: keep existing links + profile icon for activity / account */}
      <div className="hidden items-center gap-5 md:flex">
        <nav className="flex items-center gap-4 text-sm">
          <Link
            href="/opportunities"
            className={`inline-flex min-h-10 items-center transition hover:text-accent ${
              pathname.startsWith("/opportunities") ? "text-accent" : "text-ink-soft"
            }`}
          >
            Opportunities
          </Link>
          {loading ? null : user ? (
            isPremium ? (
              <>
                <Link
                  href="/bookmarks"
                  className={`inline-flex min-h-10 items-center transition hover:text-accent ${
                    pathname.startsWith("/bookmarks") ? "text-accent" : "text-ink-soft"
                  }`}
                >
                  Saved
                </Link>
                <Link
                  href="/notifications"
                  className={`inline-flex min-h-10 items-center transition hover:text-accent ${
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
                  className={`inline-flex min-h-10 items-center transition hover:text-accent ${
                    pathname === "/profile" ? "text-accent" : "text-ink-soft"
                  }`}
                >
                  Profile
                </Link>
              </>
            ) : (
              <Link
                href="/pricing"
                className={`inline-flex min-h-10 items-center transition hover:text-accent ${
                  pathname.startsWith("/pricing") ? "text-accent" : "text-warm"
                }`}
              >
                Unlock
              </Link>
            )
          ) : (
            <>
              <Link
                href="/login"
                className="inline-flex min-h-10 items-center text-ink-soft transition hover:text-accent"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="inline-flex min-h-10 items-center rounded-md bg-ink px-3.5 py-2 font-medium text-paper transition hover:bg-ink-soft"
              >
                Get started
              </Link>
            </>
          )}
        </nav>
        {!loading && user ? (
          <>
            <UserMenu />
            <button
              type="button"
              onClick={logout}
              className="inline-flex min-h-10 items-center text-sm text-ink-soft transition hover:text-warm"
            >
              Log out
            </button>
          </>
        ) : null}
      </div>

      {/* Mobile: logo + controls — no wrapping link row */}
      <div className="flex items-center gap-2 md:hidden">
        {!loading && user ? <UserMenu forceSheet /> : null}
        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-controls={mobileMenuId}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          onClick={() => setMobileOpen((v) => !v)}
          className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-line text-ink transition hover:border-accent"
        >
          {mobileOpen ? (
            <span className="relative block h-3.5 w-3.5">
              <span className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 rotate-45 bg-current" />
              <span className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 -rotate-45 bg-current" />
            </span>
          ) : (
            <span className="flex flex-col gap-1.5">
              <span className="block h-0.5 w-4 bg-current" />
              <span className="block h-0.5 w-4 bg-current" />
              <span className="block h-0.5 w-4 bg-current" />
            </span>
          )}
        </button>
      </div>

      {mobileOpen ? (
        <>
          <button
            type="button"
            aria-label="Close menu"
            className="fixed inset-0 z-30 bg-ink/25 md:hidden"
            onClick={() => setMobileOpen(false)}
          />
          <div
            id={mobileMenuId}
            className="fixed inset-x-0 top-[4.25rem] z-40 max-h-[calc(100dvh-4.25rem)] overflow-y-auto border-t border-line bg-paper px-5 py-4 shadow-[var(--shadow-soft)] md:hidden"
          >
            <nav className="flex flex-col gap-1">
              <MobileLink
                href="/opportunities"
                active={pathname.startsWith("/opportunities")}
                onNavigate={() => setMobileOpen(false)}
              >
                Opportunities
              </MobileLink>
              {loading ? null : user ? (
                <>
                  {isPremium ? (
                    <>
                      <MobileLink
                        href="/bookmarks"
                        active={pathname.startsWith("/bookmarks")}
                        onNavigate={() => setMobileOpen(false)}
                      >
                        Saved
                      </MobileLink>
                      <MobileLink
                        href="/notifications"
                        active={pathname.startsWith("/notifications")}
                        onNavigate={() => setMobileOpen(false)}
                      >
                        Alerts
                        {unread > 0 ? (
                          <span className="ml-2 inline-flex min-w-[1.25rem] justify-center rounded-md bg-warm/20 px-1.5 text-xs font-semibold text-warm">
                            {unread > 99 ? "99+" : unread}
                          </span>
                        ) : null}
                      </MobileLink>
                      <MobileLink
                        href="/profile"
                        active={pathname === "/profile"}
                        onNavigate={() => setMobileOpen(false)}
                      >
                        Profile
                      </MobileLink>
                    </>
                  ) : (
                    <MobileLink
                      href="/pricing"
                      active={pathname.startsWith("/pricing")}
                      onNavigate={() => setMobileOpen(false)}
                      className="text-warm"
                    >
                      Unlock premium
                    </MobileLink>
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      setMobileOpen(false);
                      logout();
                    }}
                    className="flex min-h-12 items-center rounded-md px-3 text-left text-base font-medium text-ink-soft transition hover:bg-fog-deep/80 hover:text-warm"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <MobileLink
                    href="/login"
                    active={pathname.startsWith("/login")}
                    onNavigate={() => setMobileOpen(false)}
                  >
                    Log in
                  </MobileLink>
                  <Link
                    href="/register"
                    onClick={() => setMobileOpen(false)}
                    className="mt-2 inline-flex min-h-12 items-center justify-center rounded-md bg-ink px-4 text-base font-semibold text-paper transition hover:bg-ink-soft"
                  >
                    Get started
                  </Link>
                </>
              )}
            </nav>
            {user ? (
              <p className="mt-4 border-t border-line pt-4 text-sm text-ink-soft">
                Signed in as <span className="font-medium text-ink">{user.email}</span>. Open
                your profile icon for activity records (saved, reminders, alerts).
              </p>
            ) : null}
          </div>
        </>
      ) : null}
    </header>
  );
}

function MobileLink({
  href,
  active,
  onNavigate,
  children,
  className = "",
}: {
  href: string;
  active: boolean;
  onNavigate: () => void;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link
      href={href}
      onClick={onNavigate}
      className={`flex min-h-12 items-center rounded-md px-3 text-base font-medium transition hover:bg-fog-deep/80 ${
        active ? "text-accent" : "text-ink-soft hover:text-ink"
      } ${className}`}
    >
      {children}
    </Link>
  );
}
