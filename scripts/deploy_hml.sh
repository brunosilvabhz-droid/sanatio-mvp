#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/apps/sanatio"
BRANCH="main"
BACKUP_DIR="${APP_DIR}/backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
COMPOSE_BACKUP="/tmp/sanatio-docker-compose-${TIMESTAMP}.yml"

cd "$APP_DIR"

echo "[1/8] Validando ambiente"
command -v git >/dev/null
command -v docker >/dev/null
docker compose version >/dev/null
test -f docker-compose.yml

if ! git diff --quiet -- . ':!docker-compose.yml' || ! git diff --cached --quiet; then
  echo "ERRO: existem alteracoes locais alem do docker-compose.yml. Revise com: git status --short"
  exit 1
fi

echo "[2/8] Preservando configuracao local do HML"
cp docker-compose.yml "$COMPOSE_BACKUP"

restore_compose() {
  if [[ -f "$COMPOSE_BACKUP" ]]; then
    cp "$COMPOSE_BACKUP" "$APP_DIR/docker-compose.yml"
  fi
}
trap restore_compose EXIT

git restore -- docker-compose.yml

echo "[3/8] Atualizando codigo"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git merge --ff-only "origin/$BRANCH"
restore_compose

echo "[4/8] Criando backup do PostgreSQL"
mkdir -p "$BACKUP_DIR"
docker compose up -d postgres

for attempt in {1..30}; do
  if docker compose exec -T postgres pg_isready -U "${POSTGRES_USER:-sanatio}" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    echo "ERRO: PostgreSQL nao ficou disponivel."
    exit 1
  fi
  sleep 2
done

docker compose exec -T postgres pg_dump \
  -U "${POSTGRES_USER:-sanatio}" \
  -d "${POSTGRES_DB:-sanatio}" \
  -Fc > "${BACKUP_DIR}/sanatio_hml_${TIMESTAMP}.dump"

echo "[5/8] Gerando novas imagens"
docker compose build --no-cache backend frontend

echo "[6/8] Aplicando migracoes"
docker compose run --rm backend alembic upgrade head

echo "[7/8] Reiniciando aplicacao"
docker compose up -d --remove-orphans postgres backend frontend

echo "[8/8] Validando publicacao"
for attempt in {1..30}; do
  if curl --fail --silent http://localhost:8000/health >/dev/null; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    echo "ERRO: backend nao respondeu em http://localhost:8000/health"
    docker compose logs --tail=150 backend
    exit 1
  fi
  sleep 2
done

curl --fail --silent --output /dev/null http://localhost:5173
docker compose ps

rm -f "$COMPOSE_BACKUP"
trap - EXIT

echo "Deploy HML concluido no commit $(git rev-parse --short HEAD)."
echo "Backup: ${BACKUP_DIR}/sanatio_hml_${TIMESTAMP}.dump"
