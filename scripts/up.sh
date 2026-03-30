#!/usr/bin/env bash
# One command: full app in Docker (needs Docker Desktop). Open http://localhost:3000
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ ! -f backend/.env ]]; then
  cp backend/.env.example backend/.env
  echo "Created backend/.env — add at least GEOAPIFY_API_KEY, then run this script again."
  exit 1
fi
exec docker compose up --build
