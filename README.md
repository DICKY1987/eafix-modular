# cli_multi_rapid_DEV

This repository serves as a proof‑of‑concept for a lightweight command‑line
interface (CLI) that can be extended into a multi‑agent development tool. The
initial scaffold demonstrates how to structure a Python project using a
``src`` layout, provides a simple CLI with subcommands, and sets up a basic
test harness.

The goal of this project is to establish repeatable development workflows and
quality gates. As future iterations introduce more complex functionality the
existing scaffolding can be built upon without reinventing the wheel.

## Quick start

You can run the CLI directly with the Python interpreter without any
installation steps. The examples below assume you are executing commands in
the repository root.

```bash
# Print a friendly greeting
python -m cli_multi_rapid.cli greet Alice

# Compute the sum of two integers
python -m cli_multi_rapid.cli sum 3 5
```

If you prefer to install the package into your current environment, you can
use a local editable install via `pip`. This step is optional and not
required to run the examples above:

```bash
pip install -e .
cli-multi-rapid greet Alice
```

The editable install will register a console script entry point named
`cli-multi-rapid`. It simply forwards to the same functionality exposed in
``cli_multi_rapid.cli``.

## Development guide

Development workflows emphasise high code quality, reproducibility and clear
communication. The repository includes a commit message template
(``.gitmessage.txt``) and a sample CI workflow (``.github/workflows/ci.yml``)
that installs common development tools such as ``pre-commit``, ``ruff`` and
``pytest``. Although these tools may not be available in all environments,
they are preconfigured so that continuous integration (CI) pipelines can
enforce formatting, linting, static type checking and unit test execution.

To run the test suite locally using the built‑in Python ``unittest`` runner:

```bash
python -m unittest discover -s tests -v
```

Alternatively, if you have ``pytest`` available, you can benefit from its
more expressive output and coverage reporting:

```bash
pytest -q --cov=src --cov-report=term-missing --cov-fail-under=80
```

## Repository structure

| Path                       | Purpose                                                 |
|---------------------------|---------------------------------------------------------|
| ``src/cli_multi_rapid``    | Source code for the CLI implementation.                 |
| ``tests``                 | Unit tests written using ``unittest``.                  |
| ``.ai``                   | Agent orchestration scripts and job definitions.         |
| ``.github/workflows``     | GitHub Actions workflows for automated CI.               |
| ``framework_readme.md``   | Detailed documentation for the broader free‑tier agentic framework. |
| ``*.md/.txt/.png/.pdf``   | Specifications, diagrams and supporting documentation.    |

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to
discuss improvements, report bugs, or suggest new features. Please follow the
commit message guidelines defined in ``.gitmessage.txt`` and aim to include
tests for any new functionality.