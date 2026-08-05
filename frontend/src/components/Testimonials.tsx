"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";

type Testimonial = {
  name: string;
  quote: string;
};

const TESTIMONIALS: Testimonial[] = [
  {
    name: "Aarav Sharma",
    quote:
      "This helped me build my profile without a counsellor — finally felt like I knew what to put down.",
  },
  {
    name: "Chloe Watson",
    quote:
      "The roadmap saves time because I don't have to search for activities. I just complete them like a game.",
  },
  {
    name: "Zhang Cheng",
    quote:
      "I stopped scrolling random lists. OpportunityMap shows programs I can actually apply to.",
  },
  {
    name: "Ethan Miller",
    quote:
      "Deadline alerts keep me honest. I used to miss everything until the last week.",
  },
  {
    name: "Diya Patel",
    quote:
      "Building my profile step by step made applying feel less overwhelming.",
  },
  {
    name: "Junwei Wang",
    quote:
      "The roadmap is clear — next activity, next checkpoint. No more guessing what to do.",
  },
  {
    name: "Zoe Smith",
    quote:
      "Finding olympiads and research programs used to take forever. Now matches show up for me.",
  },
  {
    name: "Rohan Malhotra",
    quote:
      "I don't have a counselor at school. This filled that gap for planning what to apply to.",
  },
  {
    name: "Liam Davis",
    quote:
      "Watching progress tick up on the roadmap actually makes me want to finish the next step.",
  },
  {
    name: "Meiling Chen",
    quote:
      "I get reminded before deadlines hit my inbox late. That alone changed how I apply.",
  },
  {
    name: "Kavya Singh",
    quote:
      "Profile building used to feel vague. Here it's concrete — strengths, interests, then matches.",
  },
  {
    name: "Lucas Taylor",
    quote:
      "Hackathons and programs I would never have found on my own started showing up.",
  },
  {
    name: "Li Wei",
    quote:
      "No counselor, no problem. The roadmap told me what to work on week by week.",
  },
  {
    name: "Mason Jones",
    quote:
      "It feels game-like — complete a stop, unlock the next. Studying for apps got way less boring.",
  },
  {
    name: "Ananya Josh",
    quote:
      "I used to lose track of deadlines across tabs. Now they're in one place with alerts.",
  },
];

const AUTO_MS = 5200;

export function Testimonials() {
  const labelId = useId();
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const [fadeKey, setFadeKey] = useState(0);
  const reduceMotion = useRef(false);

  useEffect(() => {
    reduceMotion.current = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
  }, []);

  const goTo = useCallback((next: number) => {
    const len = TESTIMONIALS.length;
    setIndex(((next % len) + len) % len);
    setFadeKey((k) => k + 1);
  }, []);

  const goPrev = useCallback(() => goTo(index - 1), [goTo, index]);
  const goNext = useCallback(() => goTo(index + 1), [goTo, index]);

  useEffect(() => {
    if (paused || reduceMotion.current) return;
    const id = window.setInterval(() => {
      setIndex((i) => (i + 1) % TESTIMONIALS.length);
      setFadeKey((k) => k + 1);
    }, AUTO_MS);
    return () => window.clearInterval(id);
  }, [paused]);

  const current = TESTIMONIALS[index];
  const prev = TESTIMONIALS[(index - 1 + TESTIMONIALS.length) % TESTIMONIALS.length];
  const next = TESTIMONIALS[(index + 1) % TESTIMONIALS.length];

  return (
    <section
      className="relative z-10 border-t border-line/70 px-4 py-14 sm:px-10 sm:py-20"
      aria-labelledby={labelId}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          setPaused(false);
        }
      }}
    >
      <div className="mx-auto max-w-5xl">
        <h2
          id={labelId}
          className="font-display text-2xl font-bold tracking-tight text-ink sm:text-3xl"
        >
          Students on the map
        </h2>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-soft sm:text-base">
          Short notes from students using OpportunityMap to plan, apply, and keep
          moving.
        </p>

        <div
          className="mt-8 sm:mt-10"
          role="region"
          aria-roledescription="carousel"
          aria-label="Student testimonials"
        >
          <div className="relative">
            {/* Peek cards — desktop */}
            <div className="pointer-events-none absolute inset-y-0 left-0 hidden w-[18%] items-center lg:flex">
              <article
                aria-hidden
                className="w-full scale-90 rounded-lg border border-line/80 bg-paper/60 p-5 opacity-40 shadow-soft transition-opacity duration-300"
              >
                <p className="line-clamp-3 text-sm text-ink-soft">
                  &ldquo;{prev.quote}&rdquo;
                </p>
                <p className="mt-3 text-xs font-semibold text-ink">{prev.name}</p>
              </article>
            </div>
            <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[18%] items-center lg:flex">
              <article
                aria-hidden
                className="ml-auto w-full scale-90 rounded-lg border border-line/80 bg-paper/60 p-5 opacity-40 shadow-soft transition-opacity duration-300"
              >
                <p className="line-clamp-3 text-sm text-ink-soft">
                  &ldquo;{next.quote}&rdquo;
                </p>
                <p className="mt-3 text-xs font-semibold text-ink">{next.name}</p>
              </article>
            </div>

            <div className="mx-auto max-w-xl lg:max-w-2xl">
              <article
                key={fadeKey}
                className="testimonials-slide rounded-lg border border-line bg-paper p-6 shadow-soft sm:p-8"
                aria-live="polite"
                aria-atomic="true"
              >
                <div
                  aria-hidden
                  className="mb-4 h-1 w-10 rounded-full bg-accent"
                />
                <blockquote className="font-display text-lg font-semibold leading-snug text-ink sm:text-xl">
                  &ldquo;{current.quote}&rdquo;
                </blockquote>
                <footer className="mt-5 flex items-center justify-between gap-3">
                  <cite className="not-italic text-sm font-semibold text-ink-soft">
                    {current.name}
                  </cite>
                  <span className="text-xs tabular-nums text-ink-soft/80">
                    {index + 1} / {TESTIMONIALS.length}
                  </span>
                </footer>
              </article>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-center gap-3 sm:mt-8">
            <button
              type="button"
              onClick={goPrev}
              className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-ink/20 bg-transparent text-ink transition hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              aria-label="Previous testimonial"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path
                  d="M15 6l-6 6 6 6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>

            <div
              className="flex max-w-[min(100%,14rem)] flex-wrap items-center justify-center gap-1.5 sm:max-w-none"
              role="tablist"
              aria-label="Choose testimonial"
            >
              {TESTIMONIALS.map((t, i) => (
                <button
                  key={t.name}
                  type="button"
                  role="tab"
                  aria-selected={i === index}
                  aria-label={`Show testimonial from ${t.name}`}
                  onClick={() => goTo(i)}
                  className={`h-2 rounded-full transition-[width,background-color] duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
                    i === index
                      ? "w-5 bg-accent"
                      : "w-2 bg-ink/20 hover:bg-ink/35"
                  }`}
                />
              ))}
            </div>

            <button
              type="button"
              onClick={goNext}
              className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-ink/20 bg-transparent text-ink transition hover:border-accent hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              aria-label="Next testimonial"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
                <path
                  d="M9 6l6 6-6 6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
