#!/usr/bin/env python3
"""
Main entry point for CLI Multi-Rapid GUI Terminal
"""

import sys
import os
import argparse
import logging
from pathlib import Path

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    PYQT_VERSION = 6
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        PYQT_VERSION = 5
    except ImportError:
        print("Error: PyQt6 or PyQt5 is required but not installed.")
        print("Install with: pip install PyQt6 or pip install PyQt5")
        sys.exit(1)

from .ui.main_window import MainWindow
from .config.settings import SettingsManager
from .security.policy_manager import SecurityPolicyManager
from .core.logging_config import setup_logging


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="CLI Multi-Rapid GUI Terminal - Enterprise Edition"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    parser.add_argument(
        "--security-policy",
        type=str,
        help="Path to security policy file"
    )
    parser.add_argument(
        "--no-security",
        action="store_true",
        help="Disable security policy enforcement (development only)"
    )
    parser.add_argument(
        "--command",
        type=str,
        help="Command to execute on startup"
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        help="Initial working directory"
    )
    return parser.parse_args()


def setup_application():
    """Setup QApplication with enterprise settings"""
    app = QApplication(sys.argv)
    app.setApplicationName("CLI Multi-Rapid GUI Terminal")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CLI Multi-Rapid")

    # Enable high DPI scaling
    if PYQT_VERSION == 6:
        app.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    else:
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    return app


def main():
    """Main application entry point"""
    args = parse_arguments()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting CLI Multi-Rapid GUI Terminal v1.0.0")

    try:
        # Setup QApplication
        app = setup_application()

        # Load configuration
        settings_manager = SettingsManager(config_path=args.config)

        # Setup security policy if enabled
        security_manager = None
        if not args.no_security:
            security_manager = SecurityPolicyManager(
                policy_path=args.security_policy
            )
            logger.info("Security policy enforcement enabled")
        else:
            logger.warning("Security policy enforcement DISABLED")

        # Create main window
        main_window = MainWindow(
            settings_manager=settings_manager,
            security_manager=security_manager
        )

        # Set initial command and working directory if provided
        if args.command or args.working_dir:
            main_window.set_startup_options(
                command=args.command,
                working_dir=args.working_dir
            )

        # Show main window
        main_window.show()

        # Start event loop
        logger.info("Application started successfully")
        return app.exec()

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0


if __name__ == "__main__":
    sys.exit(main())