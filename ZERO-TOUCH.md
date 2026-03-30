# As close to “you do nothing” as it gets

You cannot deploy to *our* cloud accounts without **one short setup** somewhere (that is true for every product). After that, you stop clicking around.

---

## Option A — Push only (recommended)

Do this **once**:

1. Push this repo to GitHub (if it is not there yet).
2. **Railway:** New project → Deploy from GitHub → set **Root Directory** to `backend` → add variables `GEOAPIFY_API_KEY`, `CORS_ORIGINS` (include your Vercel URL). Railway redeploys on every push to `main`.
3. **Vercel:** Import the same repo → **Root Directory** `frontend` → set `NEXT_PUBLIC_API_URL` to your Railway API URL (once). Vercel redeploys on every push to `main`.

After that you **only run `git push`**. No CLI, no manual redeploys.

---

## Option B — One command on your Mac (no Railway/Vercel)

If you have **Docker Desktop** installed:

```bash
chmod +x scripts/up.sh
./scripts/up.sh
```

First run creates `backend/.env` from `.env.example` if missing — add `GEOAPIFY_API_KEY`, run again. Then open **http://localhost:3000**.

---

## Why there is no “zero setup” cloud deploy

GitHub, Railway, and Vercel need **your** login or **your** API tokens. No tool can create those in your name without you doing that step once.
