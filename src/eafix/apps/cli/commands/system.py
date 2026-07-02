"""
System Management Commands Module
CLI commands for system monitoring, health checks, and configuration
"""

import typer
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

app = typer.Typer(help="System management and monitoring")

@app.command()
def health():
    """Comprehensive system health check"""
    try:
        from eafix.system.health_checker import HealthChecker
        
        typer.secho("🏥 System Health Check", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        checker = HealthChecker()
        health_report = checker.get_full_health_report()
        
        # Overall health
        overall = health_report.get('overall_health', 'unknown')
        if overall == 'healthy':
            typer.secho(f"✅ Overall Status: {overall.upper()}", fg=typer.colors.GREEN, bold=True)
        elif overall == 'warning':
            typer.secho(f"⚠️  Overall Status: {overall.upper()}", fg=typer.colors.YELLOW, bold=True)
        else:
            typer.secho(f"❌ Overall Status: {overall.upper()}", fg=typer.colors.RED, bold=True)
        
        # Component health
        typer.echo(f"\n🔧 Component Health:")
        components = health_report.get('components', {})
        
        for component, status in components.items():
            if status == 'healthy':
                typer.secho(f"  ✅ {component}: {status}", fg=typer.colors.GREEN)
            elif status == 'warning':
                typer.secho(f"  ⚠️  {component}: {status}", fg=typer.colors.YELLOW)
            else:
                typer.secho(f"  ❌ {component}: {status}", fg=typer.colors.RED)
        
        # Performance metrics
        if health_report.get('metrics'):
            typer.echo(f"\n📊 Performance Metrics:")
            metrics = health_report['metrics']
            typer.echo(f"  CPU Usage: {metrics.get('cpu_percent', 0):.1f}%")
            typer.echo(f"  Memory Usage: {metrics.get('memory_percent', 0):.1f}%")
            typer.echo(f"  Disk Usage: {metrics.get('disk_percent', 0):.1f}%")
            typer.echo(f"  Active Connections: {metrics.get('connections', 0)}")
        
        # Recommendations
        if health_report.get('recommendations'):
            typer.echo(f"\n💡 Recommendations:")
            for rec in health_report['recommendations']:
                typer.echo(f"  • {rec}")
        
    except ImportError:
        typer.secho("⚠️  Health checker not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error checking system health: {e}", fg=typer.colors.RED)

@app.command()
def monitor():
    """Real-time system monitoring"""
    try:
        from eafix.gui.enhanced.monitoring_tiles import MonitoringTileManager
        import time
        
        typer.secho("📊 Real-time System Monitor", fg=typer.colors.BLUE, bold=True)
        typer.echo("Press Ctrl+C to stop monitoring")
        typer.echo("-" * 40)
        
        tile_manager = MonitoringTileManager()
        
        while True:
            # Clear screen (basic approach)
            typer.echo("\n" * 2)
            
            # Get current metrics
            tiles = tile_manager.get_all_tile_data()
            
            for category, category_tiles in tiles.items():
                typer.secho(f"\n{category.upper()}", fg=typer.colors.CYAN, bold=True)
                typer.echo("-" * 20)
                
                for tile_name, tile_data in category_tiles.items():
                    value = tile_data.get('value', 'N/A')
                    status = tile_data.get('status', 'unknown')
                    
                    if status == 'healthy':
                        typer.secho(f"  ✅ {tile_name}: {value}", fg=typer.colors.GREEN)
                    elif status == 'warning':
                        typer.secho(f"  ⚠️  {tile_name}: {value}", fg=typer.colors.YELLOW)
                    else:
                        typer.secho(f"  ❌ {tile_name}: {value}", fg=typer.colors.RED)
            
            typer.echo(f"\n🕐 Last Update: {datetime.now().strftime('%H:%M:%S')}")
            time.sleep(5)  # Update every 5 seconds
        
    except KeyboardInterrupt:
        typer.secho("\n⏹️  Monitoring stopped", fg=typer.colors.YELLOW)
    except ImportError:
        typer.secho("⚠️  Monitoring tiles not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error during monitoring: {e}", fg=typer.colors.RED)

@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Configuration key to view/set"),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Value to set for the key"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults")
):
    """Manage system configuration"""
    try:
        config_file = Path("settings.json")
        
        if not config_file.exists():
            typer.secho("❌ Configuration file not found", fg=typer.colors.RED)
            return
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if reset:
            confirm = typer.confirm("⚠️  Reset configuration to defaults?")
            if confirm:
                # Create backup
                backup_file = f"settings_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                typer.secho(f"📁 Backup saved to {backup_file}", fg=typer.colors.BLUE)
                typer.secho("🔄 Configuration reset (restart required)", fg=typer.colors.GREEN)
            return
        
        if key and value:
            # Set configuration value
            keys = key.split('.')
            current = config
            
            # Navigate to parent
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            # Set value (try to parse as JSON for complex types)
            try:
                current[keys[-1]] = json.loads(value)
            except json.JSONDecodeError:
                current[keys[-1]] = value
            
            # Save configuration
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            typer.secho(f"✅ Configuration updated: {key} = {value}", fg=typer.colors.GREEN)
            return
        
        if key:
            # Get specific configuration value
            keys = key.split('.')
            current = config
            
            try:
                for k in keys:
                    current = current[k]
                
                typer.secho(f"🔑 {key}:", fg=typer.colors.BLUE, bold=True)
                if isinstance(current, dict):
                    typer.echo(json.dumps(current, indent=2))
                else:
                    typer.echo(f"  {current}")
            except KeyError:
                typer.secho(f"❌ Configuration key '{key}' not found", fg=typer.colors.RED)
            return
        
        if show:
            # Show all configuration
            typer.secho("⚙️  System Configuration", fg=typer.colors.BLUE, bold=True)
            typer.echo("-" * 40)
            typer.echo(json.dumps(config, indent=2))
        
    except Exception as e:
        typer.secho(f"❌ Error managing configuration: {e}", fg=typer.colors.RED)

@app.command()
def logs(
    tail: int = typer.Option(50, "--tail", "-n", help="Number of recent log entries to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log file (tail -f behavior)"),
    level: Optional[str] = typer.Option(None, "--level", help="Filter by log level (INFO, WARNING, ERROR)")
):
    """View system logs"""
    try:
        import glob
        
        # Find log files
        log_patterns = [
            "*.log",
            "logs/*.log", 
            "production_validation_*.log"
        ]
        
        log_files = []
        for pattern in log_patterns:
            log_files.extend(glob.glob(pattern))
        
        if not log_files:
            typer.secho("📭 No log files found", fg=typer.colors.YELLOW)
            return
        
        # Use the most recent log file
        latest_log = max(log_files, key=lambda f: Path(f).stat().st_mtime)
        
        typer.secho(f"📄 System Logs: {latest_log}", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 50)
        
        if follow:
            typer.echo("Press Ctrl+C to stop following logs")
            import subprocess
            
            cmd = ["tail", "-f", latest_log]
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                typer.secho("\n⏹️  Stopped following logs", fg=typer.colors.YELLOW)
        else:
            with open(latest_log, 'r') as f:
                lines = f.readlines()
            
            # Apply level filter
            if level:
                level_upper = level.upper()
                lines = [line for line in lines if level_upper in line]
            
            # Show tail number of lines
            recent_lines = lines[-tail:]
            
            for line in recent_lines:
                line = line.strip()
                if 'ERROR' in line:
                    typer.secho(line, fg=typer.colors.RED)
                elif 'WARNING' in line:
                    typer.secho(line, fg=typer.colors.YELLOW)
                elif 'INFO' in line:
                    typer.secho(line, fg=typer.colors.BLUE)
                else:
                    typer.echo(line)
        
    except Exception as e:
        typer.secho(f"❌ Error reading logs: {e}", fg=typer.colors.RED)

@app.command()
def backup():
    """Create system backup"""
    try:
        import shutil
        import zipfile
        
        backup_name = f"eafix_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        typer.secho(f"💾 Creating system backup: {backup_name}", fg=typer.colors.BLUE)
        
        # Files and directories to backup
        backup_items = [
            "settings.json",
            "*.db",
            "*.log",
            "src/eafix/",
            "core/",
            "tabs/"
        ]
        
        with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pattern in backup_items:
                if '*' in pattern:
                    # Glob pattern
                    import glob
                    for file in glob.glob(pattern):
                        if Path(file).exists():
                            zipf.write(file)
                            typer.echo(f"  ✅ Added: {file}")
                else:
                    # Direct file/directory
                    path = Path(pattern)
                    if path.exists():
                        if path.is_file():
                            zipf.write(path)
                            typer.echo(f"  ✅ Added: {path}")
                        elif path.is_dir():
                            for file in path.rglob("*"):
                                if file.is_file():
                                    zipf.write(file)
                            typer.echo(f"  ✅ Added directory: {path}")
        
        backup_size = Path(backup_name).stat().st_size / (1024*1024)  # MB
        typer.secho(f"✅ Backup created: {backup_name} ({backup_size:.1f} MB)", 
                   fg=typer.colors.GREEN, bold=True)
        
    except Exception as e:
        typer.secho(f"❌ Error creating backup: {e}", fg=typer.colors.RED)