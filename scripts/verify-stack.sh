#!/usr/bin/env bash
# Local verification: frontend production build + backend imports + optional API smoke (start server first).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "==> Frontend: npm run build"
cd "$ROOT/frontend"
npm run build

echo "==> Backend: import app + geocode smoke"
cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  echo "No .venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
.venv/bin/python -c "
from main import app
from services.geocode import resolve_coordinates
from config import get_settings
s = get_settings()
c = resolve_coordinates('Chicago, IL', s.google_places_api_key, s.geoapify_api_key)
assert c, 'geocode failed'
print('geocode ok:', c)
print('routes:', len(app.routes))
"

if [[ "${1:-}" == "--smoke" ]]; then
  echo "==> Expect API at http://127.0.0.1:8000 (uvicorn main:app --port 8000)"
  curl -sf "http://127.0.0.1:8000/api/ping" | head -c 200 && echo && echo "ping ok" || {
    echo "Smoke failed: start backend first, then: $0 --smoke"
    exit 1
  }
fi

echo "verify-stack: OK"
