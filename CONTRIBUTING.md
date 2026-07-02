# Contributing

Thanks for your interest in improving `cli_multi_rapid_DEV`!

## Quick start

1. Fork and clone the repo.
2. Create a virtual environment and install dev deps:
   - `pip install -e .`
   - `pip install -r requirements.txt` (optional extras for local tooling)
   - `pip install pre-commit`
   - `pre-commit install`
3. Run tests: `python -m unittest -v` or `pytest -q`.

## Development standards

- Keep changes focused and include tests for new behavior.
- Run formatting, linting, type checks, and tests locally before pushing.
- Ensure CI passes; coverage is gated at 80%.

## Pull requests

- Describe the problem and solution clearly, referencing issues if applicable.
- Add user-facing notes to `README.md` when behavior changes.
- For security-sensitive changes, coordinate privately per `SECURITY.md`.

