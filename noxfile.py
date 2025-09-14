"""
Nox configuration for testing and development
"""

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.11", "3.12"]

@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite"""
    session.install("-r", "requirements.txt")
    session.install("pytest", "pytest-asyncio", "pytest-cov", "pytest-mock")
    session.run(
        "pytest",
        "--cov=agentic_framework_v3",
        "--cov-report=term-missing",
        "--cov-report=html",
        "tests/"
    )


@nox.session(python=PYTHON_VERSIONS)
def gdw_tests(session):
    """Run GDW schema validation and lightweight tests (no heavy deps)."""
    # Avoid installing full requirements to keep Windows compatibility and speed
    session.install("pytest", "jsonschema", "pyyaml", "requests")
    # Validate example spec against schema
    session.run(
        "python",
        "-m",
        "schema.validators.python.gdw_validator",
        "gdw/git.commit_push.main/v1.0.0/spec.json",
    )
    # Run any GDW-tagged tests if present
    session.run("pytest", "-q", "-k", "gdw or GDW", external=False)
    # Optional performance/chaos tests
    if session.env.get("RUN_GDW_OPTIONAL") == "1":
        session.run("pytest", "-q", "tests/test_gdw_performance_optional.py", external=False)

@nox.session
def integration_tests(session):
    """Run integration tests (cost-controlled)"""
    session.install("-r", "requirements.txt")
    session.install("pytest", "pytest-asyncio")
    
    # Only run tests marked as 'not expensive'
    session.run(
        "pytest", 
        "tests/integration/", 
        "-m", "not expensive",
        "--tb=short"
    )

@nox.session
def lint(session):
    """Run linting and code quality checks"""
    session.install("flake8", "black", "isort", "mypy")
    session.install("-r", "requirements.txt")
    
    # Format code
    session.run("black", ".")
    session.run("isort", ".")
    
    # Lint code
    session.run("flake8", "agentic_framework_v3.py")
    session.run("mypy", "agentic_framework_v3.py", "--ignore-missing-imports")

@nox.session
def security(session):
    """Run security checks"""
    session.install("bandit", "safety")
    session.run("bandit", "-r", ".", "-x", "tests/")
    session.run("safety", "check")

@nox.session
def docs(session):
    """Build documentation"""
    session.install("sphinx", "sphinx-rtd-theme")
    session.install("-r", "requirements.txt")
    session.cd("docs")
    session.run("sphinx-build", "-b", "html", ".", "_build/html")

@nox.session
def dev_setup(session):
    """Set up development environment"""
    session.install("-r", "requirements.txt")
    session.install("pre-commit")
    session.run("pre-commit", "install")
    
    # Create example .env file
    session.run("cp", ".env.example", ".env", external=True)
    
    print("✅ Development environment set up!")
    print("📝 Edit .env file with your API keys")
    print("🚀 Run: python agentic_framework_v3.py --help")

@nox.session
def benchmark(session):
    """Run performance benchmarks"""
    session.install("-r", "requirements.txt")
    session.install("pytest-benchmark")
    session.run(
        "pytest",
        "tests/benchmarks/",
        "--benchmark-only",
        "--benchmark-sort=mean"
    )
