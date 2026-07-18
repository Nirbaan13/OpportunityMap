"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";

type ActivityStats = {
  saved: number;
  reminders: number;
  unread: number;
  profileReady: boolean;
  completedActivities: number;
  fullName: string | null;
};

const emptyStats: ActivityStats = {
  saved: 0,
  reminders: 0,
  unread: 0,
  profileReady: false,
  completedActivities: 0,
  fullName: null,
};

function initialsFrom(email: string, fullName: string | null): string {
  if (fullName?.trim()) {
    const parts = fullName.trim().split(/\s+/);
    const first = parts[0]?.[0] ?? "";
    const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? "") : "";
    return (first + last).toUpperCase() || email[0]?.toUpperCase() || "?";
  }
  return email[0]?.toUpperCase() || "?";
}

type UserMenuProps = {
  /** When true, menu fills the screen (mobile sheet). */
  forceSheet?: boolean;
  className?: string;
};

export function UserMenu({ forceSheet = false, className = "" }: UserMenuProps) {
  const { user, token } = useAuth();
  const pathname = usePathname();
  const menuId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [stats, setStats] = useState<ActivityStats>(emptyStats);
  const [statsLoading, setStatsLoading] = useState(false);

  const isPremium = Boolean(user?.is_premium);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    function onPointer(event: MouseEvent | TouchEvent) {
      const el = rootRef.current;
      if (!el) return;
      if (event.target instanceof Node && !el.contains(event.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("touchstart", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("touchstart", onPointer);
    };
  }, [open]);

  useEffect(() => {
    if (!open || !user || !token) return;
    let cancelled = false;
    (async () => {
      setStatsLoading(true);
      const next: ActivityStats = {
        ...emptyStats,
        profileReady: Boolean(user.has_profile),
      };
      try {
        if (user.is_premium) {
          const [bookmarks, unread, profile] = await Promise.all([
            api.listBookmarks(token, { page: 1, page_size: 100 }).catch(() => null),
            api.unreadNotificationCount(token).catch(() => null),
            user.has_profile ? api.getProfile(token).catch(() => null) : Promise.resolve(null),
          ]);
          if (bookmarks) {
            next.saved = bookmarks.total;
            next.reminders = bookmarks.items.filter((item) => item.remind_me).length;
          }
          if (unread) next.unread = unread.unread_count;
          if (profile) {
            next.profileReady = true;
            next.fullName = profile.full_name;
            next.completedActivities = profile.completed_opportunities?.length
              ?? profile.completed_activities.length;
          }
        }
      } finally {
        if (!cancelled) {
          setStats(next);
          setStatsLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, user, token]);

  useEffect(() => {
    if (!forceSheet || !open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [forceSheet, open]);

  if (!user) return null;

  const label = initialsFrom(user.email, stats.fullName);
  const panelClass = forceSheet
    ? "fixed inset-x-0 bottom-0 top-[3.5rem] z-50 overflow-y-auto overscroll-contain border-t border-line bg-paper px-4 pb-[max(1.25rem,env(safe-area-inset-bottom))] pt-4 shadow-[var(--shadow-soft)]"
    : "absolute right-0 top-full z-50 mt-2 w-[min(100vw-2rem,20rem)] overflow-hidden rounded-lg border border-line bg-paper shadow-[var(--shadow-soft)]";

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={menuId}
        aria-haspopup="menu"
        onClick={() => setOpen((v) => !v)}
        className="relative inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line bg-fog-deep/80 font-display text-sm font-bold text-ink transition hover:border-accent hover:bg-accent/10 sm:h-11 sm:w-11"
        title="Your account"
      >
        {label}
        {isPremium && stats.unread > 0 ? (
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-warm" />
        ) : null}
      </button>

      {open ? (
        <>
          {forceSheet ? (
            <button
              type="button"
              aria-label="Close menu"
              className="fixed inset-0 z-40 bg-ink/25"
              onClick={() => setOpen(false)}
            />
          ) : null}
          <div id={menuId} role="menu" className={panelClass}>
            <div className="border-b border-line px-1 pb-3 sm:px-4 sm:py-3">
              <p className="font-display text-base font-semibold text-ink sm:text-sm">
                {stats.fullName || "Your account"}
              </p>
              <p className="mt-0.5 truncate text-sm text-ink-soft sm:text-xs">{user.email}</p>
              <p className="mt-2 text-xs font-medium text-accent">
                {isPremium
                  ? user.premium_until
                    ? `Premium · until ${new Date(user.premium_until).toLocaleDateString()}`
                    : "Premium"
                  : "Free browse"}
              </p>
            </div>

            {isPremium ? (
              <div className="border-b border-line px-1 py-3 sm:px-4">
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-ink-soft">
                  Your activity
                </p>
                {statsLoading ? (
                  <p className="mt-2 text-sm text-ink-soft">Loading…</p>
                ) : (
                  <ul className="mt-2 grid grid-cols-2 gap-2 text-sm">
                    <li className="rounded-md bg-fog px-2.5 py-2.5">
                      <p className="text-lg font-semibold tabular-nums text-ink">{stats.saved}</p>
                      <p className="text-xs text-ink-soft">Saved</p>
                    </li>
                    <li className="rounded-md bg-fog px-2.5 py-2.5">
                      <p className="text-lg font-semibold tabular-nums text-ink">
                        {stats.reminders}
                      </p>
                      <p className="text-xs text-ink-soft">Reminders</p>
                    </li>
                    <li className="rounded-md bg-fog px-2.5 py-2.5">
                      <p className="text-lg font-semibold tabular-nums text-ink">{stats.unread}</p>
                      <p className="text-xs text-ink-soft">Unread alerts</p>
                    </li>
                    <li className="rounded-md bg-fog px-2.5 py-2.5">
                      <p className="text-lg font-semibold tabular-nums text-ink">
                        {stats.completedActivities}
                      </p>
                      <p className="text-xs text-ink-soft">Past activities</p>
                    </li>
                  </ul>
                )}
                <p className="mt-2 text-xs text-ink-soft">
                  Profile:{" "}
                  <span className="font-medium text-ink">
                    {stats.profileReady ? "Ready for matches" : "Needs setup"}
                  </span>
                </p>
              </div>
            ) : (
              <div className="border-b border-line px-1 py-3 sm:px-4">
                <p className="text-sm text-ink-soft">
                  See the premium roadmap for saved opportunities, reminders, and matches.
                </p>
                <Link
                  href="/pricing"
                  role="menuitem"
                  className="mt-3 inline-flex min-h-12 w-full items-center justify-center rounded-md bg-ink px-4 text-sm font-semibold text-paper transition hover:bg-ink-soft sm:min-h-11 sm:w-auto"
                  onClick={() => setOpen(false)}
                >
                  View roadmap
                </Link>
              </div>
            )}

            <nav className="flex flex-col py-1">
              <MenuLink href="/opportunities" active={pathname.startsWith("/opportunities")}>
                Opportunities
              </MenuLink>
              {isPremium ? (
                <>
                  <MenuLink href="/profile" active={pathname === "/profile"}>
                    Profile
                  </MenuLink>
                  <MenuLink href="/bookmarks" active={pathname.startsWith("/bookmarks")}>
                    Saved
                    {stats.saved > 0 ? (
                      <span className="ml-auto text-xs tabular-nums text-ink-soft">
                        {stats.saved}
                      </span>
                    ) : null}
                  </MenuLink>
                  <MenuLink href="/notifications" active={pathname.startsWith("/notifications")}>
                    Alerts
                    {stats.unread > 0 ? (
                      <span className="ml-auto rounded-md bg-warm/20 px-1.5 text-xs font-semibold tabular-nums text-warm">
                        {stats.unread > 99 ? "99+" : stats.unread}
                      </span>
                    ) : null}
                  </MenuLink>
                </>
              ) : (
                <MenuLink href="/pricing" active={pathname.startsWith("/pricing")}>
                  View roadmap
                </MenuLink>
              )}
            </nav>
          </div>
        </>
      ) : null}
    </div>
  );
}

function MenuLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: ReactNode;
}) {
  return (
    <Link
      href={href}
      role="menuitem"
      className={`flex min-h-12 items-center gap-2 rounded-md px-3 text-base font-medium transition hover:bg-fog-deep/80 sm:min-h-11 sm:rounded-none sm:px-4 sm:text-sm ${
        active ? "text-accent" : "text-ink-soft hover:text-ink"
      }`}
    >
      {children}
    </Link>
  );
}
