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
from typing import List, Optional


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

    parsed = parser.parse_args(argv)
    return CLIArgs(command=parsed.command, name=getattr(parsed, "name", None), a=getattr(parsed, "a", None), b=getattr(parsed, "b", None))


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
        else:
            # This branch should be unreachable because of argparse's required subcommand
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1