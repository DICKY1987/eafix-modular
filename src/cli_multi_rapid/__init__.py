"""
cli_multi_rapid package
=======================

This package contains the core implementation for a very simple example CLI tool.
It provides utility functions and a command-line interface entrypoint. The goal
is to demonstrate how to structure a Python project using an explicit package
layout, and to provide a foundation that can be extended in future iterations.

The package currently implements two subcommands:

* ``greet`` – prints a personalised greeting for the provided name.
* ``sum`` – computes the sum of two integers and prints the result.

Both commands use the standard library ``argparse`` module to parse command line
arguments and handle errors gracefully. The public API for these commands is
exposed via the :func:`greet` and :func:`sum_numbers` functions which can
also be consumed programmatically. A convenience :func:`main` function is
provided as the entry point for the CLI defined in :mod:`cli_multi_rapid.cli`.
"""

from .cli import main, greet, sum_numbers  # noqa: F401 re-export for convenience

__all__ = [
    "main",
    "greet",
    "sum_numbers",
]