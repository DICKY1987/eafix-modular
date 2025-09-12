"""
Cross-Language Bridge System
============================

Seamless Python↔MQL4↔PowerShell integration for the CLI Multi-Rapid framework.
Provides unified configuration propagation, health checking, and error handling.
"""

from .config_propagator import UnifiedConfigManager
from .health_checker import CrossSystemHealthChecker
from .error_handler import CrossLanguageErrorHandler
from .communication_bridge import CommunicationBridge

__all__ = [
    'UnifiedConfigManager',
    'CrossSystemHealthChecker', 
    'CrossLanguageErrorHandler',
    'CommunicationBridge'
]

__version__ = '1.0.0'