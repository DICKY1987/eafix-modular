#!/usr/bin/env python3
"""
Development Tools Setup Script
==============================

Automated setup script to install and configure all necessary CLI tools
and development environment for the CLI Multi-Rapid Enterprise Platform.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and report success/failure."""
    print(f"\n[SETUP] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {description}")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"[FAILED] {description}")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} - EXCEPTION: {e}")
        return False


def check_tool_installed(tool_name, command, description):
    """Check if a tool is installed."""
    print(f"\n[CHECK] {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[INSTALLED] {description}: {version}")
            return True
        else:
            print(f"[NOT FOUND] {description}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} - CHECK FAILED: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("CLI MULTI-RAPID ENTERPRISE PLATFORM")
    print("DEVELOPMENT TOOLS SETUP")
    print("=" * 60)
    
    setup_results = []
    
    # 1. Check Core Tools
    print("\n[PHASE] CHECKING CORE TOOLS...")
    core_tools = [
        ("Python", "python --version", "Python interpreter"),
        ("Git", "git --version", "Git version control"),
        ("Pip", "pip --version", "Python package manager"),
    ]
    
    for tool_name, command, description in core_tools:
        result = check_tool_installed(tool_name, command, description)
        setup_results.append((f"Core Tool: {tool_name}", result))
    
    # 2. Install Python Development Tools
    print("\n[PHASE] INSTALLING PYTHON DEVELOPMENT TOOLS...")
    dev_tools = [
        ("pip install --upgrade pip", "Upgrade pip to latest version"),
        ("pip install black isort mypy ruff bandit nox coverage pytest-cov", "Install development and testing tools"),
        ("pip install -r requirements.txt", "Install project requirements"),
    ]
    
    for command, description in dev_tools:
        result = run_command(command, description)
        setup_results.append((f"Dev Tool: {description}", result))
    
    # 3. Verify Installed Tools
    print("\n[PHASE] VERIFYING INSTALLED TOOLS...")
    verification_tools = [
        ("Black", "black --version", "Code formatter"),
        ("isort", "isort --version", "Import sorter"),
        ("MyPy", "mypy --version", "Type checker"),
        ("Ruff", "ruff --version", "Fast linter"),
        ("Bandit", "bandit --version", "Security linter"),
        ("Nox", "nox --version", "Testing automation"),
        ("Pytest", "pytest --version", "Testing framework"),
    ]
    
    for tool_name, command, description in verification_tools:
        result = check_tool_installed(tool_name, command, description)
        setup_results.append((f"Verify Tool: {tool_name}", result))
    
    # 4. Test CLI Multi-Rapid Commands
    print("\n[PHASE] TESTING CLI MULTI-RAPID COMMANDS...")
    cli_tests = [
        ("python -m src.cli_multi_rapid.cli --help", "Test enhanced CLI help"),
        ("python -m workflows.orchestrator status", "Test workflow orchestrator"),
        ("python -m workflows.execution_roadmap status", "Test execution roadmap"),
    ]
    
    for command, description in cli_tests:
        result = run_command(command, description)
        setup_results.append((f"CLI Test: {description}", result))
    
    # 5. Test Cross-Language Bridge
    print("\n[PHASE] TESTING CROSS-LANGUAGE BRIDGE...")
    bridge_command = "python test_cross_language_bridge.py"
    result = run_command(bridge_command, "Test cross-language bridge system")
    setup_results.append(("Bridge Test: Cross-language system", result))
    
    # 6. Setup Summary
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    successful_setups = 0
    total_setups = len(setup_results)
    
    for setup_name, success in setup_results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {setup_name}")
        if success:
            successful_setups += 1
    
    print(f"\nSetup Results: {successful_setups}/{total_setups} successful")
    
    if successful_setups >= total_setups * 0.8:  # 80% success rate
        print("\n[SUCCESS] DEVELOPMENT ENVIRONMENT SETUP SUCCESSFUL!")
        print("\nYour CLI Multi-Rapid Enterprise Platform is ready for development!")
        print("\nNext steps:")
        print("1. Open VS Code in this directory")
        print("2. Install recommended extensions (see .vscode/extensions.json)")
        print("3. Use Ctrl+Shift+P > 'Tasks: Run Task' to access all CLI tools")
        print("4. Start developing with the enterprise orchestration platform!")
        return 0
    else:
        print("\n[PARTIAL] DEVELOPMENT ENVIRONMENT SETUP PARTIAL")
        print("Some tools failed to install or configure properly.")
        print("Please review the errors above and install missing tools manually.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[STOPPED] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Setup failed with exception: {e}")
        sys.exit(1)