#!/usr/bin/env bash
# One entrypoint after your backend has a public URL:
#   ./scripts/deploy-all.sh https://your-service.up.railway.app
# Prerequisites: Vercel CLI logged in (`npx vercel login`), frontend linked (cd frontend && npx vercel link).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${1:?Usage: $0 https://your-api-host.example.com}"
API_URL="${API_URL%/}"

echo "==> Wiring Vercel NEXT_PUBLIC_API_URL -> $API_URL"
"$ROOT/scripts/wire-frontend-to-api.sh" "$API_URL"

echo ""
echo "Done. Backend checklist (Railway / Fly / Render):"
echo "  - Root directory: backend (or Dockerfile path: backend/Dockerfile)"
echo "  - Env: GEOAPIFY_API_KEY, CORS_ORIGINS (your Vercel URL + https://...vercel.app)"
echo "  - Optional: GEMINI_API_KEY, YELP_API_KEY, DATABASE_URL (Postgres) for durable DB"
echo "  - Health: GET $API_URL/api/ping"
