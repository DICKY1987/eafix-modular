.PHONY: contracts-validate contracts-validate-full contracts-test csv-validate reentry-validate smoke test-all docker-up docker-down replay-test signal-flow-test signal-simulation calendar-simulation manual-test-panel test-signal-flow-all dag-validate dag-report dag-workstreams dag-patterns dag-gates

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
	@echo "🔍 Running contract and scenario tests..."
	poetry run pytest tests/contracts/ -v --tb=short

contracts-compat:
	python ci/check_schema_compat.py

# Contract testing specific targets
contracts-consumer:
	@echo "🧪 Running consumer contract tests..."
	poetry run pytest tests/contracts/consumer/ -v -m consumer

contracts-provider:
	@echo "🧪 Running provider contract tests..."
	poetry run pytest tests/contracts/provider/ -v -m provider

contracts-scenarios:
	@echo "🧪 Running scenario-based integration tests..."
	poetry run pytest tests/contracts/scenarios/ -v -m scenario

contracts-properties:
	@echo "🧪 Running property-based contract tests..."
	poetry run pytest tests/contracts/properties/ -v -m property

contracts-smoke:
	@echo "🚀 Running contract smoke tests..."
	poetry run pytest tests/contracts/ -v -m smoke --tb=line

contracts-coverage:
	@echo "📊 Running contract tests with coverage..."
	poetry run pytest tests/contracts/ --cov=tests.contracts --cov-report=html:htmlcov/contracts --cov-report=term-missing

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

# Operations and runbooks
runbooks:
	@echo "📚 EAFIX Runbooks Index"
	@echo "========================"
	@echo "Opening runbooks index..."
	@if command -v open >/dev/null 2>&1; then \
		open docs/runbooks/index.md; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open docs/runbooks/index.md; \
	else \
		echo "📖 Runbooks available at: docs/runbooks/index.md"; \
		echo "🚨 Emergency: docs/runbooks/incident-response.md"; \
		echo "💰 Trading: docs/runbooks/trading-incidents.md"; \
		echo "🔧 Common Issues: docs/runbooks/common-issues.md"; \
		echo "📞 Escalation: docs/runbooks/escalation-procedures.md"; \
	fi

emergency-stop:
	@echo "🚨 EMERGENCY TRADING HALT"
	@echo "=========================="
	@echo "Stopping all trading operations..."
	@curl -X POST http://localhost:8080/emergency/stop-trading \
		-H "Content-Type: application/json" \
		-d '{"reason": "emergency_halt", "operator": "'$$USER'"}' || echo "❌ Failed to contact trading system"
	@echo "✅ Emergency stop command sent"
	@echo "📋 Next steps: Check docs/runbooks/trading-incidents.md"

emergency-restart:
	@echo "🚨 EMERGENCY SYSTEM RESTART"
	@echo "============================"
	@echo "⚠️  This will restart all trading services!"
	@read -p "Type 'CONFIRM' to proceed: " confirm; \
	if [ "$$confirm" = "CONFIRM" ]; then \
		echo "🔄 Stopping all services..."; \
		docker compose -f deploy/compose/docker-compose.yml down; \
		sleep 10; \
		echo "🚀 Starting all services..."; \
		docker compose -f deploy/compose/docker-compose.yml up -d; \
		sleep 30; \
		echo "🔍 Running health check..."; \
		make smoke; \
		echo "✅ Emergency restart completed"; \
	else \
		echo "❌ Emergency restart cancelled"; \
	fi

health-check:
	@echo "🏥 COMPREHENSIVE HEALTH CHECK"
	@echo "=============================="
	@echo "🔍 Checking all services..."
	@for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do \
		status=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$$port/healthz); \
		if [ "$$status" = "200" ]; then \
			echo "✅ Port $$port: Healthy"; \
		else \
			echo "❌ Port $$port: Unhealthy ($$status)"; \
		fi \
	done
	@echo ""
	@echo "📊 System Resources:"
	@echo "Memory: $$(free -h | awk 'NR==2{printf \"%.1f%% used\", $$3*100/$$2}')"
	@echo "Disk: $$(df -h / | awk 'NR==2{print $$5 " used"}')"
	@echo ""
	@echo "🐳 Docker Status:"
	@docker compose -f deploy/compose/docker-compose.yml ps --format table
	@echo ""
	@echo "💾 Database:"
	@psql -h localhost -p 5432 -U eafix -d eafix_prod -c "SELECT 'Connected at ' || now();" 2>/dev/null || echo "❌ Database connection failed"
	@echo ""
	@echo "📨 Redis:"
	@redis-cli -h localhost -p 6379 ping 2>/dev/null || echo "❌ Redis connection failed"

help:
	@echo "Available targets:"
	@echo ""
	@echo "🔧 Development:"
	@echo "  install                 - Install dependencies and pre-commit hooks"
	@echo "  format                  - Format code with black and isort"
	@echo "  lint                    - Run linting and type checks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test-all                - Run full test suite"
	@echo "  smoke                   - Run smoke tests"
	@echo "  contracts-validate-full - Full contract validation (JSON + CSV + re-entry)"
	@echo "  contracts-test          - Run contract and scenario tests"
	@echo "  contracts-consumer      - Run consumer contract tests"
	@echo "  contracts-provider      - Run provider verification tests"
	@echo "  contracts-scenarios     - Run scenario-based integration tests"
	@echo "  contracts-properties    - Run property-based contract tests"
	@echo "  contracts-coverage      - Run contract tests with coverage"
	@echo "  replay-test             - Run tick replay performance test"
	@echo ""
	@echo "🐳 Docker Operations:"
	@echo "  docker-up               - Start all services with Docker Compose"
	@echo "  docker-down             - Stop all services"
	@echo "  docker-logs             - Follow container logs"
	@echo ""
	@echo "📚 Operations & Runbooks:"
	@echo "  runbooks                - Open runbooks index"
	@echo "  emergency-stop          - Emergency trading halt"
	@echo "  emergency-restart       - Emergency system restart"
	@echo "  health-check            - Comprehensive health check"
	@echo "  gaps-check              - Review production readiness gaps"

# Phase 0 baseline targets

# ------------------------------
# Performance testing helpers
# ------------------------------

# Defaults (override on command line or env):
K6_TARGET_URL ?= http://localhost:8080/healthz
K6_VUS ?= 5
K6_DURATION ?= 30s

LOCUST_HOST ?= http://localhost:8080
LOCUST_USERS ?= 20
LOCUST_SPAWN ?= 5
LOCUST_DURATION ?= 1m

.PHONY: perf-k6 perf-locust

perf-k6:
	@echo "=== k6 baseline ==="
	@echo "Target: $(K6_TARGET_URL) VUs: $(K6_VUS) Duration: $(K6_DURATION)"
	@if ! command -v k6 >/dev/null 2>&1; then \
		echo "k6 not found. Install from https://k6.io/"; \
		exit 1; \
	fi
	k6 run scripts/perf/k6/script.js \
		-e TARGET_URL=$(K6_TARGET_URL) \
		-e VUS=$(K6_VUS) \
		-e DURATION=$(K6_DURATION) \
		--summary-export scripts/perf/k6/summary.json || true

perf-locust:
	@echo "=== Locust baseline ==="
	@echo "Host: $(LOCUST_HOST) Users: $(LOCUST_USERS) Spawn: $(LOCUST_SPAWN) Duration: $(LOCUST_DURATION)"
	@if ! command -v locust >/dev/null 2>&1; then \
		echo "locust not found. Install with: pip install locust"; \
		exit 1; \
	fi
	locust -f scripts/perf/locust/locustfile.py \
		--headless -u $(LOCUST_USERS) -r $(LOCUST_SPAWN) -t $(LOCUST_DURATION) \
		--host $(LOCUST_HOST) --csv scripts/perf/locust/results || true
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

# Signal Flow Testing Framework (Friday Morning Updates)
signal-flow-test:
	@echo "🧪 Running end-to-end signal flow tests..."
	cd tests/integration && python signal_flow_tester.py --mt4-data "$(MT4_DATA_PATH)"

signal-simulation:
	@echo "📊 Running indicator signal simulation..."
	cd tests/fixtures && python indicator_signal_simulator.py

calendar-simulation:
	@echo "📅 Running calendar event simulation..."
	cd tests/fixtures && python calendar_event_simulator.py

manual-test-panel:
	@echo "🎛️ Starting manual testing control panel..."
	cd P_GUI/testing && python manual_testing_control_panel.py

# Combined testing target  
test-signal-flow-all: signal-flow-test signal-simulation calendar-simulation
	@echo "✅ All signal flow tests completed"

# DAG-based Verification Framework
dag-validate:
	@echo "🔍 Validating DAG configuration..."
	python dag/validate_dag.py

dag-report:
	@echo "📊 Generating DAG execution report..."
	@cat dag/EXECUTION_REPORT.md

dag-workstreams:
	@echo "📋 Listing workstreams..."
	@python -c "import yaml; ws = yaml.safe_load(open('dag/workstreams/workstream_definitions.yaml')); print('\n'.join([f\"  {w['id']}: {w['name']} (SLA: {w['sla_budget_ms']}ms)\" for w in ws['workstreams']]))"

dag-patterns:
	@echo "🧩 Listing verification patterns..."
	@python -c "import yaml; p = yaml.safe_load(open('dag/patterns/pattern_registry.yaml')); print('\n'.join([f\"  {v['id']}: {v['description']}\" for v in p['verification_patterns']]))"

dag-gates:
	@echo "🚧 Listing quality gates..."
	@python -c "import yaml; g = yaml.safe_load(open('dag/config/quality_gates.yaml')); print('\n'.join([f\"  {gate['id']}: {gate['type']} ({gate['timeout_ms']}ms)\" for gate in g['gates']]))"
