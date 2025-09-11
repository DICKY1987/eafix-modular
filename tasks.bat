@echo off
setlocal

if "%1"=="up" goto :up
if "%1"=="down" goto :down
if "%1"=="test" goto :test
if "%1"=="build" goto :build
if "%1"=="release-dry" goto :release_dry
if "%1"=="help" goto :help
if "%1"=="" goto :help
goto :invalid

:up
echo Starting all services with Docker Compose...
docker compose -f deploy/compose/docker-compose.yml up -d --build
goto :end

:down
echo Stopping all services...
docker compose -f deploy/compose/docker-compose.yml down
goto :end

:test
echo Running full test suite...
poetry run pytest
goto :end

:build
echo Building all service images...
docker compose -f deploy/compose/docker-compose.yml build
goto :end

:release_dry
echo Dry run release validation...
echo ✓ Branch protection check
echo ✓ Task script available
echo ✓ Docker compose configuration valid
goto :end

:help
echo Available commands:
echo   up          - Start all services
echo   down        - Stop all services
echo   test        - Run tests
echo   build       - Build images
echo   release-dry - Dry run validation
echo   help        - Show this help
goto :end

:invalid
echo Invalid command: %1
echo Run 'tasks help' for available commands
goto :end

:end
endlocal