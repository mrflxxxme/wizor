# WIZOR — корневой Makefile (dev-оркестрация). Стек: PRD §12.
.DEFAULT_GOAL := help
COMPOSE := docker compose -f infra/docker-compose.dev.yml
ENV_FILE := infra/.env

.PHONY: help dev-bootstrap up down logs migrate seed \
        test backend-test frontend-test lint backend-lint frontend-lint clean

help: ## Показать список целей
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

$(ENV_FILE):
	@cp infra/.env.example $(ENV_FILE)
	@echo "Создан $(ENV_FILE) из примера — заполни секреты при необходимости."

dev-bootstrap: $(ENV_FILE) ## Поднять весь dev-стек (AC-1: цель ≤600 сек)
	$(COMPOSE) up -d --build --wait
	@echo "Стек поднят. Backend: http://localhost:8000/health · Frontend: http://localhost:3000"

up: $(ENV_FILE) ## Запустить сервисы (без пересборки)
	$(COMPOSE) up -d

down: ## Остановить сервисы и убрать тома
	$(COMPOSE) down -v

logs: ## Хвост логов всех сервисов
	$(COMPOSE) logs -f --tail=100

migrate: ## Применить миграции Alembic в backend-контейнере
	$(COMPOSE) exec backend alembic upgrade head

seed: ## Засеять тестовый тенант
	$(COMPOSE) exec backend python -m wizor.iam.seed

test: backend-test frontend-test ## Прогнать все тесты

backend-test: ## Backend unit-тесты (без integration; те — в CI)
	cd backend && . .venv/bin/activate && pytest -m "not integration"

frontend-test: ## Frontend vitest + coverage
	cd frontend && npm test

lint: backend-lint frontend-lint ## Линт + типы по всему репо

backend-lint: ## ruff + mypy
	cd backend && . .venv/bin/activate && ruff check . && ruff format --check . && mypy src

frontend-lint: ## eslint + tsc
	cd frontend && npm run lint && npm run typecheck

clean: ## Очистить кеши и артефакты
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache backend/coverage.xml
	rm -rf frontend/.next frontend/coverage
