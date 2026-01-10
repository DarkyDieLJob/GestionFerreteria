#!/usr/bin/env bash
set -euo pipefail
PROJECT_NAME=${PROJECT_NAME:-gestionferreteria}
PROJECT_MODE=${PROJECT_MODE:-local}
TABLET_MODE=${TABLET_MODE:-true}
if [ ! -f "src/.env" ]; then
  if [ -f "src/.env.example" ]; then
    cp src/.env.example src/.env
  else
    touch src/.env
  fi
fi
if ! grep -q '^PROJECT_MODE=' src/.env; then
  echo "PROJECT_MODE=${PROJECT_MODE}" >> src/.env
fi
if ! grep -q '^TABLET_MODE=' src/.env; then
  echo "TABLET_MODE=${TABLET_MODE}" >> src/.env
fi
docker compose -p "$PROJECT_NAME" up -d --build app worker
docker compose -p "$PROJECT_NAME" exec app python src/manage.py migrate --noinput
docker compose -p "$PROJECT_NAME" exec app python src/manage.py collectstatic --noinput
