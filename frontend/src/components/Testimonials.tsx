"use client";

import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type TransitionEvent,
} from "react";

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

const AUTO_MS = 4000;
const LEN = TESTIMONIALS.length;

function realFromVisual(visual: number): number {
  if (visual === 0) return LEN - 1;
  if (visual === LEN + 1) return 0;
  return visual - 1;
}

export function Testimonials() {
  const labelId = useId();
  // visualIndex: 0 = clone of last, 1..LEN = real slides, LEN+1 = clone of first
  const [visualIndex, setVisualIndex] = useState(1);
  const [enableTransition, setEnableTransition] = useState(true);
  // Refs so the rAF loop always reads current pause state without restarting.
  const hoverPaused = useRef(false);
  const focusPaused = useRef(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const visualIndexRef = useRef(1);
  const animatingRef = useRef(false);

  const slides = useMemo(
    () => [TESTIMONIALS[LEN - 1], ...TESTIMONIALS, TESTIMONIALS[0]],
    [],
  );

  const activeReal = realFromVisual(visualIndex);

  const moveTo = useCallback((next: number) => {
    if (animatingRef.current) return;
    animatingRef.current = true;
    setEnableTransition(true);
    visualIndexRef.current = next;
    setVisualIndex(next);
  }, []);

  const advance = useCallback(() => {
    moveTo(visualIndexRef.current + 1);
  }, [moveTo]);

  const goPrev = useCallback(() => {
    moveTo(visualIndexRef.current - 1);
  }, [moveTo]);

  const goNext = useCallback(() => {
    moveTo(visualIndexRef.current + 1);
  }, [moveTo]);

  const goTo = useCallback(
    (realIndex: number) => {
      const clamped = ((realIndex % LEN) + LEN) % LEN;
      moveTo(clamped + 1);
    },
    [moveTo],
  );

  const handleTransitionEnd = useCallback(
    (e: TransitionEvent<HTMLDivElement>) => {
      if (e.propertyName !== "transform") return;
      const v = visualIndexRef.current;
      if (v === LEN + 1) {
        setEnableTransition(false);
        visualIndexRef.current = 1;
        setVisualIndex(1);
      } else if (v === 0) {
        setEnableTransition(false);
        visualIndexRef.current = LEN;
        setVisualIndex(LEN);
      }
      animatingRef.current = false;
    },
    [],
  );

  // After an instant jump off a clone, re-enable transitions on the next frame.
  useEffect(() => {
    if (enableTransition) return;
    const id = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        setEnableTransition(true);
      });
    });
    return () => window.cancelAnimationFrame(id);
  }, [enableTransition, visualIndex]);

  // Autoplay starts on mount unconditionally (ignores prefers-reduced-motion).
  // rAF + Date.now() survives Strict Mode remounts and does not rely on
  // setInterval firing under background-tab throttling the same way.
  useEffect(() => {
    let raf = 0;
    let last = Date.now();

    const tick = () => {
      const now = Date.now();
      const paused = hoverPaused.current || focusPaused.current;
      if (paused || animatingRef.current) {
        // Hold the deadline while paused / mid-slide so resume waits a full AUTO_MS.
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
          <div className="mx-auto max-w-xl lg:max-w-2xl">
            <div className="testimonials-viewport overflow-hidden rounded-lg border border-line bg-paper shadow-soft">
              <div
                className={`testimonials-track flex ${
                  enableTransition ? "testimonials-track--animate" : ""
                }`}
                style={{ transform: `translate3d(-${visualIndex * 100}%, 0, 0)` }}
                onTransitionEnd={handleTransitionEnd}
              >
                {slides.map((t, i) => {
                  const isActive = i === visualIndex;
                  return (
                    <article
                      key={`${t.name}-${i}`}
                      className="testimonials-panel w-full shrink-0 grow-0 basis-full p-6 sm:p-8"
                      aria-hidden={!isActive}
                      aria-live={isActive ? "polite" : undefined}
                      aria-atomic={isActive ? true : undefined}
                    >
                      <div
                        aria-hidden
                        className="mb-4 h-1 w-10 rounded-full bg-accent"
                      />
                      <blockquote className="font-display text-lg font-semibold leading-snug text-ink sm:text-xl">
                        &ldquo;{t.quote}&rdquo;
                      </blockquote>
                      <footer className="mt-5">
                        <cite className="not-italic text-sm font-semibold text-ink-soft">
                          {t.name}
                        </cite>
                      </footer>
                    </article>
                  );
                })}
              </div>
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
                  aria-selected={i === activeReal}
                  aria-label={`Show testimonial from ${t.name}`}
                  onClick={() => goTo(i)}
                  className={`h-2 rounded-full transition-[width,background-color] duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ${
                    i === activeReal
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
