#!/usr/bin/env bash
set -euo pipefail

# Script compatible con Podman o Docker sin plugin docker-compose.
# Permite levantar PostgreSQL + App SGI 100% offline en http://localhost:8080

NETWORK="lfb-sgi-net"
DB_CONT="lfb-sgi-db"
APP_CONT="lfb-sgi-app"
VOLUME="lfb_postgres_data"
IMAGE="lfb-sgi-app:latest"

echo "1) Creando red y volumen..."
docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"
docker volume inspect "$VOLUME" >/dev/null 2>&1 || docker volume create "$VOLUME"

echo "2) Iniciando PostgreSQL..."
if ! docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONT}$"; then
  docker run -d \
    --name "$DB_CONT" \
    --network "$NETWORK" \
    -e POSTGRES_DB=sgi_finca \
    -e POSTGRES_USER=sgi_user \
    -e POSTGRES_PASSWORD=sgi_finca_2026_password \
    -v "${VOLUME}:/var/lib/postgresql/data" \
    docker.io/library/postgres:16-alpine
else
  docker start "$DB_CONT" >/dev/null || true
fi

echo "3) Esperando a PostgreSQL..."
for i in $(seq 1 20); do
  if docker exec "$DB_CONT" pg_isready -U sgi_user -d sgi_finca >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "4) Construyendo imagen del SGI..."
docker build -t "$IMAGE" .

echo "5) Iniciando aplicacion SGI en http://localhost:8080 ..."
docker rm -f "$APP_CONT" >/dev/null 2>&1 || true
docker run -d \
  --name "$APP_CONT" \
  --network "$NETWORK" \
  -p 8080:8000 \
  -e DATABASE_URL="postgresql://sgi_user:sgi_finca_2026_password@${DB_CONT}:5432/sgi_finca" \
  -e SESSION_SECRET="lfb-sgi-colima-2026-secret-key" \
  "$IMAGE"

echo "Listo! Abre http://localhost:8080 en tu navegador."
