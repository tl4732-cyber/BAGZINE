import { type ReactNode, useEffect, useLayoutEffect, useRef, useState } from "react";

export interface StoryCard {
  title: string;
  paragraphs: ReactNode[];
}

interface Props {
  cards: StoryCard[];
  label: string;
}

export function StoryDeck({ cards, label }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);
  const activeIndexRef = useRef(0);
  const storyRef = useRef<HTMLElement>(null);
  const deckRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    activeIndexRef.current = activeIndex;
  }, [activeIndex]);

  useLayoutEffect(() => {
    function layoutDeck() {
      const storyEl = storyRef.current;
      const deckEl = deckRef.current;
      if (!storyEl || !deckEl) {
        return;
      }

      const styles = getComputedStyle(storyEl);
      const titleH = Number.parseFloat(styles.getPropertyValue("--title-h")) || 56;
      const fold = Number.parseFloat(styles.getPropertyValue("--fold")) || 16;
      const titleStack = cards.length * titleH - (cards.length - 1) * fold;
      const available = storyEl.parentElement?.clientHeight ?? storyEl.clientHeight;

      storyEl.style.paddingTop = "12px";
      storyEl.style.paddingBottom = "12px";

      const inners = [...deckEl.querySelectorAll(".brand-card-body-inner")] as HTMLElement[];
      for (const inner of inners) {
        inner.style.maxHeight = "";
        inner.style.overflowY = "";
      }

      const activeInner = deckEl.querySelector(
        ".brand-card.is-active .brand-card-body-inner",
      ) as HTMLElement | null;
      const maxBody = Math.max(96, available - 24 - titleStack);
      if (activeInner) {
        const natural = activeInner.scrollHeight;
        if (natural > maxBody) {
          activeInner.style.maxHeight = `${Math.floor(maxBody)}px`;
          activeInner.style.overflowY = "auto";
        } else {
          activeInner.style.maxHeight = "";
          activeInner.style.overflowY = "";
        }
        activeInner.scrollTop = 0;
      }

      const deckHeight = deckEl.getBoundingClientRect().height;
      const offset = Math.max(12, Math.round((available - deckHeight) / 2));
      storyEl.style.paddingTop = `${offset}px`;
    }

    layoutDeck();
    const afterToggle = window.setTimeout(layoutDeck, 60);
    const afterMotion = window.setTimeout(layoutDeck, 500);
    window.addEventListener("resize", layoutDeck);
    return () => {
      window.clearTimeout(afterToggle);
      window.clearTimeout(afterMotion);
      window.removeEventListener("resize", layoutDeck);
    };
  }, [activeIndex, cards.length]);

  useEffect(() => {
    const lastIndex = cards.length - 1;
    let acc = 0;
    let gestureLocked = false;
    let readingBody = false;
    let settleTimer = 0;
    let touchStartY: number | null = null;
    let touchConsumed = false;
    const settleMs = 420;
    const threshold = 28;

    function advance(direction: 1 | -1) {
      const next = activeIndexRef.current + direction;
      if (next < 0 || next > lastIndex) {
        return false;
      }
      activeIndexRef.current = next;
      setActiveIndex(next);
      return true;
    }

    function wheelDelta(event: WheelEvent) {
      if (event.deltaMode === 1) {
        return event.deltaY * 16;
      }
      if (event.deltaMode === 2) {
        return event.deltaY * window.innerHeight;
      }
      return event.deltaY;
    }

    function activeBody() {
      return deckRef.current?.querySelector(
        ".brand-card.is-active .brand-card-body-inner",
      ) as HTMLElement | null;
    }

    function markGesture() {
      window.clearTimeout(settleTimer);
      settleTimer = window.setTimeout(() => {
        gestureLocked = false;
        readingBody = false;
        acc = 0;
      }, settleMs);
    }

    function onWheel(event: WheelEvent) {
      event.preventDefault();
      const dy = wheelDelta(event);
      markGesture();

      if (gestureLocked) {
        return;
      }

      const inner = activeBody();
      if (inner && inner.scrollHeight > inner.clientHeight + 1) {
        const atTop = inner.scrollTop <= 0;
        const atBottom = inner.scrollTop + inner.clientHeight >= inner.scrollHeight - 1;
        if ((dy > 0 && !atBottom) || (dy < 0 && !atTop)) {
          readingBody = true;
          inner.scrollTop += dy;
          return;
        }
      }

      if (readingBody) {
        return;
      }

      acc += dy;
      if (Math.abs(acc) < threshold) {
        return;
      }

      const direction: 1 | -1 = acc > 0 ? 1 : -1;
      gestureLocked = true;
      acc = 0;
      advance(direction);
    }

    function onTouchStart(event: TouchEvent) {
      touchStartY = event.touches[0]?.clientY ?? null;
      touchConsumed = false;
    }

    function onTouchMove(event: TouchEvent) {
      event.preventDefault();
      if (touchStartY == null || touchConsumed) {
        return;
      }
      const currentY = event.touches[0]?.clientY ?? touchStartY;
      const delta = touchStartY - currentY;
      if (Math.abs(delta) < 18) {
        return;
      }
      touchConsumed = true;
      advance(delta > 0 ? 1 : -1);
    }

    window.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("touchstart", onTouchStart, { passive: true });
    window.addEventListener("touchmove", onTouchMove, { passive: false });
    return () => {
      window.clearTimeout(settleTimer);
      window.removeEventListener("wheel", onWheel);
      window.removeEventListener("touchstart", onTouchStart);
      window.removeEventListener("touchmove", onTouchMove);
    };
  }, [cards.length]);

  return (
    <div className="story-page">
      <h1 className="story-page-title">{label}</h1>
      <section className="brand-story" aria-label={label} ref={storyRef}>
        <div className="brand-deck" ref={deckRef}>
          {cards.map((card, index) => (
            <article
              className={`brand-card${index === activeIndex ? " is-active" : ""}${index < activeIndex ? " is-passed" : ""}`}
              key={card.title}
              style={{ ["--stack-index" as string]: index }}
              onClick={() => setActiveIndex(index)}
            >
              <h2>{card.title}</h2>
              <div className="brand-card-body">
                <div className="brand-card-body-inner">
                  {card.paragraphs.map((paragraph, paragraphIndex) => (
                    <p key={`${card.title}-${paragraphIndex}`}>{paragraph}</p>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
