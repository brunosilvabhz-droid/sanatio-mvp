#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

if [[ -f .env.integrador ]]; then
  set -a
  source .env.integrador
  set +a
fi

exec uvicorn patient_name_resolver:app \
  --host "${PATIENT_RESOLVER_HOST:-0.0.0.0}" \
  --port "${PATIENT_RESOLVER_PORT:-5191}" \
  --proxy-headers \
  --no-server-header
