#!/usr/bin/env python3
"""
ALVT CLI - Unified command-line interface
doc_id: 2099900126260118
version: 1.0

Provides unified interface for all ALVT verification tools.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

__doc_id__ = "2099900126260118"


def run_command(cmd: list[str]) -> int:
    """Run command and return exit code."""
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"ERROR: Failed to run command: {e}", file=sys.stderr)
        return 1


def validate_contract(args: argparse.Namespace) -> int:
    """Run contract validation."""
    script_dir = Path(__file__).parent
    validator = script_dir / "2099900119260118_validate_contract.py"
    
    cmd = [sys.executable, str(validator), "--trigger", args.trigger]
    
    if args.repo_root:
        cmd.extend(["--repo-root", args.repo_root])
    
    return run_command(cmd)


def layer0(args: argparse.Namespace) -> int:
    """Run Layer 0 static verification."""
    script_dir = Path(__file__).parent
    layer0_tool = script_dir / "2099900121260118_layer0_static.py"
    
    cmd = [sys.executable, str(layer0_tool), "--trigger", args.trigger]
    
    if args.repo_root:
        cmd.extend(["--repo-root", args.repo_root])
    if args.output:
        cmd.extend(["--output", args.output])
    
    return run_command(cmd)


def layer1(args: argparse.Namespace) -> int:
    """Run Layer 1 graph verification."""
    script_dir = Path(__file__).parent
    layer1_tool = script_dir / "2099900122260118_layer1_graph.py"
    
    cmd = [sys.executable, str(layer1_tool), "--trigger", args.trigger]
    
    if args.repo_root:
        cmd.extend(["--repo-root", args.repo_root])
    if args.output:
        cmd.extend(["--output", args.output])
    
    return run_command(cmd)


def verify_all(args: argparse.Namespace) -> int:
    """Run all verification steps in sequence."""
    print(f"Running full ALVT verification for trigger: {args.trigger}")
    print("=" * 60)
    
    # Step 1: Validate contract
    print("\nStep 1: Contract Validation")
    print("-" * 60)
    exit_code = validate_contract(args)
    if exit_code != 0:
        print("\n❌ Contract validation FAILED")
        return exit_code
    print("✅ Contract validation PASSED")
    
    # Step 2: Layer 0
    print("\nStep 2: Layer 0 (Static Integrity)")
    print("-" * 60)
    exit_code = layer0(args)
    if exit_code != 0:
        print("\n❌ Layer 0 verification FAILED")
        return exit_code
    print("✅ Layer 0 verification PASSED")
    
    # Step 3: Layer 1
    print("\nStep 3: Layer 1 (Graph Connectivity)")
    print("-" * 60)
    exit_code = layer1(args)
    if exit_code != 0:
        print("\n❌ Layer 1 verification FAILED")
        return exit_code
    print("✅ Layer 1 verification PASSED")
    
    # Success
    print("\n" + "=" * 60)
    print(f"✅ All verification steps PASSED for {args.trigger}")
    print("=" * 60)
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ALVT CLI - Automation Lifecycle Verification Tooling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate contract
  alvt_cli.py validate --trigger FILE_IDENTITY_CREATE
  
  # Run Layer 0 verification
  alvt_cli.py layer0 --trigger FILE_IDENTITY_CREATE
  
  # Run Layer 1 verification
  alvt_cli.py layer1 --trigger FILE_IDENTITY_CREATE
  
  # Run all verification steps
  alvt_cli.py verify --trigger FILE_IDENTITY_CREATE
        """
    )
    
    parser.add_argument(
        "--repo-root",
        type=str,
        help="Repository root path (default: current directory)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate trigger contract"
    )
    validate_parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID (e.g., FILE_IDENTITY_CREATE)"
    )
    
    # Layer 0 command
    layer0_parser = subparsers.add_parser(
        "layer0",
        help="Run Layer 0 static integrity verification"
    )
    layer0_parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID"
    )
    layer0_parser.add_argument(
        "--output",
        type=str,
        help="Output report path"
    )
    
    # Layer 1 command
    layer1_parser = subparsers.add_parser(
        "layer1",
        help="Run Layer 1 graph connectivity verification"
    )
    layer1_parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID"
    )
    layer1_parser.add_argument(
        "--output",
        type=str,
        help="Output report path"
    )
    
    # Verify command (all steps)
    verify_parser = subparsers.add_parser(
        "verify",
        help="Run all verification steps (contract, layer0, layer1)"
    )
    verify_parser.add_argument(
        "--trigger",
        required=True,
        help="Trigger ID"
    )
    verify_parser.add_argument(
        "--output",
        type=str,
        help="Output directory for reports (default: reports/alvt/)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Dispatch to command handler
    if args.command == "validate":
        return validate_contract(args)
    elif args.command == "layer0":
        return layer0(args)
    elif args.command == "layer1":
        return layer1(args)
    elif args.command == "verify":
        return verify_all(args)
    else:
        print(f"ERROR: Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
