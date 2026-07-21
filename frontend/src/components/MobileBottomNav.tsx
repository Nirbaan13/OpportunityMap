"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/components/AuthProvider";

function isActive(pathname: string, match: string): boolean {
  if (match === "/opportunities") return pathname.startsWith("/opportunities");
  return pathname === match || pathname.startsWith(`${match}/`);
}

export function MobileBottomNav() {
  const { user, loading } = useAuth();
  const pathname = usePathname();

  if (loading || !user) return null;

  const tabs = user.is_premium
    ? [
        { href: "/opportunities", label: "Browse", match: "/opportunities" },
        { href: "/bookmarks", label: "Saved", match: "/bookmarks" },
        { href: "/notifications", label: "Alerts", match: "/notifications" },
        { href: "/profile", label: "Profile", match: "/profile" },
      ]
    : [
        { href: "/opportunities", label: "Browse", match: "/opportunities" },
        { href: "/pricing", label: "Roadmap", match: "/pricing" },
        { href: "/profile", label: "Account", match: "/profile" },
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
          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex min-h-[3.25rem] flex-1 flex-col items-center justify-center px-1 text-[0.7rem] font-semibold uppercase tracking-wide transition ${
                active ? "text-accent" : "text-ink-soft"
              }`}
            >
              <span
                className={`mb-1 h-1 w-6 rounded-full transition ${
                  active ? "bg-accent" : "bg-transparent"
                }`}
                aria-hidden
              />
              {tab.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
