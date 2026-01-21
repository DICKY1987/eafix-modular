# doc_id: DOC-AUTOOPS-002
"""CLI entry point for RepoAutoOps."""

import asyncio
from pathlib import Path

import click
import structlog

from repo_autoops import __version__
from repo_autoops.config import Config
from repo_autoops.orchestrator import Orchestrator
from repo_autoops.queue import EventQueue

__doc_id__ = "DOC-AUTOOPS-002"

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
)

logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """RepoAutoOps - Automated Git operations with file watching."""
    pass


@cli.command()
@click.option("--config", type=click.Path(exists=True), default="config/repo_autoops.yaml", help="Config file path")
@click.option("--dry-run/--execute", default=True, help="Dry-run mode (default: dry-run)")
def watch(config: str, dry_run: bool) -> None:
    """Start file watcher and process events."""
    logger.info("starting_repo_autoops", config=config, dry_run=dry_run)

    cfg = Config.load_from_file(Path(config))
    orchestrator = Orchestrator(cfg, dry_run=dry_run)

    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        logger.info("shutting_down")
        orchestrator.stop()


@cli.command()
@click.option("--db", type=click.Path(), default=".repo_autoops_queue.db", help="Queue database path")
def status(db: str) -> None:
    """Show queue status."""
    queue = EventQueue(Path(db))
    pending = queue.get_pending_count()
    click.echo(f"Pending work items: {pending}")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--event-type", default="modified", help="Event type")
def enqueue(path: str, event_type: str) -> None:
    """Manually enqueue a file for processing."""
    queue = EventQueue(Path(".repo_autoops_queue.db"))
    work_item_id = queue.enqueue(Path(path), event_type)
    click.echo(f"Enqueued: {work_item_id}")


if __name__ == "__main__":
    cli()
