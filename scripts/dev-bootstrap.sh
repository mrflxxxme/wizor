#!/usr/bin/env bash
# Идемпотентный bootstrap dev-окружения WIZOR (обёртка над `make dev-bootstrap`).
# Цель AC-1: `git clone && cp .env.example .env && make dev-bootstrap` ≤ 600 сек.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[bootstrap] подготовка infra/.env"
[ -f infra/.env ] || cp infra/.env.example infra/.env

echo "[bootstrap] поднимаю dev-стек (docker compose --wait)"
docker compose -f infra/docker-compose.dev.yml up -d --build --wait

echo "[bootstrap] готово:"
echo "  backend : http://localhost:8000/health"
echo "  frontend: http://localhost:3000"
echo "  keycloak: http://localhost:8080 (realm wizor-dev)"
