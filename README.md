# Lead Engine

Autonomous local business lead generation: multi-source discovery, Playwright website analysis, scoring, Ollama-first AI routing (Gemini fallback), revenue estimates, competitor hints, call scripts, gTTS briefings, morning digest email, APScheduler jobs, and a Next.js dashboard.

## Setup (order)

1. **Python venv** (from repo root):

   ```bash
   cd lead-bot/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

2. **Ollama** (optional but recommended):

   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull llama3.2
   ollama pull phi3:mini
   ```

3. **API keys** — copy `backend/.env.example` to `backend/.env`. Prefer **`GEOAPIFY_API_KEY`** for geocoding + Places-style discovery (no Google bill). Optional: `GOOGLE_PLACES_API_KEY` (Places + PageSpeed), `GEMINI_API_KEY` and/or Ollama for AI, `YELP_API_KEY`, Gmail fields for digest.

4. **Database** — tables are created automatically on API startup (`init_db`). Optional Alembic:

   ```bash
   cd lead-bot/backend && alembic upgrade head
   ```

5. **Backend**:

   ```bash
   cd lead-bot/backend
   source .venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

6. **Frontend**:

   ```bash
   cd lead-bot/frontend && npm install && npm run dev
   ```

7. **First scan** — open [http://localhost:3000/scan](http://localhost:3000/scan), set location/radius/categories, start scan. Dashboard: [http://localhost:3000](http://localhost:3000).

Next.js rewrites proxy `/api/*` and `/static/*` to `http://127.0.0.1:8000` **in development only**. Production (Vercel) uses `NEXT_PUBLIC_API_URL`.

## Verify locally

```bash
chmod +x scripts/*.sh
./scripts/verify-stack.sh          # Next build + backend imports + Geoapify/OSM geocode
./scripts/verify-stack.sh --smoke  # also curl /api/ping (start uvicorn on :8000 first)
```

**Near–zero-touch:** see [ZERO-TOUCH.md](ZERO-TOUCH.md) — either connect Railway + Vercel to GitHub **once** (then only `git push`), or run **`./scripts/up.sh`** with Docker for a full local stack.

## Deploy backend (Docker)

The API uses **Playwright** and must run on a container host (Railway, Render, Fly, etc.) — not Vercel.

1. **Railway:** New project → **Deploy from GitHub** (or CLI). Set **Root Directory** to `lead-bot/backend` (or the repo root that contains `backend/` and point the Dockerfile path to `backend/Dockerfile`).
2. **Environment variables** (minimum):
   - `GEOAPIFY_API_KEY` — discovery + geocode without Google
   - `CORS_ORIGINS` — comma-separated origins, must include your Vercel URL(s), e.g. `https://your-app.vercel.app,http://localhost:3000`
   - Optional: `DATABASE_URL` (Postgres) for a durable DB; default SQLite works but resets on ephemeral disks.
3. Railway reads [`backend/railway.toml`](backend/railway.toml) and [`backend/Dockerfile`](backend/Dockerfile). Health check: `GET /api/ping`.

```bash
# After the API is live:
./scripts/deploy-all.sh https://YOUR-API.up.railway.app
```

That sets `NEXT_PUBLIC_API_URL` on Vercel (production) and redeploys the frontend.

## Deploy frontend on Vercel

1. Connect the repo with **Root Directory** `lead-bot/frontend`, or deploy from that folder with `npx vercel deploy --prod`.
2. Set **`NEXT_PUBLIC_API_URL`** to your public FastAPI base URL (no trailing slash). Use `./scripts/wire-frontend-to-api.sh https://...` if the CLI is logged in.
3. Ensure **`CORS_ORIGINS`** on the API includes `https://your-app.vercel.app`.

**Note:** A `*.loca.lt` tunnel is fine for a quick demo only; use a stable API URL in production.

## Project layout

- `backend/` — FastAPI, discovery, scraping, analysis, AI router, outreach, scheduler
- `frontend/` — Next.js 14 App Router, Tailwind, Framer Motion, Recharts

## Rules implemented

- Scraping is async; failed scrapes still produce a lead row.
- **AI:** Ollama is tried before Gemini for full analysis and pitch (saves quota); Gemini used on failure if configured.
- AI responses are parsed as JSON with retry on invalid JSON.
- Screenshots are JPEG-compressed (target under 200KB).
- Revenue copy is framed as conservative estimates.

## License

Use at your own risk; respect robots.txt, site terms, and API quotas.
