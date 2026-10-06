# Repository test inventory

This inventory describes what the checked-in configuration intends to run and
what pytest can currently discover. “Active” means a test command or test
directory is referenced by current configuration or a workflow; it does not
mean the suite has passed recently. This is a static inventory, not a report of
the latest CI run.

## Discovery rules

The root [`pytest.ini`](../pytest.ini) sets `python_files = test_*.py`,
`python_classes = Test*`, and `python_functions = test_*`. It configures 46
test roots: `tests/`, 11 `services/*/tests/` directories, and all 34
`m0001`–`m0034` module test directories. Of those roots, only 18 Python files
currently match `test_*.py`:

- `tests/`: 16 files (listed below).
- `m0023-e3-matrix-lookup/m0023-tests/contract/test_hybrid_id_parity.py`
- `m0033-sk1-plugin-interface/m0033-tests/unit/test_plugin_system.py`

The service test roots contain timestamp-prefixed filenames (for example,
`services/signal-generator/tests/2099900186260118_test_signal_generator_plugin.py`).
These do not match the configured filename pattern and are not discovered by
pytest's directory-based collection. The same applies to timestamp-prefixed
files under `tests/contracts/` and `tests/legacy/`. Adding a directory to
`testpaths` does not override `python_files`.

## Active or registered test suites

| Suite | Location / entry point | Current status |
| --- | --- | --- |
| Root pytest suite | `tests/`; `pytest -q` | Registered in root configuration. The 16 matching test modules are listed below. Root CI workflows run this command; `pytest.ini` also applies coverage to `src` and `services` with an 85% minimum. |
| Module tests | `m0023-e3-matrix-lookup/m0023-tests/` and `m0033-sk1-plugin-interface/m0033-tests/` | One conventionally named test module in each is discoverable. The other 32 configured module test directories currently contain no Python test modules. |
| Service pytest suites | `services/{calendar-ingestor,data-ingestor,execution-engine,indicator-engine,reentry-engine,reentry-matrix-svc,reporter,risk-manager,signal-generator,telemetry-daemon,transport-router}/tests/` | Referenced by root configuration and service workflows, but the test filenames currently fail the `test_*.py` discovery rule. Rename them to match the rule or explicitly configure a matching pattern before relying on these jobs to execute their tests. |
| Contract tests | `tests/contracts/` | The contract workflow registers consumer, provider, scenario, property-based, coverage, and smoke jobs. Its consumer/provider commands expect `test_<name>_...py` paths that do not match the timestamp-prefixed files checked in here. Directory-based contract jobs also do not discover timestamp-prefixed tests with the root filename rule. Treat these jobs as not exercising the intended contract test cases until paths/names are reconciled. |
| GUI parity checks | `tests/test_gui_parity_optional.py`, `tests/test_gui_parity_extended_optional.py`, `tests/test_gui_parity_exit_optional.py` | The GUI Terminal workflow explicitly invokes these optional tests on Windows and Ubuntu; they are also root-discoverable. Their optional nature means a normal run may skip GUI-specific checks depending on environment. |
| Registry unit test | `tests/registries/test_registry_framework.py` | Active via `registry-validation.yml`, which uses `python -m unittest discover -s tests/registries -p 'test_*.py'`; also discoverable by root pytest. |
| Doc-ID validation | `doc_id_subsystem/validation/validate_doc_id_coverage.py` and `validate_doc_id_uniqueness.py` | Active CI validation scripts, not pytest tests. The workflow runs both and checks committed JSON baselines. |
| Re-entry library checks | `shared/reentry/tests/` in `1299900009260118_contracts-ci.yml` | Registered with `continue-on-error`; the directory is absent in this checkout, and the workflow itself notes tests may not exist yet. This job currently runs no repository test files. |

The root-level pytest command is used by `.github/workflows/ci.yml`,
`.github/workflows/1299900013260118_reentry_ci.yml`,
`.github/workflows/1299900009260118_contracts-ci.yml`, and
`.github/workflows/agentic-validators.yml`. The service-specific workflow
`.github/workflows/1299900017260118_services-ci.yml` matrices over nine
services; its `gui-gateway` entry currently has no `tests/` directory, and the
other listed service test files have non-matching timestamp prefixes. The
older `.github/workflows/1299900007260118_ci.yml` service matrix logs test
failures as non-blocking, so its green status does not guarantee those tests
passed.

### Workflow targets that do not match checked-in paths

These are registered CI commands, but their current targets are absent or
incompatible with the files in the checkout:

- `.github/workflows/1299900008260118_contract-tests.yml` expects consumer and
  provider filenames such as `test_<name>_contracts.py`; the checked-in files
  have timestamp prefixes and different separators. Its directory-based
  contract commands also do not match timestamp-prefixed modules.
- `.github/workflows/1299900007260118_ci.yml` directly invokes
  `P_tests/integration/test_p_folder_integration.py` and
  `P_tests/contracts/test_round_trip.py`. Neither path is tracked; `P_tests/`
  currently contains fixture data only.
- `.github/workflows/1299900018260118_smoke-e2e.yml` invokes
  `ci/smoke_test.py`, while the tracked smoke script is
  `ci/2099900009260118_smoke_test.py`.

## Root-discoverable test modules

These are the 16 matching modules under `tests/`:

- `tests/benchmarks/test_gdw_bench.py`
- `tests/doc_id_subsystem/test_doc_id_scanner.py`
- `tests/doc_id_subsystem/test_doc_id_validators.py`
- `tests/migration/test_p20_regeneration.py`
- `tests/registries/test_registry_framework.py`
- `tests/self_healing/test_fixers_order.py`
- `tests/self_healing/test_policy_budgets.py`
- `tests/self_healing/test_self_healing_registry.py`
- `tests/test_enterprise_modules.py`
- `tests/test_generator_update.py`
- `tests/test_gui_parity_exit_optional.py`
- `tests/test_gui_parity_extended_optional.py`
- `tests/test_gui_parity_optional.py`
- `tests/test_scenarios.py`
- `tests/test_validator_update.py`
- `tests/test_websocket_integration.py`

## Present but not included by root pytest discovery

These are tests or test-like modules in the repository that are outside the
configured test roots, or do not match the active filename pattern:

- **Service test files:** timestamp-prefixed files under the 11 service test
  roots above. Additional test-like files are outside those roots, including
  `services/common/test_service_template.py` and the tests under
  `services/desktop-ui/`.
- **Contract and legacy modules:** timestamp-prefixed test files under
  `tests/contracts/` and `tests/legacy/`. Contract workflow references to
  consumer/provider files also do not match the filenames currently checked
  in.
- **Other root test trees:** `tests/comms_test/python_comms_test.py` does not
  match `test_*.py`; files under `tests/integration/`, `tests/e2e/`,
  `tests/infrastructure/`, and `tests/signal_flow_testing/` are helpers or
  timestamp-prefixed modules rather than discoverable test modules.
- **Separate suites outside root `testpaths`:** `dag/test_dag_builder.py`,
  `dag/test_dag_utils.py`, `scenarios/test_trading_flow_scenarios.py`,
  `CLI_PY_GUI/gui_terminal/src/tests/unit/test_pty_backend.py`,
  `CLI_PY_GUI/gui_terminal/src/tests/unit/test_security_policy.py`, and
  `EAFIX_auth_docs/11_validation_quality_and_automation/test_all_modules.py`.
  These require an explicit path or a separate test configuration/command.
- **Manual/support material:** signal-flow simulators, testers, and the
  manual testing control panel under `tests/` are support tools, not
  conventionally named pytest modules. Workflow backups and files in
  `branch-archive/` are not active test configuration.

## Quick checks

- Run the root-configured suite and coverage gate: `pytest -q`
- Run registry tests as CI does: `python -m unittest discover -s tests/registries -p 'test_*.py'`
- Check collection without executing tests: `pytest --collect-only -q`

If a path appears in an inventory category but not in `pytest --collect-only`,
check the filename pattern, `testpaths`, explicit workflow paths, and whether
the suite has an independent runner. A workflow job existing in YAML alone is
not evidence that pytest collected tests or that the job is blocking.
