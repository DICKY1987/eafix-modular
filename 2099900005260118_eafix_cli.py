# doc_id: DOC-DOC-0021
# DOC_ID: DOC-SERVICE-0002
# apps/cli/src/eafix_cli/__init__.py

"""
EAFIX CLI - Command-line interface for EAFIX trading system
Provides tools for development, operations, and process management
"""

import click
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint

from .commands.validate import validate_group
from .commands.process import process_group
from .commands.deploy import deploy_group
from .commands.monitor import monitor_group
from .commands.security import security_group
from .utils.config import CLIConfig
from .utils.api_client import APIClient
from .utils.formatters import OutputFormatter

console = Console()


class EAFIXContext:
    """CLI context for sharing state between commands"""
    
    def __init__(self):
        self.config = CLIConfig()
        self.api_client = APIClient(self.config)
        self.formatter = OutputFormatter()
        self.verbose = False
        self.output_format = "table"


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'yaml']), 
              default='table', help='Output format')
@click.pass_context
def cli(ctx, config, verbose, output):
    """EAFIX CLI - Command-line interface for EAFIX trading system"""
    
    # Initialize context
    ctx.ensure_object(EAFIXContext)
    ctx.obj.verbose = verbose
    ctx.obj.output_format = output
    
    if config:
        ctx.obj.config.load_from_file(config)
    
    # Set up console logging
    if verbose:
        console.print("[dim]EAFIX CLI v1.0.0 - Verbose mode enabled[/dim]")


# Register command groups
cli.add_command(validate_group)
cli.add_command(process_group)
cli.add_command(deploy_group)
cli.add_command(monitor_group)
cli.add_command(security_group)


@cli.command()
@click.pass_context
def version(ctx):
    """Show EAFIX CLI version"""
    version_info = {
        "cli_version": "1.0.0",
        "python_version": sys.version,
        "config_file": str(ctx.obj.config.config_file),
        "api_endpoint": ctx.obj.config.api_endpoint
    }
    
    if ctx.obj.output_format == "json":
        click.echo(json.dumps(version_info, indent=2))
    else:
        console.print(Panel.fit(f"[bold]EAFIX CLI v{version_info['cli_version']}[/bold]"))
        console.print(f"Python: {version_info['python_version']}")
        console.print(f"Config: {version_info['config_file']}")
        console.print(f"API: {version_info['api_endpoint']}")


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status"""
    
    async def get_status():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Checking system status...", total=None)
                
                # Check all services
                services = [
                    "data-ingestor",
                    "indicator-engine", 
                    "signal-generator",
                    "risk-manager",
                    "execution-engine",
                    "reentry-matrix",
                    "portfolio-manager",
                    "notification-service",
                    "process-executor"
                ]
                
                status_data = []
                for service in services:
                    try:
                        health = await ctx.obj.api_client.get_service_health(service)
                        status_data.append({
                            "service": service,
                            "status": health.get("status", "unknown"),
                            "uptime": health.get("uptime", 0),
                            "version": health.get("version", "unknown")
                        })
                    except Exception as e:
                        status_data.append({
                            "service": service,
                            "status": "error",
                            "uptime": 0,
                            "version": "unknown",
                            "error": str(e)
                        })
                
                progress.update(task, completed=True)
            
            # Format output
            if ctx.obj.output_format == "json":
                click.echo(json.dumps(status_data, indent=2))
            else:
                ctx.obj.formatter.print_service_status(status_data)
                
        except Exception as e:
            console.print(f"[red]Error checking status: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(get_status())


@cli.command()
@click.option('--service', help='Specific service to check')
@click.pass_context
def logs(ctx, service):
    """View service logs"""
    
    async def get_logs():
        try:
            if service:
                logs = await ctx.obj.api_client.get_service_logs(service)
                if ctx.obj.output_format == "json":
                    click.echo(json.dumps(logs, indent=2))
                else:
                    ctx.obj.formatter.print_logs(logs, service)
            else:
                # Show logs from all services
                services = ["data-ingestor", "indicator-engine", "signal-generator"]
                
                with Progress(console=console) as progress:
                    task = progress.add_task("Fetching logs...", total=len(services))
                    
                    for svc in services:
                        try:
                            logs = await ctx.obj.api_client.get_service_logs(svc, limit=10)
                            if not ctx.obj.output_format == "json":
                                console.print(f"\n[bold]{svc.upper()}[/bold]")
                                ctx.obj.formatter.print_logs(logs, svc)
                        except Exception as e:
                            if ctx.obj.verbose:
                                console.print(f"[red]Error fetching logs for {svc}: {e}[/red]")
                        
                        progress.advance(task)
                        
        except Exception as e:
            console.print(f"[red]Error fetching logs: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(get_logs())


@cli.command()
@click.argument('environment')
@click.option('--service', help='Specific service to configure')
@click.option('--key', help='Configuration key')
@click.option('--value', help='Configuration value')
@click.pass_context
def config(ctx, environment, service, key, value):
    """Manage configuration"""
    
    async def manage_config():
        try:
            if key and value:
                # Set configuration
                await ctx.obj.api_client.set_config(environment, service, key, value)
                console.print(f"[green]✓[/green] Set {key}={value} for {service or 'global'} in {environment}")
            else:
                # Get configuration
                config_data = await ctx.obj.api_client.get_config(environment, service)
                
                if ctx.obj.output_format == "json":
                    click.echo(json.dumps(config_data, indent=2))
                else:
                    ctx.obj.formatter.print_config(config_data, environment, service)
                    
        except Exception as e:
            console.print(f"[red]Error managing config: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(manage_config())


@cli.command()
@click.option('--watch', '-w', is_flag=True, help='Watch for real-time updates')
@click.option('--interval', default=5, help='Update interval in seconds')
@click.pass_context
def metrics(ctx, watch, interval):
    """View system metrics"""
    
    async def get_metrics():
        try:
            while True:
                metrics_data = await ctx.obj.api_client.get_metrics()
                
                if ctx.obj.output_format == "json":
                    click.echo(json.dumps(metrics_data, indent=2))
                    if not watch:
                        break
                else:
                    console.clear()
                    ctx.obj.formatter.print_metrics(metrics_data)
                    
                    if not watch:
                        break
                    
                    console.print(f"\n[dim]Updating every {interval}s... (Press Ctrl+C to stop)[/dim]")
                    await asyncio.sleep(interval)
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]Error fetching metrics: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(get_metrics())


@cli.command()
@click.argument('query')
@click.option('--limit', default=100, help='Number of results to return')
@click.option('--format', type=click.Choice(['table', 'json', 'csv']), 
              default='table', help='Output format')
@click.pass_context
def query(ctx, query, limit, format):
    """Query system data"""
    
    async def execute_query():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Executing query...", total=None)
                
                results = await ctx.obj.api_client.execute_query(query, limit)
                progress.update(task, completed=True)
            
            if format == "json":
                click.echo(json.dumps(results, indent=2))
            elif format == "csv":
                ctx.obj.formatter.print_csv(results)
            else:
                ctx.obj.formatter.print_query_results(results, query)
                
        except Exception as e:
            console.print(f"[red]Error executing query: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(execute_query())


@cli.command()
@click.pass_context
def doctor(ctx):
    """Run system diagnostics"""
    
    async def run_diagnostics():
        console.print("[bold]EAFIX System Diagnostics[/bold]\n")
        
        checks = [
            ("Configuration", ctx.obj.api_client.check_config),
            ("Database Connection", ctx.obj.api_client.check_database),
            ("Redis Connection", ctx.obj.api_client.check_redis),
            ("Service Health", ctx.obj.api_client.check_services),
            ("API Endpoints", ctx.obj.api_client.check_endpoints),
            ("Security", ctx.obj.api_client.check_security),
        ]
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for check_name, check_func in checks:
                task = progress.add_task(f"Checking {check_name.lower()}...", total=None)
                
                try:
                    result = await check_func()
                    status = "✓ PASS" if result.get("healthy", False) else "✗ FAIL"
                    results.append({
                        "check": check_name,
                        "status": status,
                        "details": result.get("details", ""),
                        "healthy": result.get("healthy", False)
                    })
                except Exception as e:
                    results.append({
                        "check": check_name,
                        "status": "✗ ERROR",
                        "details": str(e),
                        "healthy": False
                    })
                
                progress.update(task, completed=True)
        
        # Print results
        console.print("\n[bold]Diagnostic Results:[/bold]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        for result in results:
            status_style = "green" if result["healthy"] else "red"
            table.add_row(
                result["check"],
                f"[{status_style}]{result['status']}[/{status_style}]",
                result["details"]
            )
        
        console.print(table)
        
        # Summary
        passed = sum(1 for r in results if r["healthy"])
        total = len(results)
        
        if passed == total:
            console.print(f"\n[green]✓ All {total} checks passed![/green]")
        else:
            console.print(f"\n[yellow]⚠ {passed}/{total} checks passed[/yellow]")
            if passed < total:
                sys.exit(1)
    
    asyncio.run(run_diagnostics())


if __name__ == '__main__':
    cli()