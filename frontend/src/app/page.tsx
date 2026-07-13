import Link from "next/link";

export default function Home() {
  return (
    <main className="atmosphere relative min-h-[calc(100vh-5rem)] overflow-hidden">
      <div
        aria-hidden
        className="map-plane animate-drift pointer-events-none absolute inset-0"
      />

      {/* Full-bleed visual plane: constellation of opportunity nodes */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        <svg className="h-full w-full opacity-70" viewBox="0 0 1200 800" fill="none">
          <path
            d="M180 520 C320 420, 480 460, 640 360 S980 220, 1100 280"
            stroke="rgba(15,118,110,0.35)"
            strokeWidth="1.5"
          />
          <path
            d="M120 240 C280 280, 420 180, 580 220 S860 340, 1040 300"
            stroke="rgba(234,88,12,0.28)"
            strokeWidth="1.5"
          />
          <circle className="animate-pulse-dot" cx="180" cy="520" r="7" fill="#0f766e" />
          <circle cx="640" cy="360" r="6" fill="#ea580c" />
          <circle className="animate-pulse-dot" cx="1100" cy="280" r="8" fill="#14b8a6" />
          <circle cx="120" cy="240" r="5" fill="#1f3a47" />
          <circle cx="580" cy="220" r="6" fill="#0f766e" />
          <circle cx="1040" cy="300" r="5" fill="#ea580c" />
        </svg>
      </div>

      <section className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl flex-col justify-center px-6 pb-20 pt-10 sm:px-10">
        <p className="animate-rise font-display text-5xl font-bold tracking-tight text-ink sm:text-7xl md:text-8xl">
          OpportunityMap
        </p>
        <h1 className="animate-rise-delay mt-6 max-w-2xl font-display text-2xl font-semibold leading-snug text-ink-soft sm:text-3xl">
          Find olympiads, hackathons, and research programs you can actually apply to.
        </h1>
        <p className="animate-rise-delay-2 mt-4 max-w-xl text-base text-ink-soft sm:text-lg">
          Browse openings free. Unlock a yearly premium plan when you want a saved
          profile, personalized matches, and deadline alerts to your email.
        </p>
        <div className="animate-rise-delay-2 mt-10 flex flex-wrap items-center gap-4">
          <Link
            href="/opportunities"
            className="inline-flex items-center rounded-md bg-ink px-5 py-3 text-sm font-semibold text-paper transition hover:bg-ink-soft"
          >
            Browse opportunities
          </Link>
          <Link
            href="/pricing"
            className="inline-flex items-center rounded-md border border-ink/20 bg-transparent px-5 py-3 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
          >
            Unlock premium
          </Link>
        </div>
      </section>
    </main>
  );
}
