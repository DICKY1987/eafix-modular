"""
Logging configuration for DOC_ID system.

Provides centralized logging setup with:
- Console output (colored, level-based)
- File output (rotating logs)
- Configurable log levels
- Module-specific loggers
"""
# DOC_ID: DOC-CORE-COMMON-LOGGING-SETUP-1170

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import MODULE_ROOT


# Log directory
LOG_DIR = MODULE_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file path
LOG_FILE = LOG_DIR / "doc_id_system.log"

# Default format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
CONSOLE_FORMAT = "%(levelname)s - %(message)s"

# Log level mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    
    Uses ANSI color codes for different log levels.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
        "RESET": "\033[0m",       # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


def setup_logging(
    name: str = "doc_id",
    level: str = "INFO",
    console: bool = True,
    file: bool = True,
    colored: bool = True,
) -> logging.Logger:
    """
    Setup logging for a module.
    
    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console: Enable console output
        file: Enable file output
        colored: Use colored console output
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from common.logging_setup import setup_logging
        >>> logger = setup_logging(__name__)
        >>> logger.info("Starting scan...")
        >>> logger.warning("Found duplicate doc_id")
        >>> logger.error("Failed to load registry")
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVELS.get(level.upper(), logging.INFO))
        
        if colored:
            console_formatter = ColoredFormatter(CONSOLE_FORMAT)
        else:
            console_formatter = logging.Formatter(CONSOLE_FORMAT)
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler (rotating)
    if file:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_formatter = logging.Formatter(DEFAULT_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get or create a logger for a module.
    
    Convenience function for consistent logger creation.
    
    Args:
        name: Logger name (use __name__)
        level: Log level
        
    Returns:
        Logger instance
    """
    return setup_logging(name, level=level)


# Default logger for the common module
logger = setup_logging("doc_id.common", level="INFO")
