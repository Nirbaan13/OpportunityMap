import type { ReactNode } from "react";

type AuthShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
};

export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className="atmosphere relative min-h-[calc(100vh-5rem)] overflow-hidden">
      <div className="map-plane animate-drift pointer-events-none absolute inset-0 opacity-80" />
      <div className="relative mx-auto flex w-full max-w-md flex-col px-6 py-12 sm:py-16">
        <div className="animate-rise">
          <p className="font-display text-sm font-semibold uppercase tracking-[0.18em] text-accent">
            OpportunityMap
          </p>
          <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            {title}
          </h1>
          <p className="mt-3 text-base text-ink-soft">{subtitle}</p>
        </div>

        <div className="animate-rise-delay mt-8 space-y-5 border-t border-line pt-8">
          {children}
        </div>

        <p className="animate-rise-delay-2 mt-8 text-sm text-ink-soft">{footer}</p>
      </div>
    </div>
  );
}
