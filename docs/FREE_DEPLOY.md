# Free deployment: GitHub Pages + Neon + Render

Total cost: **$0**. Tradeoff: the API sleeps when idle (first visit may take ~30–60s).

## What you get

| Part | Host | URL |
|------|------|-----|
| Website | GitHub Pages | `https://tl4732-cyber.github.io/BAGZINE/` |
| Database | Neon (free) | (connection string only) |
| API | Render (free web) | `https://bagzine-api.onrender.com` |

---

## Step 1 — Create a free Neon database

1. Go to [neon.tech](https://neon.tech) and sign up (GitHub login is fine).
2. Click **New Project** → name it `bagzine`.
3. Open **Dashboard → Connection details**.
4. Copy the **connection string** (URI format). It looks like:
   ```
   postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Save it somewhere safe — you'll paste it into Render in Step 3.

---

## Step 2 — Export your local data

On your Mac, with Docker Postgres running:

```bash
cd ~/Projects/luxury_vintage_bag_price

# Start local Postgres if needed
docker compose up -d

# Export your database
bash scripts/export_db_snapshot.sh
```

This creates `bagzine_snapshot.sql` in the project root.

Import it into Neon:

```bash
psql "YOUR_NEON_CONNECTION_STRING" < bagzine_snapshot.sql
```

If `psql` is not installed: `brew install libpq` then `brew link --force libpq`.

Verify:

```bash
psql "YOUR_NEON_CONNECTION_STRING" -c "SELECT COUNT(*) FROM listings;"
```

You should see ~4000+ rows.

---

## Step 3 — Deploy the API on Render (free)

1. Go to [render.com](https://render.com) and sign up with GitHub.
2. Click **New +** → **Blueprint**.
3. Connect the **BAGZINE** repo and select branch `main`.
4. Render reads `render.yaml` and creates a web service named `bagzine-api`.
5. When asked for **DATABASE_URL**, paste your Neon connection string from Step 1.
6. Click **Apply** and wait for the deploy to finish (green **Live**).
7. Copy your API URL, e.g. `https://bagzine-api.onrender.com`.

Test it:

```bash
curl https://bagzine-api.onrender.com/health
curl https://bagzine-api.onrender.com/models
```

Both should return JSON (not an error page).

---

## Step 4 — Connect the website to the API

1. Open your repo on GitHub → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Name: `VITE_API_URL`
4. Value: your Render API URL with **no trailing slash**, e.g.:
   ```
   https://bagzine-api.onrender.com
   ```
5. Go to **Actions** → **Deploy to GitHub Pages** → **Run workflow** → branch `main` → **Run workflow**.

Wait for the workflow to finish, then open:

**https://tl4732-cyber.github.io/BAGZINE/prices**

Click a bag model — listings and prices should load.

---

## Step 5 — Refresh data later

After you scrape new listings locally:

```bash
bash scripts/export_db_snapshot.sh
psql "YOUR_NEON_CONNECTION_STRING" < bagzine_snapshot.sql
python3 scripts/export_models_snapshot.py
git add web/public/data/models.json
git commit -m "Refresh catalog snapshot"
git push origin main
```

No Render redeploy needed for DB updates. Push the models snapshot if you want the static catalog fallback updated too.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| API returns 503 on first visit | Free Render sleeps — wait 30–60s and retry |
| `Failed to fetch` on explore | Check `VITE_API_URL` secret and re-run Pages deploy |
| `health` shows `database: error` | Wrong `DATABASE_URL` on Render — re-paste Neon string (use **Show password** → copy) |
| Render deploy failed | Open the failed deploy → **Logs**; common fixes: set `DATABASE_URL`, redeploy after latest `main` push |
| Password has special characters | In Neon, reset password to letters+numbers only, update `DATABASE_URL` on Render |
| Import fails on Neon | Ensure connection string ends with `?sslmode=require` |
