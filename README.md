# BAGZINE

**Live site:** [https://tl4732-cyber.github.io/BAGZINE/](https://tl4732-cyber.github.io/BAGZINE/)

BAGZINE is a luxury vintage handbag price explorer. Browse bags by brand, compare asking prices across marketplaces, and see where a listing sits relative to similar bags on the market.

The goal is simple: make secondhand bag shopping less like detective work. No sales pitch — just a clearer picture of what bags are actually going for.

---

## What it does

- **Explore** — browse tracked brands and models (Hermès, Chanel, Louis Vuitton, and more)
- **Compare** — see listings, filters, and price context for a specific bag
- **Investigate** — open a listing to see how its ask compares to similar bags (median, percentile, comparables)

Data currently comes from **eBay** and **Fashionphile**, with more sources planned over time.

---

## How this was built

This started as a personal project combining two things I care about: handbags and learning to build with data.

The process, in plain terms:

1. **Collect** — scrapers pull listing data from marketplaces on a schedule
2. **Store** — listings and price history live in a PostgreSQL database
3. **Organize** — titles are parsed and matched to brands, models, size, color, and leather
4. **Analyze** — SQL views summarize prices, trends, and comparables
5. **Serve** — a read-only API exposes that data to the website
6. **Show** — a React frontend turns it into something you can actually browse

Along the way I learned how the pieces fit together: from raw web data → cleaned records → database → API → live site. The in-app **Tech Specs** page walks through each step in more detail.

---

## Tools & stack

| Layer | What we use |
|-------|-------------|
| **Frontend** | React, TypeScript, Vite, React Router |
| **Charts** | Recharts |
| **API** | Python, FastAPI |
| **Database** | PostgreSQL |
| **Scraping** | Scrapy |
| **Migrations** | Alembic, SQLAlchemy |
| **Local dev** | Docker |
| **Hosting (free)** | GitHub Pages (site), Render (API), Neon (database) |

---

## Running locally

If you want to run the project on your machine:

```bash
cp .env.example .env
docker compose up -d
make setup          # or: bash scripts/setup_db.sh
bash scripts/run_api.sh
cd web && npm install && npm run dev
```

- Site: [http://localhost:5173](http://localhost:5173)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

For deployment notes, see [`docs/FREE_DEPLOY.md`](docs/FREE_DEPLOY.md).

---

## Status

BAGZINE is live and evolving. Prices reflect active marketplace **asking** prices, not completed sales. The dataset grows as scrapers run and new listings are added.

Built by [tl4732-cyber](https://github.com/tl4732-cyber).
