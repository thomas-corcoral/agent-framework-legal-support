.PHONY: help install dev-install lint format test test-cov clean docker-build docker-run pre-commit

# Default target
help:
	@echo "Agent Framework Legal Support - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install        Install production dependencies"
	@echo "  dev-install    Install development dependencies"
	@echo "  pre-commit     Install pre-commit hooks"
	@echo ""
	@echo "Development:"
	@echo "  lint           Run linting (ruff)"
	@echo "  format         Format code (ruff format)"
	@echo "  typecheck      Run type checking (mypy)"
	@echo "  test           Run tests"
	@echo "  test-cov       Run tests with coverage"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run Docker container"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          Remove build artifacts"
	@echo "  update         Update dependencies"

# Installation
install:
	uv sync --no-dev

dev-install:
	uv sync
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

pre-commit:
	uv run pre-commit install
	uv run pre-commit install --hook-type commit-msg

# Development
lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ --cov=src/legal_support --cov-report=html --cov-report=term-missing

# Docker
docker-build:
	docker build -t legal-support:latest -f docker/Dockerfile .

docker-run:
	docker run --rm -it \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/output:/app/output \
		--env-file .env \
		legal-support:latest

docker-compose-up:
	docker compose -f docker/docker-compose.yaml up -d

docker-compose-down:
	docker compose -f docker/docker-compose.yaml down

# Maintenance
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

update:
	uv lock --upgrade
	uv sync

# CI/CD helpers
ci-lint:
	uv run ruff check src tests --output-format=github

ci-test:
	uv run pytest tests/ --cov=src/legal_support --cov-report=xml --junitxml=junit.xml
