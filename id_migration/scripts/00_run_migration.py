from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG_PATH = REPO_ROOT / "id_migration" / "config" / "physical_id_config.json"
ASSIGN_SCRIPT_PATH = SCRIPT_DIR / "02_assign_physical_ids.py"


def run_step(arguments: list[str]) -> int:
    command = [sys.executable, str(ASSIGN_SCRIPT_PATH), *arguments]
    result = subprocess.run(command, cwd=REPO_ROOT)
    return result.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PH-02 migration orchestrator")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Path to physical_id_config.json")
    parser.add_argument("--mode", choices=["plan", "apply"], required=True, help="Run mode")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()

    if not ASSIGN_SCRIPT_PATH.is_file():
        print(f"ERROR: allocator script not found: {ASSIGN_SCRIPT_PATH}", file=sys.stderr)
        return 2
    if not config_path.is_file():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        return 2

    shared_args = ["--config", str(config_path)]

    if args.mode == "plan":
        return run_step([*shared_args, "--mode", "plan"])

    for step_args in (
        [*shared_args, "--mode", "apply"],
        [*shared_args, "--derive-registry"],
    ):
        exit_code = run_step(step_args)
        if exit_code != 0:
            return exit_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
