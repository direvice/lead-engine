#!/usr/bin/env bash
# Usage: ./scripts/wire-frontend-to-api.sh https://your-fastapi-host.com
# Sets NEXT_PUBLIC_API_URL on Vercel (production + preview) and triggers a production deploy.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${1:?Usage: $0 https://your-api.example.com}"
API_URL="${API_URL%/}"
cd "$ROOT/frontend"
npx vercel@latest env add NEXT_PUBLIC_API_URL production --value "$API_URL" --yes --force
npx vercel@latest env add NEXT_PUBLIC_API_URL preview --value "$API_URL" --yes --force
echo "Redeploying production so the new variable is picked up…"
npx vercel@latest deploy --prod --yes
echo "Done. Open your Vercel URL and the dashboard should reach $API_URL"
