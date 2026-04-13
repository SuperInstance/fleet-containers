# ============================================================
# FLUX Fleet — Build, Run, Test, Clean targets
# ============================================================

.PHONY: help build build-all build-base build-runtime build-agent \
        up down logs ps test test-unit test-integration test-all \
        clean clean-images clean-volumes clean-all \
        shell run-agent run-oracle health inspect network

.DEFAULT_GOAL := help

# --- Variables ---
COMPOSE := docker compose
IMAGE_PREFIX := fleet
TAG := latest
GITHUB_TOKEN ?= ""

# --- Help ---
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Build targets ---
build-base: ## Build base image
	docker build -f Dockerfile.base -t $(IMAGE_PREFIX)/base:$(TAG) .

build-runtime: ## Build FLUX runtime image
	docker build -f Dockerfile.flux-runtime -t $(IMAGE_PREFIX)/runtime:$(TAG) .

build-agent: ## Build agent image
	docker build -f Dockerfile.agent -t $(IMAGE_PREFIX)/agent:$(TAG) .

build-all: build-base build-runtime build-agent ## Build all images

build: build-all ## Alias for build-all

# --- Run targets ---
up: ## Start the fleet (all services)
	GITHUB_TOKEN=$(GITHUB_TOKEN) $(COMPOSE) up -d

down: ## Stop the fleet
	$(COMPOSE) down

restart: down up ## Restart the fleet

ps: ## Show running services
	$(COMPOSE) ps

logs: ## Show fleet logs
	$(COMPOSE) logs -f

logs-agent: ## Show agent logs
	$(COMPOSE) logs -f agent

# --- Test targets ---
test: ## Run all tests
	python3 -m pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	python3 -m pytest tests/ -v -m unit --tb=short

test-integration: ## Run integration tests only
	python3 -m pytest tests/ -v -m integration --tb=short

test-verbose: ## Run tests with full output
	python3 -m pytest tests/ -v --tb=long -s

# --- Clean targets ---
clean: ## Remove stopped containers and dangling images
	$(COMPOSE) down --remove-orphans 2>/dev/null || true
	docker image prune -f

clean-images: ## Remove all fleet images
	docker rmi $$(docker images -q $(IMAGE_PREFIX)/*:$(TAG)) 2>/dev/null || true

clean-volumes: ## Remove fleet volumes
	docker volume rm fleet-data fleet-logs fleet-secrets 2>/dev/null || true
	$(COMPOSE) down -v 2>/dev/null || true

clean-all: clean clean-images clean-volumes ## Clean everything

# --- Utility targets ---
shell: ## Shell into agent container
	$(COMPOSE) exec agent /bin/bash

run-agent: ## Run a one-off agent container
	docker run --rm -it \
		-e AGENT_NAME=$(AGENT_NAME)-ephemeral \
		-e AGENT_ROLE=greenhorn \
		-e GITHUB_TOKEN=$(GITHUB_TOKEN) \
		--network fleet-network \
		$(IMAGE_PREFIX)/agent:$(TAG) shell

run-oracle: ## Run a one-off oracle container
	docker run --rm -it \
		-e AGENT_NAME=oracle-ephemeral \
		-e AGENT_ROLE=oracle \
		-e GITHUB_TOKEN=$(GITHUB_TOKEN) \
		--network fleet-network \
		$(IMAGE_PREFIX)/agent:$(TAG) shell

health: ## Check health of all containers
	@for c in $$(docker ps --filter "name=fleet-" -q); do \
		echo "--- $$c ---"; \
		docker inspect --format='{{.State.Health.Status}}' $$c 2>/dev/null || echo "no healthcheck"; \
	done

inspect: ## Inspect fleet network
	docker network inspect fleet-network

network: ## Create fleet network
	docker network create --driver bridge --subnet=172.28.0.0/16 fleet-network 2>/dev/null || echo "Network exists"

# --- Lint targets ---
lint-dockerfiles: ## Validate Dockerfile syntax
	@for f in Dockerfile.*; do \
		echo "Checking $$f..."; \
		docker run --rm -i hadolint/hadolint < $$f 2>/dev/null || true; \
	done

lint-compose: ## Validate docker-compose.yml
	$(COMPOSE) config --quiet
	@echo "docker-compose.yml is valid"

lint: lint-dockerfiles lint-compose ## Run all linters
