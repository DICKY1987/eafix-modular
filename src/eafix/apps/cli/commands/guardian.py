"""
Guardian System Commands Module
CLI commands for Guardian protection system management and monitoring
"""

import typer
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

app = typer.Typer(help="Guardian protection system management")

@app.command()
def status():
    """Show Guardian system status and active constraints"""
    try:
        from eafix.guardian.constraints import ConstraintRepository
        from eafix.guardian.agents import RiskAgent, MarketAgent, SystemAgent
        
        typer.secho("🛡️  Guardian Protection System Status", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 50)
        
        # Constraint Repository Status
        repo = ConstraintRepository()
        constraints = repo.get_active_constraints()
        
        typer.echo(f"📋 Active Constraints: {len(constraints)}")
        for constraint in constraints[:10]:  # Show first 10
            status_icon = "🟢" if constraint.get('enabled', False) else "🔴"
            typer.echo(f"  {status_icon} {constraint.get('name', 'N/A')} - {constraint.get('type', 'N/A')}")
        
        if len(constraints) > 10:
            typer.echo(f"  ... and {len(constraints) - 10} more")
        
        # Agent Status
        typer.echo(f"\n🤖 Guardian Agents:")
        agents = [
            ("Risk Agent", RiskAgent()),
            ("Market Agent", MarketAgent()),
            ("System Agent", SystemAgent())
        ]
        
        for name, agent in agents:
            try:
                agent_status = agent.get_status()
                health_icon = "🟢" if agent_status.get('healthy', False) else "🟡"
                typer.echo(f"  {health_icon} {name}: {agent_status.get('status', 'Unknown')}")
            except Exception as e:
                typer.echo(f"  🔴 {name}: Error - {e}")
        
    except ImportError:
        typer.secho("⚠️  Guardian system not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error checking Guardian status: {e}", fg=typer.colors.RED)

@app.command()
def constraints(
    enable: Optional[str] = typer.Option(None, "--enable", help="Enable constraint by name"),
    disable: Optional[str] = typer.Option(None, "--disable", help="Disable constraint by name"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all constraints")
):
    """Manage Guardian constraints"""
    try:
        from eafix.guardian.constraints import ConstraintRepository
        
        repo = ConstraintRepository()
        
        if enable:
            success = repo.enable_constraint(enable)
            if success:
                typer.secho(f"✅ Constraint '{enable}' enabled", fg=typer.colors.GREEN)
            else:
                typer.secho(f"❌ Failed to enable constraint '{enable}'", fg=typer.colors.RED)
            return
        
        if disable:
            success = repo.disable_constraint(disable)
            if success:
                typer.secho(f"⚠️  Constraint '{disable}' disabled", fg=typer.colors.YELLOW)
            else:
                typer.secho(f"❌ Failed to disable constraint '{disable}'", fg=typer.colors.RED)
            return
        
        # List constraints
        constraints = repo.get_all_constraints() if list_all else repo.get_active_constraints()
        
        title = "All Constraints" if list_all else "Active Constraints"
        typer.secho(f"📋 {title}", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if not constraints:
            typer.secho("📭 No constraints found", fg=typer.colors.YELLOW)
            return
        
        for constraint in constraints:
            status_icon = "🟢" if constraint.get('enabled', False) else "🔴"
            typer.echo(f"{status_icon} {constraint.get('name', 'N/A')}")
            typer.echo(f"   Type: {constraint.get('type', 'N/A')}")
            typer.echo(f"   Description: {constraint.get('description', 'No description')}")
            
            if constraint.get('last_triggered'):
                typer.echo(f"   Last Triggered: {constraint['last_triggered']}")
            typer.echo("")
        
    except ImportError:
        typer.secho("⚠️  Guardian constraints not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error managing constraints: {e}", fg=typer.colors.RED)

@app.command()
def gates():
    """Check Guardian gate system status"""
    try:
        from eafix.guardian.gates import (
            BrokerConnectivityGate,
            MarketQualityGate,
            RiskManagementGate,
            SystemHealthGate
        )
        
        typer.secho("🚪 Guardian Gate System Status", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        gates = [
            ("Broker Connectivity", BrokerConnectivityGate()),
            ("Market Quality", MarketQualityGate()),
            ("Risk Management", RiskManagementGate()),
            ("System Health", SystemHealthGate())
        ]
        
        all_open = True
        
        for name, gate in gates:
            try:
                is_open = gate.is_open()
                gate_status = gate.get_status()
                
                if is_open:
                    typer.secho(f"🟢 {name}: OPEN", fg=typer.colors.GREEN)
                else:
                    typer.secho(f"🔴 {name}: CLOSED", fg=typer.colors.RED)
                    all_open = False
                
                # Show gate details
                if gate_status.get('details'):
                    for detail in gate_status['details'][:3]:  # Show first 3 details
                        typer.echo(f"   • {detail}")
                        
            except Exception as e:
                typer.secho(f"🔴 {name}: ERROR - {e}", fg=typer.colors.RED)
                all_open = False
        
        typer.echo("-" * 40)
        if all_open:
            typer.secho("✅ All gates are OPEN - Trading allowed", fg=typer.colors.GREEN, bold=True)
        else:
            typer.secho("❌ Some gates are CLOSED - Trading restricted", fg=typer.colors.RED, bold=True)
        
    except ImportError:
        typer.secho("⚠️  Guardian gates not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error checking gates: {e}", fg=typer.colors.RED)

@app.command()
def alerts():
    """Show recent Guardian alerts and violations"""
    try:
        from eafix.guardian.monitoring import AlertManager
        
        alert_manager = AlertManager()
        recent_alerts = alert_manager.get_recent_alerts(limit=20)
        
        typer.secho("🚨 Recent Guardian Alerts", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if not recent_alerts:
            typer.secho("✅ No recent alerts", fg=typer.colors.GREEN)
            return
        
        for alert in recent_alerts:
            severity = alert.get('severity', 'info').lower()
            
            if severity == 'critical':
                icon, color = "🔴", typer.colors.RED
            elif severity == 'warning':
                icon, color = "🟡", typer.colors.YELLOW
            elif severity == 'info':
                icon, color = "🔵", typer.colors.BLUE
            else:
                icon, color = "⚪", typer.colors.WHITE
            
            typer.secho(f"{icon} {alert.get('timestamp', 'N/A')}", fg=color)
            typer.echo(f"   {alert.get('message', 'No message')}")
            
            if alert.get('constraint'):
                typer.echo(f"   Constraint: {alert['constraint']}")
            
            if alert.get('action_taken'):
                typer.echo(f"   Action: {alert['action_taken']}")
            
            typer.echo("")
        
    except ImportError:
        typer.secho("⚠️  Guardian monitoring not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error retrieving alerts: {e}", fg=typer.colors.RED)

@app.command()
def emergency():
    """Emergency Guardian controls"""
    try:
        from eafix.gui.enhanced.emergency_controls import EmergencyControlsPanel
        
        typer.secho("🚨 EMERGENCY GUARDIAN CONTROLS", fg=typer.colors.RED, bold=True)
        typer.echo("-" * 50)
        
        typer.echo("Available emergency actions:")
        typer.echo("1. 🛑 STOP ALL - Stop all trading immediately")
        typer.echo("2. ⏸️  PAUSE - Pause trading decisions")
        typer.echo("3. 📊 FLATTEN - Close all positions")
        typer.echo("4. 🔄 RESUME - Resume normal operations")
        
        action = typer.prompt("Select emergency action (1-4)")
        
        controls = EmergencyControlsPanel()
        
        if action == "1":
            confirm = typer.confirm("⚠️  STOP ALL TRADING - Are you sure?")
            if confirm:
                controls.emergency_stop()
                typer.secho("🛑 ALL TRADING STOPPED", fg=typer.colors.RED, bold=True)
        
        elif action == "2":
            controls.pause_decisions()
            typer.secho("⏸️  Trading decisions PAUSED", fg=typer.colors.YELLOW, bold=True)
        
        elif action == "3":
            confirm = typer.confirm("⚠️  FLATTEN ALL POSITIONS - Are you sure?")
            if confirm:
                result = controls.flatten_all_positions()
                typer.secho(f"📊 {result.get('closed_positions', 0)} positions closed", 
                          fg=typer.colors.YELLOW, bold=True)
        
        elif action == "4":
            controls.resume_operations()
            typer.secho("🔄 Operations RESUMED", fg=typer.colors.GREEN, bold=True)
        
        else:
            typer.secho("❌ Invalid selection", fg=typer.colors.RED)
        
    except ImportError:
        typer.secho("⚠️  Emergency controls not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error executing emergency action: {e}", fg=typer.colors.RED)