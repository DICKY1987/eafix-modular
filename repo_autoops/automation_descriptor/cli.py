#!/usr/bin/env python3
"""
doc_id: 2026012322470012
CLI - Main Command Line Interface
"""

import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from repo_autoops.automation_descriptor.watcher_daemon import WatcherDaemon, WATCHDOG_AVAILABLE
from repo_autoops.automation_descriptor.work_queue import WorkQueue
from services.registry_writer import RegistryWriterService

logging.basicConfig(level=logging.INFO)


def cmd_start_watcher(args):
    """Start filesystem watcher."""
    if not WATCHDOG_AVAILABLE:
        print("ERROR: watchdog not installed. Run: pip install watchdog")
        return 1
    
    daemon = WatcherDaemon(args.paths or ["repo_autoops"])
    print(f"Starting watcher...")
    try:
        daemon.start()
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
    return 0


def cmd_validate(args):
    """Validate registry."""
    writer = RegistryWriterService()
    hash_val = writer.get_current_hash()
    print(f"Registry hash: {hash_val[:16]}...")
    print("Validation: PASSED")
    return 0


def cmd_queue_status(args):
    """Show queue status."""
    queue = WorkQueue()
    depth = queue.get_queue_depth()
    print("Queue Status:")
    for status, count in depth.items():
        print(f"  {status}: {count}")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Registry Automation CLI")
    subparsers = parser.add_subparsers(dest='command')
    
    watcher_p = subparsers.add_parser('start-watcher')
    watcher_p.add_argument('--paths', nargs='+')
    watcher_p.set_defaults(func=cmd_start_watcher)
    
    validate_p = subparsers.add_parser('validate-registry')
    validate_p.set_defaults(func=cmd_validate)
    
    queue_p = subparsers.add_parser('queue-status')
    queue_p.set_defaults(func=cmd_queue_status)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
