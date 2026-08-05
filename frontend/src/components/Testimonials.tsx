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
      "I don't have a counselor, so this actually helped me figure out what to put on my profile.",
  },
  {
    name: "Chloe Watson",
    quote:
      "The roadmap saves me so much time. I just knock out activities like a game instead of googling forever.",
  },
  {
    name: "Zhang Cheng",
    quote:
      "I stopped scrolling random lists. It shows programs I can actually apply to.",
  },
  {
    name: "Ethan Miller",
    quote:
      "Deadline alerts keep me honest. I used to miss everything until the last week.",
  },
  {
    name: "Diya Patel",
    quote:
      "Building my profile step by step made applying feel way less overwhelming.",
  },
  {
    name: "Junwei Wang",
    quote:
      "The roadmap is clear. Next activity, next checkpoint. No more guessing what to do.",
  },
  {
    name: "Zoe Smith",
    quote:
      "Finding olympiads and research programs used to take forever. Now the matches just show up.",
  },
  {
    name: "Rohan Malhotra",
    quote:
      "We don't have a counselor at school. This pretty much filled that gap for what to apply to.",
  },
  {
    name: "Liam Davis",
    quote:
      "Watching progress tick up on the roadmap weirdly makes me want to finish the next step.",
  },
  {
    name: "Meiling Chen",
    quote:
      "I get reminded before deadlines sneak up on me. That alone changed how I apply.",
  },
  {
    name: "Kavya Singh",
    quote:
      "Profile building used to feel so vague. Here it's just strengths, interests, then matches.",
  },
  {
    name: "Lucas Taylor",
    quote:
      "Hackathons and programs I never would've found on my own started showing up.",
  },
  {
    name: "Li Wei",
    quote:
      "No counselor at school, and that's fine. The roadmap told me what to work on week by week.",
  },
  {
    name: "Mason Jones",
    quote:
      "It feels like a game. Complete a stop, unlock the next. Studying for apps got way less boring.",
  },
  {
    name: "Ananya Josh",
    quote:
      "I used to lose track of deadlines across like ten tabs. Now they're in one place with alerts.",
  },
];

const AUTO_MS = 3800;
const LEN = TESTIMONIALS.length;

export function Testimonials() {
  const labelId = useId();
  const [index, setIndex] = useState(0);
  const [fadeKey, setFadeKey] = useState(0);
  // Refs so the rAF loop always reads current pause state without restarting.
  const hoverPaused = useRef(false);
  const focusPaused = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const advance = useCallback(() => {
    setIndex((i) => (i + 1) % LEN);
    setFadeKey((k) => k + 1);
  }, []);

  const goTo = useCallback((next: number) => {
    setIndex(((next % LEN) + LEN) % LEN);
    setFadeKey((k) => k + 1);
  }, []);

  const goPrev = useCallback(() => goTo(index - 1), [goTo, index]);
  const goNext = useCallback(() => goTo(index + 1), [goTo, index]);

  // Autoplay starts on mount unconditionally (ignores prefers-reduced-motion).
  // rAF + Date.now() survives Strict Mode remounts and does not rely on
  // setInterval firing under background-tab throttling the same way.
  useEffect(() => {
    let raf = 0;
    let last = Date.now();

    const tick = () => {
      const now = Date.now();
      const paused = hoverPaused.current || focusPaused.current;
      if (paused) {
        // Hold the deadline while paused so resume waits a full AUTO_MS.
        last = now;
      } else if (now - last >= AUTO_MS) {
        last = now;
        advance();
      }
      raf = window.requestAnimationFrame(tick);
    };

    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [advance]);

  // Safety: if pointer leaves the window or tab hides, never leave pause stuck.
  useEffect(() => {
    const clearHover = () => {
      hoverPaused.current = false;
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        hoverPaused.current = false;
        // If focus left the carousel while hidden, clear that too.
        const root = rootRef.current;
        if (root && !root.contains(document.activeElement)) {
          focusPaused.current = false;
        }
      }
    };
    window.addEventListener("blur", clearHover);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("blur", clearHover);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  const current = TESTIMONIALS[index];
  const prev = TESTIMONIALS[(index - 1 + LEN) % LEN];
  const next = TESTIMONIALS[(index + 1) % LEN];

  return (
    <section
      className="relative z-10 border-t border-line/70 px-4 py-14 sm:px-10 sm:py-20"
      aria-labelledby={labelId}
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
          ref={rootRef}
          className="mt-8 sm:mt-10"
          role="region"
          aria-roledescription="carousel"
          aria-label="Student testimonials"
          onPointerEnter={(e) => {
            // Mouse only — touch :hover can stick and freeze autoplay forever.
            if (e.pointerType === "mouse") hoverPaused.current = true;
          }}
          onPointerLeave={() => {
            hoverPaused.current = false;
          }}
          onFocusCapture={() => {
            focusPaused.current = true;
          }}
          onBlurCapture={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node)) {
              focusPaused.current = false;
            }
          }}
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
                    {index + 1} / {LEN}
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
