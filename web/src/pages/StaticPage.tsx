import { type ReactNode } from "react";
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

export function TechSpecsPage() {
  return (
    <StaticPage title="Tech Specs">
      <p>
        Bagzine is a full-stack price intelligence system: scrape, normalize, store, and publish.
      </p>
      <ul>
        <li>
          <strong>Collection.</strong> Python Scrapy spiders pull listings from the eBay Browse API
          and Fashionphile&apos;s public Shopify feed, with validation so accessories and junk
          prices never enter the catalog.
        </li>
        <li>
          <strong>Matching.</strong> Title parsers canonicalize brand, model, size, leather, and
          color, then score confidence before a listing is linked to a product variant.
        </li>
        <li>
          <strong>Storage.</strong> PostgreSQL holds listings and append-only price history.
          Alembic migrations and SQL analytics views power medians, percentiles, and comparable
          sets.
        </li>
        <li>
          <strong>API.</strong> FastAPI exposes read-only REST endpoints for models, listings, and
          investigation reports.
        </li>
        <li>
          <strong>Interface.</strong> A React and TypeScript dashboard — catalog, model pages, and
          listing investigations with price charts.
        </li>
        <li>
          <strong>Cloud.</strong> An optional AWS path runs crawls on a schedule (Lambda, S3,
          EventBridge), provisioned with Terraform and monitored in CloudWatch.
        </li>
      </ul>
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
