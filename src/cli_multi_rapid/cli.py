"""
Command-line interface for the ``cli_multi_rapid`` package.

This module exposes a :func:`main` function which is intended to be used as
the entry point when this package is installed as a console script. It
provides two simple subcommands:

* ``greet`` – prints a friendly greeting to the supplied name.
* ``sum`` – computes the sum of two integers.

These functions are intentionally simple so that they can be easily tested
without additional dependencies beyond the Python standard library. They
demonstrate argument parsing, error handling and unit testability. Future
iterations of this project can replace or extend these commands with more
complex behaviour as the multi-agent CLI evolves.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List, Optional, Any, Dict
import os
import json


def greet(name: str) -> str:
    """Return a greeting for the given ``name``.

    This function encapsulates the logic for generating a greeting. It
    returns the greeting rather than printing it so that it can be easily
    tested in isolation. The :func:`main` function handles printing to
    standard output.

    Parameters
    ----------
    name:
        The name of the person to greet. Leading and trailing whitespace
        will be stripped.

    Returns
    -------
    str
        A greeting message.
    """
    cleaned = name.strip()
    return f"Hello, {cleaned}!"


def sum_numbers(a: int, b: int) -> int:
    """Return the sum of two integers.

    Parameters
    ----------
    a:
        First integer operand.
    b:
        Second integer operand.

    Returns
    -------
    int
        The sum ``a + b``.
    """
    return a + b


@dataclass
class CLIArgs:
    """Dataclass capturing parsed CLI arguments for testability."""

    command: str
    name: Optional[str] = None
    a: Optional[int] = None
    b: Optional[int] = None
    # Optional fields used by specific subcommands
    file: Optional[str] = None
    show: Optional[str] = None


def parse_args(argv: Optional[List[str]] = None) -> CLIArgs:
    """Parse command line arguments and return a :class:`CLIArgs` instance.

    This function is factored out for ease of testing. Passing a list of
    strings as ``argv`` allows unit tests to simulate command line input.

    Parameters
    ----------
    argv:
        A list of argument strings. If ``None``, defaults to ``sys.argv[1:]``.

    Returns
    -------
    CLIArgs
        The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="cli-multi-rapid",
        description="Simple multi-rapid CLI demonstrating basic subcommands.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # greet subcommand
    greet_parser = subparsers.add_parser("greet", help="Print a greeting")
    greet_parser.add_argument(
        "name",
        type=str,
        help="Name of the person to greet",
    )

    # sum subcommand
    sum_parser = subparsers.add_parser("sum", help="Compute the sum of two integers")
    sum_parser.add_argument(
        "a",
        type=int,
        help="First integer operand",
    )
    sum_parser.add_argument(
        "b",
        type=int,
        help="Second integer operand",
    )

    # run-job subcommand
    run_job_parser = subparsers.add_parser(
        "run-job", help="List and inspect jobs from tasks.json or agent_jobs.yaml"
    )
    run_job_parser.add_argument(
        "--file",
        dest="file",
        type=str,
        help="Path to a manifest file (tasks.json or agent_jobs.yaml)",
    )
    run_job_parser.add_argument(
        "--name",
        dest="name",
        type=str,
        help="Filter by job label/name (substring match)",
    )
    run_job_parser.add_argument(
        "--show",
        dest="show",
        choices=["steps"],
        help="Show detailed steps/fields for each job",
    )

    parsed = parser.parse_args(argv)
    return CLIArgs(
        command=parsed.command,
        name=getattr(parsed, "name", None),
        a=getattr(parsed, "a", None),
        b=getattr(parsed, "b", None),
        file=getattr(parsed, "file", None),
        show=getattr(parsed, "show", None),
    )


def _load_tasks_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tasks = data.get("tasks", [])
    jobs: List[Dict[str, Any]] = []
    for t in tasks:
        label = t.get("label")
        if not label:
            continue
        jobs.append({
            "source": os.path.basename(path),
            "type": "tasks.json",
            "name": label,
            "command": t.get("command"),
            "args": t.get("args", []),
            "dependsOn": t.get("dependsOn"),
        })
    return jobs


def _load_agent_jobs_yaml(path: str) -> List[Dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except Exception:
        # YAML support is optional; return empty if not available
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    jobs_data = data.get("jobs", [])
    jobs: List[Dict[str, Any]] = []
    for j in jobs_data:
        name = j.get("name")
        if not name:
            continue
        jobs.append({
            "source": os.path.basename(path),
            "type": "agent_jobs.yaml",
            "name": name,
            "tool": j.get("tool"),
            "branch": j.get("branch"),
            "worktree": j.get("worktree"),
            "tests": j.get("tests"),
        })
    return jobs


def _discover_manifests(explicit_file: Optional[str]) -> List[str]:
    if explicit_file:
        return [explicit_file]
    candidates = [
        os.path.join(os.getcwd(), "tasks.json"),
        os.path.join(os.getcwd(), "agent_jobs.yaml"),
        os.path.join(os.getcwd(), "agent_jobs.yml"),
    ]
    return [p for p in candidates if os.path.exists(p)]


def _list_jobs(file: Optional[str], name_filter: Optional[str], show: Optional[str]) -> int:
    manifests = _discover_manifests(file)
    all_jobs: List[Dict[str, Any]] = []
    for m in manifests:
        base = os.path.basename(m)
        if base.endswith(".json"):
            try:
                all_jobs.extend(_load_tasks_json(m))
            except Exception as exc:
                print(f"Warning: failed to parse {base}: {exc}")
        elif base.endswith(".yaml") or base.endswith(".yml"):
            jobs = _load_agent_jobs_yaml(m)
            if not jobs:
                # If YAML not supported, provide a hint once
                pass
            all_jobs.extend(jobs)

    # Optional filtering
    if name_filter:
        needle = name_filter.lower()
        all_jobs = [j for j in all_jobs if needle in str(j.get("name", "")).lower()]

    # Stable ordering by name
    all_jobs.sort(key=lambda j: str(j.get("name", "")))

    if not all_jobs:
        if manifests:
            print("No jobs matched.")
        else:
            print("No manifests found (looked for tasks.json, agent_jobs.yaml).")
        return 0

    for j in all_jobs:
        src = j.get("source")
        nm = j.get("name")
        if j.get("type") == "tasks.json":
            cmd = j.get("command")
            print(f"{src}: {nm} (command: {cmd})")
            if show == "steps":
                args = j.get("args") or []
                depends = j.get("dependsOn")
                print(f"  args: {args}")
                if depends:
                    print(f"  dependsOn: {depends}")
        else:
            tool = j.get("tool")
            branch = j.get("branch")
            print(f"{src}: {nm} [tool: {tool}, branch: {branch}]")
            if show == "steps":
                worktree = j.get("worktree")
                tests = j.get("tests")
                print(f"  worktree: {worktree}")
                print(f"  tests: {tests}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the command-line interface.

    This function parses the command line arguments and dispatches to the
    appropriate subcommand implementation. It writes output to standard
    output and returns an exit code. When imported and executed from another
    module or script, the exit code may be used to determine success/failure.

    Parameters
    ----------
    argv:
        Optional argument list to parse instead of ``sys.argv[1:]``. Passing a
        list here facilitates unit testing.

    Returns
    -------
    int
        Exit status code (0 for success, non-zero for error).
    """
    try:
        args = parse_args(argv)
        if args.command == "greet":
            assert args.name is not None  # for type-checkers
            print(greet(args.name))
            return 0
        elif args.command == "sum":
            assert args.a is not None and args.b is not None
            result = sum_numbers(args.a, args.b)
            print(result)
            return 0
        elif args.command == "run-job":
            # We re-parse known optional args from sys.argv to avoid expanding CLIArgs
            # and keep backward compatibility of tests that import CLIArgs.
            # Since parse_args already parsed them, reach back into sys.argv via argparse Namespace
            # by re-parsing with the same parser would complicate structure; instead, inspect sys.argv here
            # is unnecessary because we already extended parse_args with the options; recover them from locals.
            # Mypy note: using getattr for optional attributes.
            # "type: ignore[attr-defined]" not needed at runtime.
            file = getattr(args, "file", None)
            name_filter = getattr(args, "name", None)
            show = getattr(args, "show", None)
            return _list_jobs(file, name_filter, show)
        else:
            # This branch should be unreachable because of argparse's required subcommand
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
