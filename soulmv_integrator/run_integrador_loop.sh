#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source .venv/bin/activate

if [[ -f .env.integrador ]]; then
  set -a
  source .env.integrador
  set +a
fi

interval_minutes="${SANATIO_INTERVAL_MINUTES:-15}"
if ! [[ "$interval_minutes" =~ ^[1-9][0-9]*$ ]]; then
  echo "SANATIO_INTERVAL_MINUTES deve ser um inteiro maior que zero" >&2
  exit 2
fi

while true; do
  ./run_integrador.sh || true
  sleep "$((interval_minutes * 60))"
done
