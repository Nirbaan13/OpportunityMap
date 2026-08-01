"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/AuthProvider";
import { api } from "@/lib/api";

function isActive(pathname: string, match: string): boolean {
  if (match === "/opportunities") return pathname.startsWith("/opportunities");
  return pathname === match || pathname.startsWith(`${match}/`);
}

type Tab = {
  href: string;
  label: string;
  match: string;
  badge?: number;
};

export function MobileBottomNav() {
  const { user, token, loading } = useAuth();
  const pathname = usePathname();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user?.is_premium || !token) {
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

  if (loading || !user) return null;

  const tabs: Tab[] = user.is_premium
    ? [
        { href: "/opportunities", label: "Browse", match: "/opportunities" },
        { href: "/roadmap", label: "Roadmap", match: "/roadmap" },
        { href: "/bookmarks", label: "Saved", match: "/bookmarks" },
        {
          href: "/notifications",
          label: "Alerts",
          match: "/notifications",
          badge: unread,
        },
        { href: "/profile", label: "Profile", match: "/profile" },
      ]
    : [
        { href: "/opportunities", label: "Browse", match: "/opportunities" },
        { href: "/roadmap", label: "Roadmap", match: "/roadmap" },
        { href: "/profile", label: "Profile", match: "/profile" },
      ];

  return (
    <nav
      aria-label="Main navigation"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-paper/95 backdrop-blur-md md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      <div className="flex">
        {tabs.map((tab) => {
          const active = isActive(pathname, tab.match);
          const badge = tab.badge && tab.badge > 0 ? tab.badge : 0;
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`relative flex min-h-[3.25rem] flex-1 flex-col items-center justify-center px-0.5 text-[0.65rem] font-semibold uppercase tracking-wide transition sm:text-[0.7rem] ${
                active ? "text-accent" : "text-ink-soft"
              }`}
            >
              <span
                className={`mb-1 h-1 w-5 rounded-full transition sm:w-6 ${
                  active ? "bg-accent" : "bg-transparent"
                }`}
                aria-hidden
              />
              <span className="inline-flex items-center gap-0.5">
                {tab.label}
                {badge > 0 ? (
                  <span
                    className="inline-flex h-4 min-w-[1rem] items-center justify-center rounded bg-warm/20 px-0.5 text-[0.55rem] font-bold tabular-nums text-warm"
                    aria-label={`${badge} unread`}
                  >
                    {badge > 99 ? "99+" : badge}
                  </span>
                ) : null}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
