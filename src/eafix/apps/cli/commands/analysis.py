"""
Analysis Commands Module
CLI commands for market analysis, reporting, and data processing
"""

import typer
import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

app = typer.Typer(help="Market analysis and reporting tools")

@app.command()
def currency_strength(
    timeframe: str = typer.Option("1H", "--timeframe", "-t", help="Timeframe (15M, 1H, 4H, 1D)"),
    export: bool = typer.Option(False, "--export", "-e", help="Export results to JSON"),
    top: int = typer.Option(8, "--top", help="Number of currencies to show")
):
    """Analyze currency strength across major pairs"""
    try:
        from eafix.currency_strength import CurrencyStrengthAnalyzer
        
        typer.secho("💪 Currency Strength Analysis", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        analyzer = CurrencyStrengthAnalyzer()
        strength_data = analyzer.calculate_strength(timeframe=timeframe)
        
        # Sort by strength
        sorted_currencies = sorted(strength_data.items(), key=lambda x: x[1], reverse=True)
        
        typer.echo(f"📊 Currency strength for {timeframe} timeframe:")
        typer.echo("")
        
        for i, (currency, strength) in enumerate(sorted_currencies[:top]):
            if strength > 60:
                color = typer.colors.GREEN
                icon = "💪"
            elif strength > 40:
                color = typer.colors.YELLOW
                icon = "👍"
            else:
                color = typer.colors.RED
                icon = "👎"
            
            rank = i + 1
            typer.secho(f"{icon} #{rank} {currency}: {strength:.1f}%", fg=color)
        
        if export:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'timeframe': timeframe,
                'currency_strength': dict(sorted_currencies)
            }
            filename = f"currency_strength_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            typer.secho(f"📁 Analysis exported to {filename}", fg=typer.colors.GREEN)
        
    except ImportError:
        typer.secho("⚠️  Currency strength analyzer not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error analyzing currency strength: {e}", fg=typer.colors.RED)

@app.command()
def positioning(
    source: str = typer.Option("cot", "--source", "-s", help="Data source (cot, sentiment, combined)"),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Specific currency to analyze")
):
    """Analyze institutional positioning and sentiment"""
    try:
        typer.secho("🏛️  Institutional Positioning Analysis", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 50)
        
        if source in ["cot", "combined"]:
            from eafix.positioning.cftc.cot_processor import CFTCCOTProcessor
            
            typer.echo("📊 CFTC Commitment of Traders Data:")
            cot_processor = CFTCCOTProcessor()
            cot_data = cot_processor.get_latest_positioning()
            
            for currency_data in cot_data:
                curr = currency_data.get('currency', 'N/A')
                if currency and curr.upper() != currency.upper():
                    continue
                
                net_long = currency_data.get('net_long_percentage', 0)
                
                if net_long > 70:
                    icon, color = "📈", typer.colors.GREEN
                elif net_long < 30:
                    icon, color = "📉", typer.colors.RED
                else:
                    icon, color = "➡️", typer.colors.YELLOW
                
                typer.secho(f"{icon} {curr}: {net_long:.1f}% net long", fg=color)
                
                # Show contrarian signals
                if currency_data.get('contrarian_signal'):
                    typer.secho(f"   🔄 Contrarian Signal: {currency_data['contrarian_signal']}", 
                              fg=typer.colors.MAGENTA)
        
        if source in ["sentiment", "combined"]:
            from eafix.positioning.retail.sentiment_aggregator import SentimentAggregator
            
            typer.echo("\n👥 Retail Sentiment Analysis:")
            sentiment_agg = SentimentAggregator()
            sentiment_data = sentiment_agg.get_aggregated_sentiment()
            
            for pair_data in sentiment_data:
                pair = pair_data.get('pair', 'N/A')
                if currency and currency.upper() not in pair.upper():
                    continue
                
                sentiment = pair_data.get('sentiment_score', 50)
                
                if sentiment > 70:
                    icon, color = "😄", typer.colors.GREEN
                elif sentiment < 30:
                    icon, color = "😟", typer.colors.RED
                else:
                    icon, color = "😐", typer.colors.YELLOW
                
                typer.secho(f"{icon} {pair}: {sentiment:.1f}% bullish sentiment", fg=color)
                
                # Show extreme sentiment warnings
                if pair_data.get('extreme_sentiment'):
                    typer.secho(f"   ⚠️  Extreme sentiment detected", fg=typer.colors.RED)
        
    except ImportError:
        typer.secho("⚠️  Positioning analysis modules not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error analyzing positioning: {e}", fg=typer.colors.RED)

@app.command()
def indicators(
    symbol: str = typer.Argument(..., help="Currency pair symbol (e.g., EURUSD)"),
    timeframe: str = typer.Option("1H", "--timeframe", "-t", help="Chart timeframe"),
    indicator_type: Optional[str] = typer.Option(None, "--type", help="Specific indicator type")
):
    """Calculate and display technical indicators"""
    try:
        from eafix.indicators.advanced.rate_differential import RateDifferentialMomentum
        from eafix.indicators.advanced.volatility_spillover import VolatilitySpilloverAnalysis
        
        typer.secho(f"📈 Technical Indicators for {symbol.upper()}", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        if indicator_type is None or indicator_type == "rate_differential":
            typer.echo("💹 Rate Differential Momentum:")
            rdm = RateDifferentialMomentum(symbol)
            rdm_data = rdm.calculate()
            
            momentum = rdm_data.get('momentum', 0)
            if momentum > 0.5:
                typer.secho(f"   📈 Momentum: {momentum:.3f} (Strong Bullish)", fg=typer.colors.GREEN)
            elif momentum < -0.5:
                typer.secho(f"   📉 Momentum: {momentum:.3f} (Strong Bearish)", fg=typer.colors.RED)
            else:
                typer.secho(f"   ➡️  Momentum: {momentum:.3f} (Neutral)", fg=typer.colors.YELLOW)
            
            if rdm_data.get('signal'):
                typer.echo(f"   🎯 Signal: {rdm_data['signal']}")
        
        if indicator_type is None or indicator_type == "volatility_spillover":
            typer.echo("\n🌊 Volatility Spillover Analysis:")
            vsa = VolatilitySpilloverAnalysis([symbol])
            vsa_data = vsa.analyze_spillover_effects()
            
            if symbol in vsa_data:
                spillover = vsa_data[symbol]
                
                received = spillover.get('spillover_received', 0)
                transmitted = spillover.get('spillover_transmitted', 0)
                
                typer.echo(f"   📥 Spillover Received: {received:.1f}%")
                typer.echo(f"   📤 Spillover Transmitted: {transmitted:.1f}%")
                
                if received > 50:
                    typer.secho("   ⚠️  High volatility influence from other pairs", fg=typer.colors.YELLOW)
        
        # Standard indicators
        typer.echo("\n📊 Standard Indicators:")
        
        # This would connect to your existing indicator system
        # For now, showing placeholder structure
        indicators_data = {
            'RSI': 45.2,
            'MACD': 0.0015,
            'Stochastic': 38.7,
            'Z-Score': -1.2
        }
        
        for indicator, value in indicators_data.items():
            if indicator == 'RSI':
                if value > 70:
                    color = typer.colors.RED
                elif value < 30:
                    color = typer.colors.GREEN
                else:
                    color = typer.colors.YELLOW
            else:
                color = typer.colors.WHITE
            
            typer.secho(f"   {indicator}: {value}", fg=color)
        
    except ImportError:
        typer.secho("⚠️  Advanced indicators not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error calculating indicators: {e}", fg=typer.colors.RED)

@app.command()
def report(
    report_type: str = typer.Argument(..., help="Report type (daily, weekly, monthly, custom)"),
    start_date: Optional[str] = typer.Option(None, "--start", help="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end", help="End date (YYYY-MM-DD)"),
    format: str = typer.Option("console", "--format", "-f", help="Output format (console, json, html)")
):
    """Generate comprehensive analysis reports"""
    try:
        from datetime import datetime, timedelta
        
        # Determine date range
        if report_type == "daily":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=1)
        elif report_type == "weekly":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(weeks=1)
        elif report_type == "monthly":
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=30)
        elif report_type == "custom":
            if not start_date or not end_date:
                typer.secho("❌ Custom reports require --start and --end dates", fg=typer.colors.RED)
                return
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            typer.secho(f"❌ Unknown report type: {report_type}", fg=typer.colors.RED)
            return
        
        typer.secho(f"📄 {report_type.title()} Analysis Report", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"Period: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
        typer.echo("-" * 50)
        
        # Generate report sections
        report_data = {
            'report_type': report_type,
            'period': {
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat()
            },
            'generated_at': datetime.now().isoformat()
        }
        
        # Trading Performance Summary
        typer.echo("💰 Trading Performance:")
        # This would integrate with your actual trading history
        perf_data = {
            'total_trades': 47,
            'winning_trades': 28,
            'losing_trades': 19,
            'win_rate': 59.6,
            'total_pnl': 2847.50,
            'avg_trade': 60.59
        }
        
        report_data['performance'] = perf_data
        
        typer.echo(f"   Total Trades: {perf_data['total_trades']}")
        win_rate_color = typer.colors.GREEN if perf_data['win_rate'] > 50 else typer.colors.RED
        typer.secho(f"   Win Rate: {perf_data['win_rate']:.1f}%", fg=win_rate_color)
        pnl_color = typer.colors.GREEN if perf_data['total_pnl'] > 0 else typer.colors.RED
        typer.secho(f"   Total P&L: ${perf_data['total_pnl']:.2f}", fg=pnl_color)
        
        # Market Activity Summary
        typer.echo("\n📊 Market Activity:")
        activity_data = {
            'most_traded_pair': 'EURUSD',
            'highest_volatility': 'GBPJPY',
            'strongest_currency': 'USD',
            'weakest_currency': 'JPY'
        }
        report_data['market_activity'] = activity_data
        
        for key, value in activity_data.items():
            typer.echo(f"   {key.replace('_', ' ').title()}: {value}")
        
        # Guardian System Summary
        typer.echo("\n🛡️  Guardian System:")
        guardian_data = {
            'total_alerts': 12,
            'critical_alerts': 2,
            'constraints_triggered': 8,
            'emergency_actions': 0
        }
        report_data['guardian'] = guardian_data
        
        for key, value in guardian_data.items():
            color = typer.colors.RED if 'critical' in key or 'emergency' in key else typer.colors.BLUE
            typer.secho(f"   {key.replace('_', ' ').title()}: {value}", fg=color)
        
        # Save report if requested
        if format == "json":
            filename = f"analysis_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            typer.secho(f"\n📁 Report saved to {filename}", fg=typer.colors.GREEN)
        
        elif format == "html":
            filename = f"analysis_report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head><title>{report_type.title()} Analysis Report</title></head>
            <body>
            <h1>{report_type.title()} Analysis Report</h1>
            <p>Period: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}</p>
            <pre>{json.dumps(report_data, indent=2)}</pre>
            </body>
            </html>
            """
            with open(filename, 'w') as f:
                f.write(html_content)
            typer.secho(f"\n📁 HTML report saved to {filename}", fg=typer.colors.GREEN)
        
    except Exception as e:
        typer.secho(f"❌ Error generating report: {e}", fg=typer.colors.RED)

@app.command()
def scan():
    """Scan for trading opportunities and market inefficiencies"""
    try:
        typer.secho("🔍 Market Opportunity Scanner", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 40)
        
        # This would integrate with your various scanning tools
        from tools.trading_framework_scan import TradingFrameworkScanner
        
        scanner = TradingFrameworkScanner()
        opportunities = scanner.scan_for_opportunities()
        
        if not opportunities:
            typer.secho("📭 No significant opportunities detected", fg=typer.colors.YELLOW)
            return
        
        for opp in opportunities:
            confidence = opp.get('confidence', 0)
            
            if confidence > 80:
                icon, color = "🟢", typer.colors.GREEN
            elif confidence > 60:
                icon, color = "🟡", typer.colors.YELLOW
            else:
                icon, color = "🔴", typer.colors.RED
            
            typer.secho(f"{icon} {opp.get('type', 'N/A')} - {opp.get('symbol', 'N/A')}", fg=color)
            typer.echo(f"   Confidence: {confidence}%")
            typer.echo(f"   Description: {opp.get('description', 'N/A')}")
            
            if opp.get('action'):
                typer.echo(f"   Suggested Action: {opp['action']}")
            typer.echo("")
        
    except ImportError:
        typer.secho("⚠️  Market scanner not available", fg=typer.colors.YELLOW)
    except Exception as e:
        typer.secho(f"❌ Error scanning market: {e}", fg=typer.colors.RED)