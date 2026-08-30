import { Fragment, useEffect, useLayoutEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

const TYPED_SEGMENTS = [
  { text: "Your place to discover, compare, and talk bags." },
];

const TYPED_LENGTH = TYPED_SEGMENTS.reduce((total, segment) => total + segment.text.length, 0);

const BRANDS = [
  "Bottega Veneta",
  "Celine",
  "Chanel",
  "Dior",
  "Fendi",
  "Goyard",
  "Gucci",
  "Hermès",
  "Loewe",
  "Louis Vuitton",
  "Prada",
  "Saint Laurent",
];

const MARQUEE_SPEED_PX_PER_SEC = 45;

export function LandingPage() {
  const [statementStage, setStatementStage] = useState(0);
  const [typedCharacters, setTypedCharacters] = useState(0);
  const [typingFinished, setTypingFinished] = useState(false);
  const brandGroupRef = useRef<HTMLDivElement>(null);
  const [marqueeCopies, setMarqueeCopies] = useState(4);
  const [marqueeShift, setMarqueeShift] = useState(0);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reducedMotion) {
      setStatementStage(3);
      setTypedCharacters(TYPED_LENGTH);
      setTypingFinished(true);
      return;
    }

    let typingTimer: number | undefined;
    const timers = [
      window.setTimeout(() => setStatementStage(1), 1200),
      window.setTimeout(() => setStatementStage(2), 1550),
      window.setTimeout(() => setStatementStage(3), 1900),
    ];

    timers.push(window.setTimeout(() => {
      typingTimer = window.setInterval(() => {
        setTypedCharacters((current) => {
          const next = current + 1;
          if (next >= TYPED_LENGTH) {
            window.clearInterval(typingTimer);
            setTypingFinished(true);
            return TYPED_LENGTH;
          }
          return next;
        });
      }, 42);
    }, 2350));

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      if (typingTimer) window.clearInterval(typingTimer);
    };
  }, []);

  useLayoutEffect(() => {
    const group = brandGroupRef.current;
    const container = group?.parentElement?.parentElement;
    if (!group || !container) return;

    const measure = () => {
      const groupWidth = group.getBoundingClientRect().width;
      const containerWidth = container.getBoundingClientRect().width;
      if (groupWidth <= 0) return;
      setMarqueeCopies(Math.max(2, Math.ceil(containerWidth / groupWidth) + 1));
      setMarqueeShift(groupWidth);
    };

    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(group);
    observer.observe(container);
    void document.fonts?.ready.then(measure);
    return () => observer.disconnect();
  }, []);

  function renderTypedCopy() {
    let remaining = typedCharacters;

    return TYPED_SEGMENTS.map((segment, index) => {
      const visibleText = segment.text.slice(0, Math.max(0, remaining));
      remaining -= segment.text.length;
      if (!visibleText) return null;

      const content = segment.emphasis ? <strong>{visibleText}</strong> : visibleText;
      return <Fragment key={`${segment.text}-${index}`}>{content}</Fragment>;
    });
  }

  return (
    <section className="landing-page">
      <div className="landing-decoration" aria-hidden>
        <span className="landing-frame landing-frame--one" />
        <span className="landing-frame landing-frame--two" />
      </div>

      <div className="landing-name" aria-label="Bagzine">
        <span className="landing-word landing-word--bag">BAG</span>
        <span className="landing-word landing-word--zine">ZINE</span>
      </div>

      <div className="landing-copy" aria-live="polite">
        <p className="landing-statements">
          <span className={statementStage >= 1 ? "is-visible" : ""}>Bags.</span>
          <span className={statementStage >= 2 ? "is-visible" : ""}>Prices.</span>
          <span className={statementStage >= 3 ? "is-visible" : ""}>Opinions.</span>
        </p>
        <p className="landing-intro">
          {renderTypedCopy()}
          {!typingFinished && typedCharacters > 0 && <span className="typing-cursor" aria-hidden />}
        </p>
      </div>

      <div className={`landing-actions${typingFinished ? " is-visible" : ""}`}>
        <Link className="landing-start" to="/prices">
          Start Exploring <span aria-hidden>→</span>
        </Link>

        <div className="landing-brand-marquee">
          <nav
            className="landing-brand-track"
            aria-label="Explore prices by brand"
            style={{
              ["--marquee-shift" as string]: `${marqueeShift}px`,
              ["--marquee-duration" as string]: `${
                marqueeShift > 0 ? marqueeShift / MARQUEE_SPEED_PX_PER_SEC : 28
              }s`,
            }}
          >
            {Array.from({ length: marqueeCopies }, (_, group) => (
              <div
                className="landing-brand-group"
                key={group}
                ref={group === 0 ? brandGroupRef : undefined}
                aria-hidden={group > 0}
              >
                {BRANDS.map((brand) => (
                  <Link
                    key={`${group}-${brand}`}
                    tabIndex={group > 0 ? -1 : undefined}
                    to={`/prices?brand=${encodeURIComponent(brand)}`}
                  >
                    {brand}
                  </Link>
                ))}
              </div>
            ))}
          </nav>
        </div>
      </div>
    </section>
  );
}
