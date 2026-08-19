import { Fragment, useEffect, useState } from "react";
import { Link } from "react-router-dom";

const TYPED_SEGMENTS = [
  { text: "BAGZINE", emphasis: true },
  { text: " isn't here to sell you a bag, but to help you find your " },
  { text: "perfect one", emphasis: true },
  { text: " with the most " },
  { text: "complete price breakdown", emphasis: true },
  { text: " and a " },
  { text: "curated list", emphasis: true },
  { text: " of where to buy it." },
];

const TYPED_LENGTH = TYPED_SEGMENTS.reduce((total, segment) => total + segment.text.length, 0);

const BRANDS = [
  "Celine",
  "Chanel",
  "Dior",
  "Hermès",
  "Louis Vuitton",
  "Prada",
  "Saint Laurent",
];

export function LandingPage() {
  const [statementStage, setStatementStage] = useState(0);
  const [typedCharacters, setTypedCharacters] = useState(0);
  const [typingFinished, setTypingFinished] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (reducedMotion) {
      setStatementStage(4);
      setTypedCharacters(TYPED_LENGTH);
      setTypingFinished(true);
      return;
    }

    let typingTimer: number | undefined;
    const timers = [
      window.setTimeout(() => setStatementStage(1), 1950),
      window.setTimeout(() => setStatementStage(2), 3050),
      window.setTimeout(() => setStatementStage(3), 4200),
      window.setTimeout(() => setStatementStage(4), 5250),
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
    }, 6150));

    return () => {
      timers.forEach((timer) => window.clearTimeout(timer));
      if (typingTimer) window.clearInterval(typingTimer);
    };
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
        <span className="landing-guide landing-guide--horizontal" />
        <span className="landing-guide landing-guide--vertical" />
        <span className="landing-edition landing-edition--top">Price archive / 001</span>
        <span className="landing-edition landing-edition--bottom">Est. 2026</span>
      </div>

      <div className="landing-name" aria-label="Bagzine">
        <span className="landing-word landing-word--bag">BAG</span>
        <span className="landing-word landing-word--zine">ZINE</span>
      </div>

      <div className="landing-copy" aria-live="polite">
        <p className="landing-statements">
          <span className={statementStage >= 1 ? "is-visible" : ""}>Not a reseller.</span>
          <span className={statementStage >= 2 ? "is-visible" : ""}>Not a marketplace.</span>
        </p>
        <p className={`landing-investigation${statementStage >= 3 ? " is-visible" : ""}`}>
          Just the detective
        </p>
        <p
          className={`landing-investigation-sub${statementStage >= 4 ? " is-visible" : ""}`}
        >
          for your next bag investigation.
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
          <nav className="landing-brand-track" aria-label="Explore prices by brand">
            {[0, 1].map((group) => (
              <div className="landing-brand-group" key={group} aria-hidden={group === 1}>
                {BRANDS.map((brand) => (
                  <Link
                    key={`${group}-${brand}`}
                    tabIndex={group === 1 ? -1 : undefined}
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
