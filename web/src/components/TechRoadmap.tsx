import type { ReactNode } from "react";

const REPO = "https://github.com/tl4732-cyber/luxury_vintage_bag_price";
const BRANCH = "cursor/phase1-scrapy-step-by-step";

function tree(path: string) {
  return `${REPO}/tree/${BRANCH}/${path}`;
}

function blob(path: string) {
  return `${REPO}/blob/${BRANCH}/${path}`;
}

function Badges({ items }: { items: string[] }) {
  return (
    <div className="tech-badges">
      {items.map((item) => (
        <span className="tech-badge" key={item}>
          {item}
        </span>
      ))}
    </div>
  );
}

function FileList({ files }: { files: { path: string; label: string }[] }) {
  return (
    <ul className="tech-file-list">
      {files.map((file) => (
        <li key={file.path}>
          <a href={blob(file.path)} target="_blank" rel="noreferrer">
            {file.label}
          </a>
        </li>
      ))}
    </ul>
  );
}

function PipelineStage({
  step,
  title,
  detail,
}: {
  step: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="tech-pipeline-stage">
      <span className="tech-pipeline-step">{step}</span>
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

interface RoadmapStepProps {
  number: number;
  title: string;
  summary: string;
  details?: string[];
  tools: string[];
  folder?: { path: string; label: string };
  files?: { path: string; label: string }[];
  children?: ReactNode;
}

function RoadmapStep({
  number,
  title,
  summary,
  details,
  tools,
  folder,
  files,
  children,
}: RoadmapStepProps) {
  return (
    <article className="tech-roadmap-step">
      <div className="tech-roadmap-marker" aria-hidden="true">
        <span>{number}</span>
      </div>
      <div className="tech-roadmap-content">
        <h3>{title}</h3>
        <p className="tech-roadmap-summary">{summary}</p>
        {details?.map((paragraph) => (
          <p className="tech-roadmap-detail" key={paragraph.slice(0, 48)}>
            {paragraph}
          </p>
        ))}
        <Badges items={tools} />
        {folder && (
          <p className="tech-roadmap-folder">
            <a href={tree(folder.path)} target="_blank" rel="noreferrer">
              {folder.label} ↗
            </a>
          </p>
        )}
        {files && files.length > 0 && <FileList files={files} />}
        {children}
      </div>
    </article>
  );
}

export function TechRoadmap() {
  return (
    <div className="tech-roadmap">
      <p className="tech-roadmap-intro">
        Bagzine was built in deliberate layers: collect marketplace listings, validate and match
        them to a canonical catalog, store append-only price history, expose analytics through a
        read-only API, and publish a React dashboard. Each stage below explains the design choices,
        what was built, and links to the source on GitHub.
      </p>

      <div className="tech-roadmap-track">
        <RoadmapStep
          number={1}
          title="Scrapy project skeleton"
          summary="Phase 1 started with the crawler alone — no database, API, or frontend — so scraping logic could be tested end-to-end before anything else was wired up."
          details={[
            "The Scrapy project lives under scrapers/ with project name bags. scrapy.cfg tells Scrapy where to find spiders; bags/settings.py configures polite crawling (robots.txt, download delay) and registers the ordered item pipeline.",
            "Every spider yields a ListingItem — a typed bag of fields (marketplace, source_listing_id, url, title, price, condition, image_url, etc.) defined in items.py. Spiders stay thin: they fetch raw marketplace data and map it into this shared shape.",
            "dev_sample.py provides two offline mock listings so the full pipeline can be exercised without API keys or network access — useful for tests and local development.",
          ]}
          tools={["Python 3", "Scrapy", "ItemAdapter", "Pydantic", "python-dotenv"]}
          folder={{ path: "scrapers", label: "scrapers/" }}
          files={[
            { path: "PHASE1.md", label: "PHASE1.md — step-by-step build plan" },
            { path: "scrapers/scrapy.cfg", label: "scrapy.cfg — Scrapy project entry point" },
            { path: "scrapers/bags/items.py", label: "items.py — ListingItem field definitions" },
            { path: "scrapers/bags/settings.py", label: "settings.py — throttling, .env loading, pipeline order" },
            { path: "scrapers/bags/schemas.py", label: "schemas.py — Pydantic validation rules" },
            { path: "scrapers/bags/utils.py", label: "utils.py — condition normalization & content hashing" },
            { path: "scrapers/bags/spiders/dev_sample.py", label: "dev_sample.py — offline mock spider" },
            { path: "requirements-scrapers.txt", label: "requirements-scrapers.txt — crawler dependencies" },
          ]}
        />

        <RoadmapStep
          number={2}
          title="Item pipeline — how data is processed"
          summary="Scrapy pipelines are the backbone of data quality. Each listing passes through the same ordered stages whether it was scraped locally or loaded from S3 — business logic lives in one place."
          details={[
            "Pipelines are registered in settings.py with numeric priorities (100–400) that define execution order. An item that fails validation or is identified as junk is dropped immediately via DropItem and never reaches Postgres.",
            "The design separates concerns: schema validation (Pydantic), cleaning (normalization), optional raw archiving (S3), catalog matching (title parsing + product variants), and persistence (SQLAlchemy upserts). This makes each stage independently testable — see scrapers/tests/test_pipelines.py.",
            "On the AWS path, stages 4–7 are skipped inside Lambda and replayed later by scripts/load_from_s3.py, so the same junk-filtering and matching rules apply regardless of where the crawl ran.",
          ]}
          tools={["Scrapy pipelines", "Pydantic", "SQLAlchemy", "boto3"]}
          folder={{ path: "scrapers/bags", label: "scrapers/bags/" }}
          files={[
            { path: "scrapers/bags/pipelines.py", label: "pipelines.py — all seven pipeline classes" },
            { path: "scrapers/bags/product_matching.py", label: "product_matching.py — variant lookup & creation" },
            { path: "scrapers/bags/product_linking.py", label: "product_linking.py — junk rules & link thresholds" },
            { path: "scrapers/bags/title_parser.py", label: "title_parser.py — brand/model/size parsing" },
            { path: "scrapers/tests/test_pipelines.py", label: "test_pipelines.py — pipeline unit tests" },
          ]}
        >
          <div className="tech-pipeline-flow" aria-label="Scrapy pipeline stages">
            <PipelineStage
              step="1"
              title="Validation"
              detail="Runs ListingSchema (Pydantic): marketplace must be ebay/fashionphile, price must be positive, url and source_listing_id required. Invalid items are dropped with a logged warning."
            />
            <PipelineStage
              step="2"
              title="Normalization"
              detail="Trims titles, uppercases currency, maps condition_raw → condition_normalized (excellent/good/fair), sets status=active and scraped_at, and computes content_hash to detect listing changes over time."
            />
            <PipelineStage
              step="3"
              title="S3 archive"
              detail="Buffers items in memory and flushes one .jsonl file per spider run to S3 (bronze layer). Disabled locally unless S3_ARCHIVE_BUCKET is set; always on in the Lambda crawl profile."
            />
            <PipelineStage
              step="4"
              title="Junk filter"
              detail="Parses the title and drops non-bags: organizers, wallets, charms, dust bags, and listings where no tracked brand/model can be identified. Uses regex patterns in product_linking.py."
            />
            <PipelineStage
              step="5"
              title="Product link"
              detail="Extracts brand, model, size, leather, and color from the title, scores match confidence, flags suspicious prices, and links the listing to a product_variant row in the catalog (or leaves it unlinked if confidence is too low)."
            />
            <PipelineStage
              step="6"
              title="Postgres listing"
              detail="Upserts the listings table by marketplace + source_listing_id: updates title, url, condition, image_url, match metadata, and last_seen_at on repeat scrapes; sets listing_id for the next stage."
            />
            <PipelineStage
              step="7"
              title="Price observation"
              detail="Appends a row to price_observations only when the ask price changes (or on first sighting). Append-only history powers the 'Asking price over time' chart on listing pages."
            />
          </div>
        </RoadmapStep>

        <RoadmapStep
          number={3}
          title="eBay Browse API spider"
          summary="ebay_api is the primary data source. It uses eBay's official Browse API with OAuth 2.0 client-credentials flow — no HTML scraping, no browser automation."
          details={[
            "Credentials (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET) are loaded from .env at the project root. Without credentials the spider falls back to two mock eBay-shaped items so the pipeline can still be tested.",
            "Each crawl job accepts a search query, result limit, and optional pagination. The daily schedule (scripts/crawl_daily.sh and lambda_handler.py) runs targeted queries per flagship model — Hermès Birkin/Kelly, Chanel Classic Flap, Louis Vuitton Neverfull, etc. — with negative keywords to exclude accessories.",
            "Results are mapped into ListingItem with marketplace=ebay, including image_url from eBay's image field. Custom settings relax robots.txt (API calls, not page scraping) and allow modest concurrency.",
          ]}
          tools={["eBay Browse API", "OAuth 2.0", "httpx", "Scrapy"]}
          folder={{ path: "scrapers/bags/spiders", label: "scrapers/bags/spiders/" }}
          files={[
            { path: "scrapers/bags/spiders/ebay_api.py", label: "ebay_api.py — Browse API spider" },
            { path: ".env.example", label: ".env.example — credential template" },
            { path: "scrapers/tests/test_ebay_api_spider.py", label: "test_ebay_api_spider.py — spider tests" },
            { path: "scripts/backfill_listing_images.py", label: "backfill_listing_images.py — image URL backfill" },
          ]}
        />

        <RoadmapStep
          number={4}
          title="Fashionphile spider"
          summary="fashionphile adds a second marketplace using Fashionphile's public Shopify storefront API — plain JSON, no bot challenges, no Playwright."
          details={[
            "The spider works in two stages: first it pages through /collections/handbags/products.json to discover product handles and filter by vendor (tracked luxury brands); then it fetches each product's HTML page for the condition rating and JSON-LD structured data (name, brand, price, currency) that the collection feed does not include.",
            "Fashionphile was chosen because, unlike The RealReal (PerimeterX CAPTCHA on every request), it serves unauthenticated JSON and allows crawling /collections and /products per robots.txt. The RealReal spider exists for offline mock testing only.",
            "A use_mock=1 flag yields fixed test data without network access, matching the pattern used by dev_sample and ebay_api.",
          ]}
          tools={["Shopify products.json", "JSON-LD", "Scrapy", "regex"]}
          folder={{ path: "scrapers/bags/spiders", label: "scrapers/bags/spiders/" }}
          files={[
            { path: "scrapers/bags/spiders/fashionphile.py", label: "fashionphile.py — Shopify + JSON-LD spider" },
            { path: "scrapers/bags/spiders/therealreal.py", label: "therealreal.py — offline mock only (blocked live)" },
            { path: "scrapers/tests/test_fashionphile_spider.py", label: "test_fashionphile_spider.py — spider tests" },
          ]}
        />

        <RoadmapStep
          number={5}
          title="Database — schema, migrations & Docker"
          summary="PostgreSQL is the system of record. It runs locally in Docker (port 5433 to avoid conflicts with a system Postgres on 5432) and is never exposed to AWS Lambda."
          details={[
            "The schema evolved through seven Alembic migrations: core listings + price_observations (001), product catalog (002–004), SQL analytics views (005), investigation matching flags (006), and listing image_url (007). Each migration is versioned under db/migrations/versions/.",
            "The catalog hierarchy is Brand → Model → ProductVariant (a specific size/leather/color combination). Listings link to a variant when match confidence is high enough; price_observations are append-only so historical ask prices are never overwritten.",
            "Analytics views (v_latest_listing_prices, v_model_price_stats, v_price_history, etc.) pre-join listings with their latest price and catalog attributes. The API reads almost exclusively from these views rather than raw tables — documented in db/analytics/VIEWS.md.",
            "scripts/setup_db.sh starts Docker Compose, waits for Postgres to be healthy, and runs alembic upgrade head.",
          ]}
          tools={["PostgreSQL 16", "Docker Compose", "Alembic", "SQLAlchemy 2"]}
          folder={{ path: "db", label: "db/" }}
          files={[
            { path: "docker-compose.yml", label: "docker-compose.yml — Postgres container on :5433" },
            { path: "db/models.py", label: "models.py — ORM models (Brand, Model, Listing, PriceObservation…)" },
            { path: "db/session.py", label: "session.py — SQLAlchemy session factory" },
            { path: "db/alembic.ini", label: "alembic.ini — migration config" },
            { path: "db/migrations/versions/001_initial.py", label: "001 — listings & price_observations" },
            { path: "db/migrations/versions/004_brands_models_variants.py", label: "004 — catalog hierarchy" },
            { path: "db/migrations/versions/005_analytics_views.py", label: "005 — SQL analytics views" },
            { path: "db/migrations/versions/006_investigation_matching.py", label: "006 — is_confident flag for comparables" },
            { path: "db/migrations/versions/007_listing_image_url.py", label: "007 — listing image_url column" },
            { path: "db/analytics/VIEWS.md", label: "VIEWS.md — view documentation & example queries" },
            { path: "scripts/setup_db.sh", label: "setup_db.sh — start DB & run migrations" },
            { path: "scripts/query_db.sh", label: "query_db.sh — quick SQL console" },
          ]}
        />

        <RoadmapStep
          number={6}
          title="Read-only backend API"
          summary="Phase B added a thin FastAPI layer that serves pre-computed analytics from Postgres views — no writes, no auth, designed purely for the dashboard."
          details={[
            "api/main.py defines GET-only routes: /models (catalog overview), /listings (filterable browse), /listings/{id} (detail + price history), /listings/{id}/investigation (comparable-set report), /filters (distinct attribute values), and /health.",
            "api/queries.py holds all SQL. The investigation endpoint is the most complex: it tries progressively broader comparison groups (exact variant → size+leather+condition → model-only) until it finds at least five confident comparables, then computes P25/median/P75, percentile, and verdict (below/within/above typical range).",
            "api/schemas.py defines Pydantic response models shared with the frontend types. CORS is open for local dev. scripts/run_api.sh starts Uvicorn on :8000 with hot reload.",
          ]}
          tools={["FastAPI", "Uvicorn", "Pydantic v2", "SQLAlchemy"]}
          folder={{ path: "api", label: "api/" }}
          files={[
            { path: "api/main.py", label: "main.py — route definitions" },
            { path: "api/queries.py", label: "queries.py — SQL & investigation logic" },
            { path: "api/schemas.py", label: "schemas.py — response models" },
            { path: "api/deps.py", label: "deps.py — database session dependency" },
            { path: "api/tests/test_api.py", label: "test_api.py — API integration tests" },
            { path: "requirements-api.txt", label: "requirements-api.txt — API dependencies" },
            { path: "scripts/run_api.sh", label: "run_api.sh — start API on :8000" },
          ]}
        />

        <RoadmapStep
          number={7}
          title="React dashboard (frontend)"
          summary="Phase C is a Vite + React + TypeScript single-page app that consumes the API and presents Bagzine's editorial design — catalog browsing, model dashboards, and per-listing investigation reports."
          details={[
            "web/src/main.tsx wires React Router routes: /prices (explore catalog with brand sections and model tiles), /explore/:brand/:model (model dashboard with filters and listing grid), /listings/:id (investigation report with price-position chart and comparables), plus story pages for brand and creator content.",
            "web/src/api.ts is a thin fetch client over the FastAPI endpoints. Shared TypeScript types in types.ts mirror api/schemas.py. Recharts powers the asking-price-over-time chart on listing pages.",
            "Key UI components: CatalogModelTile (brand catalog grid), ListingPhoto (real eBay listing images), StoryDeck (scrollable story cards), ScrollToTop (fixes navigation scroll position). Styling is custom CSS in index.css — Bodoni headings, minimal borders, no component library.",
            "scripts/run_dashboard.sh installs npm deps and starts Vite dev server on :5173. The API must be running separately on :8000.",
          ]}
          tools={["React 18", "TypeScript", "Vite 6", "React Router 6", "Recharts"]}
          folder={{ path: "web/src", label: "web/src/" }}
          files={[
            { path: "web/src/main.tsx", label: "main.tsx — app routes" },
            { path: "web/src/api.ts", label: "api.ts — API fetch client" },
            { path: "web/src/types.ts", label: "types.ts — shared TypeScript types" },
            { path: "web/src/pages/OverviewPage.tsx", label: "OverviewPage.tsx — explore catalog (/prices)" },
            { path: "web/src/pages/ModelExplorePage.tsx", label: "ModelExplorePage.tsx — model dashboard" },
            { path: "web/src/pages/ListingDetailPage.tsx", label: "ListingDetailPage.tsx — investigation report" },
            { path: "web/src/components/CatalogModelTile.tsx", label: "CatalogModelTile.tsx — model tile with bag image" },
            { path: "web/src/components/PriceChart.tsx", label: "PriceChart.tsx — price history chart" },
            { path: "web/src/lib/modelImages.ts", label: "modelImages.ts — catalog image mapping" },
            { path: "web/package.json", label: "package.json — frontend dependencies" },
            { path: "scripts/run_dashboard.sh", label: "run_dashboard.sh — dev server on :5173" },
          ]}
        />

        <RoadmapStep
          number={8}
          title="AWS pipeline"
          summary="The AWS path automates daily crawls in the cloud: EventBridge triggers a Lambda container running Scrapy, results land in S3 as immutable JSONL, and a local loader replays them into Postgres."
          details={[
            "Lambda never connects to Postgres by design — it uses settings_lambda.py, a DB-free Scrapy profile that runs only validation, normalization, and S3 archiving. This keeps the cloud footprint small and avoids needing RDS.",
            "lambda_handler.py mirrors the job list in scripts/crawl_daily.sh (ebay_api queries per flagship model + fashionphile). The container image is built from Dockerfile.lambda and pushed to ECR; Terraform provisions S3, Lambda, EventBridge, IAM, CloudWatch alarms, SNS failure alerts, and a cost budget.",
            "scripts/load_from_s3.py lists new S3 objects, downloads each .jsonl file, and replays every raw item through pipeline stages 4–7 (junk filter → product link → Postgres listing → price observation). A state file (logs/s3_loaded_keys.json) tracks which keys have already been processed.",
            "scripts/spark_silver_consolidate.py is a future analytics step that deduplicates the bronze archive into Parquet — not part of the live dashboard path yet.",
          ]}
          tools={["AWS Lambda", "S3", "ECR", "EventBridge", "Terraform", "Docker", "boto3"]}
          folder={{ path: "infra/terraform", label: "infra/terraform/" }}
          files={[
            { path: "scrapers/bags/lambda_handler.py", label: "lambda_handler.py — Lambda entrypoint & job list" },
            { path: "scrapers/bags/settings_lambda.py", label: "settings_lambda.py — DB-free crawl profile" },
            { path: "scripts/load_from_s3.py", label: "load_from_s3.py — S3 → Postgres loader" },
            { path: "Dockerfile.lambda", label: "Dockerfile.lambda — Lambda container image" },
            { path: "requirements-lambda.txt", label: "requirements-lambda.txt — Lambda image dependencies" },
            { path: "infra/terraform/lambda.tf", label: "lambda.tf — Lambda function resource" },
            { path: "infra/terraform/s3.tf", label: "s3.tf — bronze archive bucket" },
            { path: "infra/terraform/eventbridge.tf", label: "eventbridge.tf — cron schedule" },
            { path: "infra/terraform/README.md", label: "terraform/README.md — deploy guide" },
            { path: "scripts/crawl_daily.sh", label: "crawl_daily.sh — local daily crawl (cron)" },
            { path: "scripts/install_daily_schedule.sh", label: "install_daily_schedule.sh — macOS launchd setup" },
            { path: "scrapers/tests/test_s3_pipeline.py", label: "test_s3_pipeline.py — S3 archive tests" },
            { path: "scrapers/tests/test_load_from_s3.py", label: "test_load_from_s3.py — loader tests" },
          ]}
        >
          <div className="tech-aws-flow" aria-label="AWS data flow">
            <span>EventBridge (cron)</span>
            <span className="tech-aws-arrow">→</span>
            <span>Lambda (Scrapy)</span>
            <span className="tech-aws-arrow">→</span>
            <span>S3 (bronze JSONL)</span>
            <span className="tech-aws-arrow">→</span>
            <span>load_from_s3.py</span>
            <span className="tech-aws-arrow">→</span>
            <span>Postgres</span>
          </div>
        </RoadmapStep>
      </div>

      <p className="tech-roadmap-repo">
        Full repository:{" "}
        <a href={`${REPO}/tree/${BRANCH}`} target="_blank" rel="noreferrer">
          github.com/tl4732-cyber/luxury_vintage_bag_price ↗
        </a>
      </p>
    </div>
  );
}
