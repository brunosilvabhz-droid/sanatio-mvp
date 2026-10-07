#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

if [[ -f .env.integrador ]]; then
  set -a
  source .env.integrador
  set +a
fi

args=(
  patient_name_resolver:app
  --host "${PATIENT_RESOLVER_HOST:-0.0.0.0}"
  --port "${PATIENT_RESOLVER_PORT:-5191}"
  --proxy-headers
  --no-server-header
)

if [[ -n "${PATIENT_RESOLVER_SSL_CERTFILE:-}" && -n "${PATIENT_RESOLVER_SSL_KEYFILE:-}" ]]; then
  args+=(
    --ssl-certfile "$PATIENT_RESOLVER_SSL_CERTFILE"
    --ssl-keyfile "$PATIENT_RESOLVER_SSL_KEYFILE"
  )
fi

exec uvicorn "${args[@]}"
