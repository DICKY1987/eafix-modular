# Contributing to EAFIX Trading System

Thank you for your interest in contributing to the EAFIX Trading System! This document outlines the process for contributing to this project.

## Code of Conduct

Please be respectful and professional in all interactions. This is a trading system that affects real financial positions, so attention to detail is critical.

## Development Setup

1. **Prerequisites**:
   - Docker and Docker Compose
   - Python 3.11+
   - Poetry for dependency management

2. **Initial Setup**:
   ```bash
   git clone https://github.com/DICKY1987/eafix-modular.git
   cd eafix-modular
   poetry install
   poetry run pre-commit install
   ```

3. **Start Development Environment**:
   ```bash
   # Start all services
   ./tasks.bat up
   # OR
   docker compose -f deploy/compose/docker-compose.yml up
   ```

## Contributing Process

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:
   - Follow existing code patterns and conventions
   - Add tests for new functionality
   - Update documentation as needed
   - Ensure all services remain compatible

3. **Quality Checks**:
   ```bash
   # Format code
   poetry run black services/
   poetry run isort services/

   # Run linting
   poetry run flake8 services/
   poetry run mypy services/*/src

   # Run tests
   poetry run pytest
   
   # Validate contracts
   make contracts-validate-full
   ```

4. **Submit Pull Request**:
   - Create PR against the main branch
   - Provide clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## Contract System Guidelines

This system uses a **centralized contract registry**. When making changes:

1. **Schema Changes**: Update schemas in `contracts/schemas/json/` first
2. **Model Generation**: Regenerate Pydantic models using the contract tooling
3. **Validation**: Run `make contracts-validate-full` to ensure compatibility
4. **Versioning**: Follow semantic versioning for breaking changes

## Service Development Guidelines

When working on services:

1. **Structure**: Follow the established service structure pattern
2. **Configuration**: Use Pydantic Settings with environment variable support
3. **Health Checks**: Implement `/healthz` and `/readyz` endpoints
4. **Metrics**: Expose Prometheus metrics at `/metrics`
5. **Logging**: Use structured JSON logging with correlation IDs
6. **Error Handling**: Follow defensive posture - fail closed on integrity errors

## Testing Requirements

All contributions must include appropriate tests:

- **Unit Tests**: For business logic
- **Integration Tests**: For service interactions
- **Contract Tests**: For schema validation
- **End-to-End Tests**: For complete workflows

## Performance Considerations

This is a real-time trading system. Consider:

- **Latency**: Keep p95 latencies under established SLOs
- **Memory Usage**: Monitor memory consumption in long-running services
- **CPU Usage**: Profile CPU-intensive indicator calculations
- **Network**: Minimize unnecessary API calls between services

## Documentation

Update documentation for:
- API changes in service README files
- Architecture changes in main README
- New patterns in CLAUDE.md
- Operational procedures in runbooks

## Security Guidelines

- **No Secrets**: Never commit API keys, passwords, or tokens
- **Environment Variables**: Use env vars for all configuration
- **Input Validation**: Validate all external inputs
- **Error Information**: Don't leak sensitive data in error messages

## Questions and Support

For questions about:
- **Architecture**: Check `docs/modernization/` and ADRs
- **Contracts**: See `contracts/` documentation
- **Service Issues**: Check individual service READMs
- **Operations**: Consult `docs/runbooks/`

Thank you for contributing to the EAFIX Trading System!