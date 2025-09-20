"""
CLI Utility Functions
Cross-platform utility functions for the CLI
"""

import sys
import os


def safe_print(text, color=None, bold=False):
    """Print text safely across different terminals and encodings"""
    try:
        if color or bold:
            import typer
            typer.secho(text, fg=color, bold=bold)
        else:
            print(text)
    except UnicodeEncodeError:
        # Fallback for terminals that don't support Unicode
        # Replace Unicode symbols with ASCII equivalents
        ascii_text = text.replace('✅', '[OK]').replace('❌', '[ERROR]').replace('⚠️', '[WARN]')
        ascii_text = ascii_text.replace('🟢', '[OK]').replace('🔴', '[ERROR]').replace('🟡', '[WARN]')
        ascii_text = ascii_text.replace('📊', '[CHART]').replace('💰', '[MONEY]').replace('🛡️', '[GUARD]')
        ascii_text = ascii_text.replace('🎉', '[SUCCESS]').replace('💾', '[DISK]').replace('🔧', '[TOOL]')
        ascii_text = ascii_text.replace('📦', '[PACKAGE]').replace('🚀', '[LAUNCH]').replace('🧪', '[TEST]')
        ascii_text = ascii_text.replace('🏥', '[HEALTH]').replace('⏹️', '[STOP]').replace('📁', '[FILE]')
        
        if color or bold:
            import typer
            typer.secho(ascii_text, fg=color, bold=bold)
        else:
            print(ascii_text)


def safe_echo(text, color=None, bold=False):
    """Typer echo wrapper with encoding safety"""
    try:
        import typer
        if color or bold:
            typer.secho(text, fg=color, bold=bold)
        else:
            typer.echo(text)
    except UnicodeEncodeError:
        safe_print(text, color, bold)


def configure_console():
    """Configure console for better Unicode support on Windows"""
    if sys.platform.startswith('win'):
        try:
            # Try to enable UTF-8 mode on Windows
            os.system('chcp 65001 >nul 2>&1')
            # Set console output encoding
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass  # Fall back to ASCII-safe output