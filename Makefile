SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: help up down logs build migrate revision seed test lint fmt typecheck clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all services (db + redis + minio + backend + frontend + worker)
	$(COMPOSE) up -d --build

down: ## Stop all services
	$(COMPOSE) down

logs: ## Tail logs from all services
	$(COMPOSE) logs -f --tail=100

build: ## Rebuild service images
	$(COMPOSE) build

migrate: ## Apply database migrations
	$(COMPOSE) exec backend alembic upgrade head

revision: ## Create a new alembic revision (usage: make revision m="message")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(m)"

seed: ## Load demo data
	$(COMPOSE) exec backend python -m app.scripts.seed

test: ## Run backend tests
	$(COMPOSE) exec backend pytest -q

lint: ## Run linters
	$(COMPOSE) exec backend ruff check app tests
	cd frontend && npm run lint

fmt: ## Format code
	$(COMPOSE) exec backend ruff format app tests
	cd frontend && npm run format

typecheck: ## Static type checks
	$(COMPOSE) exec backend mypy app
	cd frontend && npm run typecheck

clean: ## Remove containers + volumes (destructive)
	$(COMPOSE) down -v
