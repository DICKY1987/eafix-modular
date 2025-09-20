"""
Setup and Installation Commands Module
CLI commands for system setup, dependency management, and configuration
"""

import typer
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

app = typer.Typer(help="Setup and configuration tools")

@app.command()
def install(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall dependencies"),
    dev: bool = typer.Option(False, "--dev", help="Install development dependencies")
):
    """Install system dependencies and requirements"""
    try:
        typer.secho("📦 Installing EAFIX Dependencies", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        # Check for requirements files
        req_files = [
            "mt4_dde_interface/requirements.txt",
            "requirements.txt"
        ]
        
        found_requirements = []
        for req_file in req_files:
            if Path(req_file).exists():
                found_requirements.append(req_file)
        
        if not found_requirements:
            typer.secho("⚠️  No requirements.txt files found", fg=typer.colors.YELLOW)
            return
        
        # Install each requirements file
        for req_file in found_requirements:
            typer.echo(f"📋 Installing from {req_file}...")
            
            cmd = [sys.executable, "-m", "pip", "install", "-r", req_file]
            if force:
                cmd.append("--force-reinstall")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                typer.secho(f"✅ Installed from {req_file}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"❌ Failed to install from {req_file}", fg=typer.colors.RED)
                typer.echo(f"Error: {result.stderr}")
        
        # Install additional development tools if requested
        if dev:
            typer.echo("\n🛠️  Installing development tools...")
            dev_packages = [
                "pytest",
                "pytest-asyncio", 
                "typer[all]",
                "rich",
                "psutil"
            ]
            
            for package in dev_packages:
                cmd = [sys.executable, "-m", "pip", "install", package]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    typer.secho(f"✅ Installed {package}", fg=typer.colors.GREEN)
                else:
                    typer.secho(f"❌ Failed to install {package}", fg=typer.colors.RED)
        
        typer.secho("\n🎉 Installation completed!", fg=typer.colors.GREEN, bold=True)
        
    except Exception as e:
        typer.secho(f"❌ Installation error: {e}", fg=typer.colors.RED)

@app.command()
def init(
    directory: Optional[str] = typer.Argument(None, help="Directory to initialize (default: current)"),
    template: str = typer.Option("basic", "--template", "-t", help="Template type (basic, full, minimal)")
):
    """Initialize a new EAFIX project structure"""
    try:
        target_dir = Path(directory) if directory else Path.cwd()
        
        typer.secho(f"🚀 Initializing EAFIX project in {target_dir}", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 50)
        
        # Create directory structure based on template
        if template == "minimal":
            directories = [
                "src/eafix/signals",
                "tests",
                "logs"
            ]
            files = {
                "settings.json": """{
  "signals": {
    "FridayMove": {
      "enabled": true,
      "percent_threshold": 1.0
    }
  }
}""",
                "README.md": "# EAFIX Trading System\\n\\nMinimal setup for trading system."
            }
        
        elif template == "full":
            directories = [
                "src/eafix/apps/cli",
                "src/eafix/guardian", 
                "src/eafix/signals",
                "src/eafix/indicators",
                "src/eafix/positioning",
                "core",
                "tabs",
                "mt4_dde_interface",
                "tests/enhanced",
                "tools",
                "docs",
                "logs"
            ]
            files = {
                "settings.json": Path("settings.json").read_text() if Path("settings.json").exists() else "{}",
                "pytest.ini": "[pytest]\\ntestpaths = tests\\npythonpath = src\\n",
                "launch_trading_system.py": "#!/usr/bin/env python3\\n# Main trading system launcher\\nprint('Trading system launcher')",
                "README.md": "# EAFIX Trading System\\n\\nFull trading system with Guardian protection."
            }
        
        else:  # basic template
            directories = [
                "src/eafix/signals",
                "src/eafix/guardian",
                "core", 
                "tests",
                "logs"
            ]
            files = {
                "settings.json": """{
  "signals": {
    "FridayMove": {
      "enabled": true,
      "percent_threshold": 1.0
    }
  },
  "dde": {
    "poll_ms": 100
  }
}""",
                "README.md": "# EAFIX Trading System\\n\\nBasic trading system setup."
            }
        
        # Create directories
        for dir_path in directories:
            full_path = target_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            typer.echo(f"📁 Created directory: {dir_path}")
        
        # Create files
        for file_path, content in files.items():
            full_path = target_dir / file_path
            if not full_path.exists() or typer.confirm(f"File {file_path} exists. Overwrite?"):
                full_path.write_text(content)
                typer.echo(f"📄 Created file: {file_path}")
        
        # Create __init__.py files for Python packages
        python_dirs = [d for d in directories if d.startswith("src/")]
        for py_dir in python_dirs:
            init_file = target_dir / py_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text("")
                typer.echo(f"🐍 Created __init__.py in {py_dir}")
        
        typer.secho(f"\\n✅ Project initialized with {template} template!", fg=typer.colors.GREEN, bold=True)
        typer.echo("\\nNext steps:")
        typer.echo("1. Run 'eafix setup install' to install dependencies")
        typer.echo("2. Configure settings.json for your environment")
        typer.echo("3. Run 'eafix system health' to check system status")
        
    except Exception as e:
        typer.secho(f"❌ Initialization error: {e}", fg=typer.colors.RED)

@app.command()
def test_install():
    """Test the CLI installation and basic functionality"""
    try:
        typer.secho("🧪 Testing EAFIX CLI Installation", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        # Test Python imports
        typer.echo("🐍 Testing Python imports...")
        test_imports = [
            ("typer", "CLI framework"),
            ("pathlib", "Path handling"),
            ("json", "JSON processing"),
            ("datetime", "Date/time handling"),
            ("subprocess", "Process execution")
        ]
        
        for module, description in test_imports:
            try:
                __import__(module)
                typer.secho(f"  ✅ {module}: {description}", fg=typer.colors.GREEN)
            except ImportError:
                typer.secho(f"  ❌ {module}: {description} - MISSING", fg=typer.colors.RED)
        
        # Test file structure
        typer.echo("\\n📁 Testing file structure...")
        required_paths = [
            ("src/eafix/apps/cli/main.py", "Main CLI module"),
            ("src/eafix/apps/cli/commands/", "Command modules directory"),
            ("settings.json", "Configuration file"),
            ("CLAUDE.md", "Documentation")
        ]
        
        for file_path, description in required_paths:
            path = Path(file_path)
            if path.exists():
                typer.secho(f"  ✅ {file_path}: {description}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"  ⚠️  {file_path}: {description} - MISSING", fg=typer.colors.YELLOW)
        
        # Test CLI commands
        typer.echo("\\n⚙️  Testing CLI commands...")
        try:
            from eafix.apps.cli.main import app as cli_app
            typer.secho("  ✅ Main CLI app loads successfully", fg=typer.colors.GREEN)
        except ImportError as e:
            typer.secho(f"  ❌ CLI app failed to load: {e}", fg=typer.colors.RED)
        
        # Test configuration
        typer.echo("\\n⚙️  Testing configuration...")
        config_file = Path("settings.json")
        if config_file.exists():
            try:
                import json
                with open(config_file) as f:
                    config = json.load(f)
                typer.secho("  ✅ Configuration file is valid JSON", fg=typer.colors.GREEN)
                
                # Check required sections
                required_sections = ["signals", "dde", "ui"]
                for section in required_sections:
                    if section in config:
                        typer.secho(f"  ✅ Configuration has {section} section", fg=typer.colors.GREEN)
                    else:
                        typer.secho(f"  ⚠️  Configuration missing {section} section", fg=typer.colors.YELLOW)
            
            except json.JSONDecodeError:
                typer.secho("  ❌ Configuration file has invalid JSON", fg=typer.colors.RED)
        else:
            typer.secho("  ⚠️  No configuration file found", fg=typer.colors.YELLOW)
        
        # Test database connectivity
        typer.echo("\\n💾 Testing database connectivity...")
        db_files = [
            "trading_system.db",
            "huey_project_organizer.db"
        ]
        
        for db_file in db_files:
            if Path(db_file).exists():
                typer.secho(f"  ✅ Database file exists: {db_file}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"  ⚠️  Database file not found: {db_file}", fg=typer.colors.YELLOW)
        
        typer.secho("\\n🎉 Installation test completed!", fg=typer.colors.GREEN, bold=True)
        
    except Exception as e:
        typer.secho(f"❌ Test failed: {e}", fg=typer.colors.RED)

@app.command()
def configure(
    mt4_path: Optional[str] = typer.Option(None, "--mt4-path", help="MetaTrader 4 installation path"),
    database_path: Optional[str] = typer.Option(None, "--db-path", help="Database directory path"),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Interactive configuration mode")
):
    """Configure system settings and paths"""
    try:
        import json
        
        config_file = Path("settings.json")
        
        # Load existing configuration
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
        else:
            config = {}
        
        typer.secho("⚙️  EAFIX System Configuration", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if interactive:
            # Interactive configuration
            typer.echo("🖥️  Interactive Configuration Mode")
            typer.echo("Press Enter to keep current values\\n")
            
            # Trading signals configuration
            if "signals" not in config:
                config["signals"] = {}
            
            friday_enabled = typer.prompt(
                f"Enable Friday Vol Signal [{config.get('signals', {}).get('FridayMove', {}).get('enabled', True)}]",
                default=config.get('signals', {}).get('FridayMove', {}).get('enabled', True),
                type=bool
            )
            
            threshold = typer.prompt(
                f"Friday Vol threshold [{config.get('signals', {}).get('FridayMove', {}).get('percent_threshold', 1.0)}]",
                default=config.get('signals', {}).get('FridayMove', {}).get('percent_threshold', 1.0),
                type=float
            )
            
            config["signals"]["FridayMove"] = {
                "enabled": friday_enabled,
                "percent_threshold": threshold,
                "start_local": "07:30",
                "end_local": "14:00"
            }
            
            # DDE configuration
            if "dde" not in config:
                config["dde"] = {}
            
            poll_ms = typer.prompt(
                f"DDE polling interval (ms) [{config.get('dde', {}).get('poll_ms', 100)}]",
                default=config.get('dde', {}).get('poll_ms', 100),
                type=int
            )
            
            config["dde"]["poll_ms"] = poll_ms
        
        # Apply command line options
        if mt4_path:
            if "paths" not in config:
                config["paths"] = {}
            config["paths"]["mt4_terminal"] = mt4_path
            typer.secho(f"✅ MT4 path set to: {mt4_path}", fg=typer.colors.GREEN)
        
        if database_path:
            if "paths" not in config:
                config["paths"] = {}
            config["paths"]["database_dir"] = database_path
            typer.secho(f"✅ Database path set to: {database_path}", fg=typer.colors.GREEN)
        
        # Save configuration
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        typer.secho(f"\\n💾 Configuration saved to {config_file}", fg=typer.colors.GREEN, bold=True)
        
        # Validate configuration
        typer.echo("\\n🔍 Validating configuration...")
        
        # Check MT4 path if specified
        if config.get("paths", {}).get("mt4_terminal"):
            mt4_path = Path(config["paths"]["mt4_terminal"])
            if mt4_path.exists():
                typer.secho("  ✅ MT4 path is valid", fg=typer.colors.GREEN)
            else:
                typer.secho("  ⚠️  MT4 path does not exist", fg=typer.colors.YELLOW)
        
        typer.secho("✅ Configuration complete!", fg=typer.colors.GREEN)
        
    except Exception as e:
        typer.secho(f"❌ Configuration error: {e}", fg=typer.colors.RED)

@app.command()
def doctor():
    """Run comprehensive system diagnostics"""
    try:
        typer.secho("🏥 EAFIX System Doctor", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        issues_found = []
        
        # Check Python version
        typer.echo("🐍 Checking Python version...")
        python_version = sys.version_info
        if python_version >= (3, 8):
            typer.secho(f"  ✅ Python {python_version.major}.{python_version.minor}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  ❌ Python {python_version.major}.{python_version.minor} (requires >= 3.8)", fg=typer.colors.RED)
            issues_found.append("Python version too old")
        
        # Check critical dependencies
        typer.echo("\\n📦 Checking critical dependencies...")
        critical_deps = ["typer", "pathlib", "json", "datetime", "subprocess"]
        
        for dep in critical_deps:
            try:
                __import__(dep)
                typer.secho(f"  ✅ {dep}", fg=typer.colors.GREEN)
            except ImportError:
                typer.secho(f"  ❌ {dep} - MISSING", fg=typer.colors.RED)
                issues_found.append(f"Missing dependency: {dep}")
        
        # Check file permissions
        typer.echo("\\n📁 Checking file permissions...")
        import os
        critical_paths = [
            Path("settings.json"),
            Path("src/eafix/apps/cli/main.py"),
            Path.cwd()
        ]
        
        for path in critical_paths:
            if path.exists():
                if path.is_file():
                    if os.access(path, os.R_OK):
                        typer.secho(f"  ✅ {path} - readable", fg=typer.colors.GREEN)
                    else:
                        typer.secho(f"  ❌ {path} - not readable", fg=typer.colors.RED)
                        issues_found.append(f"Cannot read {path}")
                elif path.is_dir():
                    if os.access(path, os.W_OK):
                        typer.secho(f"  ✅ {path} - writable", fg=typer.colors.GREEN)
                    else:
                        typer.secho(f"  ❌ {path} - not writable", fg=typer.colors.RED)
                        issues_found.append(f"Cannot write to {path}")
        
        # Check disk space
        typer.echo("\\n💾 Checking disk space...")
        try:
            import shutil
            total, used, free = shutil.disk_usage(Path.cwd())
            free_gb = free // (1024**3)
            
            if free_gb > 1:
                typer.secho(f"  ✅ {free_gb} GB free space", fg=typer.colors.GREEN)
            else:
                typer.secho(f"  ⚠️  {free_gb} GB free space (low)", fg=typer.colors.YELLOW)
                issues_found.append("Low disk space")
                
        except Exception:
            typer.secho("  ⚠️  Could not check disk space", fg=typer.colors.YELLOW)
        
        # Summary
        typer.echo("\\n" + "="*50)
        if not issues_found:
            typer.secho("🎉 System is healthy - no issues found!", fg=typer.colors.GREEN, bold=True)
        else:
            typer.secho(f"⚠️  Found {len(issues_found)} issues:", fg=typer.colors.YELLOW, bold=True)
            for issue in issues_found:
                typer.echo(f"  • {issue}")
            
            typer.echo("\\nRecommended actions:")
            typer.echo("1. Run 'eafix setup install' to install missing dependencies")
            typer.echo("2. Check file permissions in your project directory")
            typer.echo("3. Ensure adequate free disk space")
        
    except Exception as e:
        typer.secho(f"❌ Doctor check failed: {e}", fg=typer.colors.RED)