#!/usr/bin/env python3
"""
EAFIX Trading System CLI - Main Entry Point
Unified command-line interface for the trading system with APF integration
"""

import sys
import os
import typer
from typing import Optional
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Configure console for better Unicode support
try:
    from eafix.apps.cli.utils import configure_console
    configure_console()
except ImportError:
    pass

try:
    from eafix.apps.cli.apf.__main__ import app as apf_app
except ImportError:
    # Fallback if APF module is not available
    apf_app = typer.Typer(help="APF operations (not available)")
    
    @apf_app.command()
    def not_available():
        """APF module not available"""
        typer.secho("⚠️  APF module not available", fg=typer.colors.YELLOW)

from eafix.apps.cli.commands import (
    trading_app,
    guardian_app,
    system_app,
    analysis_app,
    setup_app
)

# Main CLI application
app = typer.Typer(
    name="eafix",
    help="EAFIX Trading System - Comprehensive CLI for trading operations, system management, and APF integration",
    add_completion=False,
    rich_markup_mode="rich"
)

# Add subcommand groups
app.add_typer(trading_app, name="trade", help="[bold blue]Trading operations and signals[/bold blue]")
app.add_typer(guardian_app, name="guardian", help="[bold red]Guardian protection system[/bold red]")
app.add_typer(system_app, name="system", help="[bold green]System management and monitoring[/bold green]")
app.add_typer(analysis_app, name="analyze", help="[bold yellow]Market analysis and reporting[/bold yellow]")
app.add_typer(setup_app, name="setup", help="[bold cyan]Setup and configuration[/bold cyan]")
app.add_typer(apf_app, name="apf", help="[bold magenta]Atomic Process Framework operations[/bold magenta]")

@app.command()
def version():
    """Show version information"""
    typer.echo("EAFIX Trading System CLI v1.0.0")
    typer.echo("Production-ready trading platform with Guardian protection")

@app.command()
def status():
    """Quick system status check"""
    try:
        from eafix.system.health_checker import HealthChecker
        checker = HealthChecker()
        status = checker.get_quick_status()
        
        if status['overall_health'] == 'healthy':
            typer.secho(f"✅ System Status: {status['overall_health'].upper()}", fg=typer.colors.GREEN)
        elif status['overall_health'] == 'warning':
            typer.secho(f"⚠️  System Status: {status['overall_health'].upper()}", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"❌ System Status: {status['overall_health'].upper()}", fg=typer.colors.RED)
            
        typer.echo(f"Database: {status['database']}")
        typer.echo(f"Guardian: {status['guardian']}")
        typer.echo(f"MT4 Connection: {status['mt4_connection']}")
        
    except ImportError:
        typer.secho("⚠️  Health checker not available. Run 'eafix setup install' to install dependencies.", 
                   fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error checking status: {e}", fg=typer.colors.RED)

@app.command()
def launch():
    """Launch the main trading system GUI"""
    try:
        import subprocess
        import sys
        
        # Try to launch the main trading system
        result = subprocess.run([sys.executable, "launch_trading_system.py"], 
                              cwd=Path.cwd(), 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            typer.secho("✅ Trading system launched successfully", fg=typer.colors.GREEN)
        else:
            typer.secho(f"❌ Failed to launch: {result.stderr}", fg=typer.colors.RED)
            
    except Exception as e:
        typer.secho(f"❌ Error launching system: {e}", fg=typer.colors.RED)

def main():
    """Main CLI entry point with error handling"""
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\n⏹️  Operation cancelled by user", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.secho(f"❌ Unexpected error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    main()