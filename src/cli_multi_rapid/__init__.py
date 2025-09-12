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

__all__ = ["main", "greet", "sum_numbers"]


def main(*args, **kwargs):  # pragma: no cover - thin wrapper
    """Lazy wrapper for `cli_multi_rapid.cli.main` to avoid import side effects.

    Importing the CLI implementation only when used prevents `python -m`
    warnings by ensuring the submodule isn't pre-imported during package init.
    """
    from .cli import main as _main

    return _main(*args, **kwargs)


def greet(name):  # pragma: no cover - thin wrapper
    from .cli import greet as _greet

    return _greet(name)


def sum_numbers(a, b):  # pragma: no cover - thin wrapper
    from .cli import sum_numbers as _sum

    return _sum(a, b)
