"""
Trading Commands Module
CLI commands for trading operations, signals, and position management
"""

import typer
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

app = typer.Typer(help="Trading operations and signal management")

@app.command()
def signals(
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="Currency pair symbol (e.g., EURUSD)"),
    active_only: bool = typer.Option(False, "--active", "-a", help="Show only active signals"),
    export: bool = typer.Option(False, "--export", "-e", help="Export signals to JSON")
):
    """List and manage trading signals"""
    try:
        from eafix.signals.friday_vol_signal import FridayVolSignal
        from eafix.signals.conditional_signals import ConditionalSignalProcessor
        
        typer.secho("📊 Trading Signals Analysis", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        # Friday Vol Signal
        friday_signal = FridayVolSignal()
        if symbol:
            signals = friday_signal.get_signals_for_symbol(symbol)
            typer.echo(f"\n🎯 Friday Vol Signals for {symbol}:")
        else:
            signals = friday_signal.get_all_active_signals()
            typer.echo(f"\n🎯 All Friday Vol Signals:")
        
        for signal in signals:
            status = "🟢 ACTIVE" if signal.get('active', False) else "🔴 INACTIVE"
            typer.echo(f"  {status} {signal.get('symbol', 'N/A')} - {signal.get('signal_type', 'N/A')}")
            typer.echo(f"    Strength: {signal.get('strength', 0):.2f}")
            typer.echo(f"    Timestamp: {signal.get('timestamp', 'N/A')}")
        
        # Conditional Signals
        conditional = ConditionalSignalProcessor()
        cond_signals = conditional.get_active_signals()
        
        typer.echo(f"\n🎲 Conditional Signals ({len(cond_signals)} active):")
        for signal in cond_signals:
            typer.echo(f"  📈 {signal.get('condition', 'N/A')} -> {signal.get('action', 'N/A')}")
        
        if export:
            import json
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'friday_vol_signals': signals,
                'conditional_signals': cond_signals
            }
            filename = f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            typer.secho(f"📁 Signals exported to {filename}", fg=typer.colors.GREEN)
            
    except ImportError as e:
        typer.secho(f"⚠️  Signal modules not available: {e}", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error retrieving signals: {e}", fg=typer.colors.RED)

@app.command()
def positions(
    symbol: Optional[str] = typer.Option(None, "--symbol", "-s", help="Filter by currency pair"),
    close_all: bool = typer.Option(False, "--close-all", help="Close all positions (requires confirmation)")
):
    """View and manage trading positions"""
    try:
        from core.ea_connector import EAConnector
        
        connector = EAConnector()
        positions = connector.get_positions()
        
        typer.secho("💼 Current Trading Positions", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if not positions:
            typer.secho("📭 No open positions", fg=typer.colors.YELLOW)
            return
        
        filtered_positions = positions
        if symbol:
            filtered_positions = [p for p in positions if p.get('symbol') == symbol.upper()]
        
        total_pnl = 0
        for pos in filtered_positions:
            pnl = pos.get('profit', 0)
            total_pnl += pnl
            
            pnl_color = typer.colors.GREEN if pnl >= 0 else typer.colors.RED
            pnl_symbol = "📈" if pnl >= 0 else "📉"
            
            typer.echo(f"{pnl_symbol} {pos.get('symbol', 'N/A')} - {pos.get('type', 'N/A')}")
            typer.echo(f"   Size: {pos.get('lots', 0):.2f}")
            typer.echo(f"   Entry: {pos.get('open_price', 0):.5f}")
            typer.echo(f"   Current: {pos.get('current_price', 0):.5f}")
            typer.secho(f"   P&L: ${pnl:.2f}", fg=pnl_color)
            typer.echo("")
        
        total_color = typer.colors.GREEN if total_pnl >= 0 else typer.colors.RED
        typer.secho(f"💰 Total P&L: ${total_pnl:.2f}", fg=total_color, bold=True)
        
        if close_all and filtered_positions:
            confirm = typer.confirm("⚠️  Are you sure you want to close all positions?")
            if confirm:
                closed = connector.close_all_positions()
                typer.secho(f"✅ Closed {closed} positions", fg=typer.colors.GREEN)
            
    except ImportError:
        typer.secho("⚠️  EA Connector not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error managing positions: {e}", fg=typer.colors.RED)

@app.command()
def start():
    """Start automated trading"""
    try:
        from core.app_controller import AppController
        
        controller = AppController()
        
        typer.echo("🚀 Starting automated trading...")
        result = controller.start_trading()
        
        if result:
            typer.secho("✅ Automated trading started successfully", fg=typer.colors.GREEN)
        else:
            typer.secho("❌ Failed to start trading", fg=typer.colors.RED)
            
    except ImportError:
        typer.secho("⚠️  App Controller not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error starting trading: {e}", fg=typer.colors.RED)

@app.command()
def stop():
    """Stop automated trading"""
    try:
        from core.app_controller import AppController
        
        controller = AppController()
        
        confirm = typer.confirm("⚠️  Stop all automated trading?")
        if confirm:
            typer.echo("⏹️  Stopping automated trading...")
            result = controller.stop_trading()
            
            if result:
                typer.secho("✅ Automated trading stopped", fg=typer.colors.GREEN)
            else:
                typer.secho("❌ Failed to stop trading", fg=typer.colors.RED)
        
    except ImportError:
        typer.secho("⚠️  App Controller not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error stopping trading: {e}", fg=typer.colors.RED)

@app.command()
def calendar():
    """Show economic calendar events"""
    try:
        from eafix.economic_calendar import EconomicCalendarProcessor
        
        processor = EconomicCalendarProcessor()
        events = processor.get_todays_events()
        
        typer.secho("📅 Today's Economic Calendar", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if not events:
            typer.secho("📭 No major events today", fg=typer.colors.YELLOW)
            return
        
        for event in events:
            impact_color = {
                'high': typer.colors.RED,
                'medium': typer.colors.YELLOW, 
                'low': typer.colors.GREEN
            }.get(event.get('impact', 'low').lower(), typer.colors.WHITE)
            
            impact_symbol = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(event.get('impact', 'low').lower(), '⚪')
            
            typer.echo(f"{impact_symbol} {event.get('time', 'N/A')} - {event.get('currency', 'N/A')}")
            typer.secho(f"   {event.get('event', 'N/A')}", fg=impact_color)
            if event.get('forecast'):
                typer.echo(f"   Forecast: {event['forecast']}")
            typer.echo("")
            
    except ImportError:
        typer.secho("⚠️  Economic calendar not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error loading calendar: {e}", fg=typer.colors.RED)