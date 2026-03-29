# Configuration (what’s already done vs what only you can do)

## Already applied in this repo

1. **`backend/.env`** — Created (gitignored) with **`CORS_ORIGINS`** set for:
   - Local: `http://localhost:3000`, `http://127.0.0.1:3000`
   - Your Vercel app: `https://frontend-two-taupe-12.vercel.app`, `https://frontend-hi8q12wtt-linkboreds-projects.vercel.app`
2. **`backend/config.py`** — Default `cors_origins` matches the same list if you omit `CORS_ORIGINS` in `.env`.
3. **`scripts/wire-frontend-to-api.sh`** — One command to push your API URL to Vercel and redeploy (see below).

## Only you can do (secrets & hosting)

Nobody else can log into your Google / Vercel / host accounts. You still need to:

1. **Edit `backend/.env`** and set at least **`GOOGLE_PLACES_API_KEY`** (and optionally Gemini, Yelp, Gmail, etc.).
2. **Run the FastAPI app** on a public HTTPS host (Railway, Fly.io, Render, VPS, …). Note the base URL, e.g. `https://something.up.railway.app` (no trailing slash).

## Wire Vercel to that API (one command)

From the **`lead-bot`** folder, after your API is live:

```bash
./scripts/wire-frontend-to-api.sh https://YOUR-ACTUAL-API-HOST
```

That sets **`NEXT_PUBLIC_API_URL`** for **production** and **preview** on the linked Vercel project and runs a production deploy.

**Or manually:** Vercel → Project → Settings → Environment Variables → add **`NEXT_PUBLIC_API_URL`** = same URL → Redeploy.

## Check

- Open `https://YOUR-API/api/health` in a browser.
- Open your Vercel site; the “Backend not reachable” banner should disappear once the URL and CORS are correct.
