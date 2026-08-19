import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface Props {
  title: string;
  children: ReactNode;
}

export function StaticPage({ title, children }: Props) {
  return (
    <section className="static-page">
      <h1>{title}</h1>
      <div className="static-page-body">{children}</div>
      <Link to="/" className="back-link">
        ← Back to home
      </Link>
    </section>
  );
}

export function AboutPage() {
  return (
    <StaticPage title="About">
      <p>
        Bagzine tracks vintage luxury handbag ask prices from eBay, grouped by brand and model so
        you can explore the market at a glance.
      </p>
    </StaticPage>
  );
}

export function BlogPage() {
  return (
    <StaticPage title="Blog">
      <p className="muted">Editorial content coming soon.</p>
    </StaticPage>
  );
}

export function PricingPage() {
  return (
    <StaticPage title="Pricing">
      <p className="muted">Subscription plans coming soon.</p>
    </StaticPage>
  );
}
