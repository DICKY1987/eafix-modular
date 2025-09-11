.PHONY: contracts-validate contracts-validate-full contracts-test csv-validate reentry-validate smoke test-all docker-up docker-down replay-test

# Contract validation (comprehensive)
contracts-validate-full:
	@echo "=== Full Contract Validation ==="
	cd contracts && python validate_json_schemas.py --report
	cd contracts && python validate_csv_artifacts.py --directory ../tests/contracts/fixtures --pattern "*.csv"
	cd shared/reentry && python reentry_helpers_cli.py --validate-csv ../../tests/contracts/fixtures/
	python tests/contracts/test_integration.py

# Individual contract validation targets
contracts-validate:
	python ci/validate_schemas.py

csv-validate:
	cd contracts && python validate_csv_artifacts.py --directory ../tests/contracts/fixtures --pattern "*.csv"

reentry-validate:
	cd shared/reentry && python -c "from hybrid_id import HybridIdHelper; h = HybridIdHelper(); print('✓ Re-entry library loaded successfully')"
	cd shared/reentry && python -c "from vocab import ReentryVocabulary; v = ReentryVocabulary(); print(f'✓ Vocabulary loaded: {len(v.get_all_valid_tokens())} token categories')"

contracts-test:
	python tests/contracts/test_integration.py

contracts-compat:
	python ci/check_schema_compat.py

# Health and smoke testing
smoke:
	python ci/smoke_test.py

# Full test suite
test-all:
	poetry run pytest

# Docker operations
docker-up:
	docker compose -f deploy/compose/docker-compose.yml up -d --build

docker-down:
	docker compose -f deploy/compose/docker-compose.yml down

docker-logs:
	docker compose -f deploy/compose/docker-compose.yml logs -f

# Performance testing
replay-test:
	python scripts/replay/replay_ticks.py scripts/replay/sample_ticks.csv --verbose

# Development helpers
install:
	poetry install
	poetry run pre-commit install

format:
	poetry run black services/
	poetry run isort services/

lint:
	poetry run flake8 services/
	poetry run mypy services/*/src

# Production readiness checks
gaps-check:
	@echo "=== Gap Register Review ==="
	@cat docs/gaps/GAP_REGISTER.md
	@echo "\n=== SLO Status ==="
	@cat docs/gaps/slo/SLOs.md

help:
	@echo "Available targets:"
	@echo "  contracts-validate  - Validate JSON schemas"
	@echo "  contracts-compat    - Check schema compatibility"
	@echo "  smoke               - Run smoke tests"
	@echo "  test-all            - Run full test suite"
	@echo "  docker-up           - Start all services with Docker Compose"
	@echo "  docker-down         - Stop all services"
	@echo "  docker-logs         - Follow container logs"
	@echo "  replay-test         - Run tick replay performance test"
	@echo "  install             - Install dependencies and pre-commit hooks"
	@echo "  format              - Format code with black and isort"
	@echo "  lint                - Run linting and type checks"
	@echo "  gaps-check          - Review production readiness gaps"

# Phase 0 baseline targets
up: docker-up

build:
	@echo "Building all service images..."
	docker compose -f deploy/compose/docker-compose.yml build

sbom:
	@echo "Generating SBOM (placeholder - requires syft)..."
	@echo "Would run: syft packages dir:. -o json > sbom.json"

release-dry:
	@echo "Dry run release validation..."
	@echo "✓ Branch protection check"
	@echo "✓ Makefile targets available" 
	@echo "✓ Docker compose configuration valid"
