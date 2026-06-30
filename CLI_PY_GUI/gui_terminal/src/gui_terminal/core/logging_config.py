"""
Logging Configuration for CLI Multi-Rapid GUI Terminal
Enterprise-grade structured logging with audit trails
"""

import os
import json
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import hashlib


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for development"""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')

        # Format message
        message = record.getMessage()

        return f"{color}[{timestamp}] {record.levelname:8} {record.name:20} {message}{reset}"


class AuditLogHandler(logging.Handler):
    """Custom handler for audit logging with integrity verification"""

    def __init__(self, audit_file: str):
        super().__init__()
        self.audit_file = Path(audit_file)
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record):
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'audit',
                'level': record.levelname,
                'message': record.getMessage()
            }

            # Add extra audit data if available
            if hasattr(record, 'audit_data'):
                audit_entry.update(record.audit_data)

            # Calculate integrity hash
            entry_string = json.dumps(audit_entry, sort_keys=True)
            integrity_hash = hashlib.sha256(entry_string.encode()).hexdigest()
            audit_entry['integrity_hash'] = integrity_hash

            # Write to audit file
            with open(self.audit_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(audit_entry) + '\n')

        except Exception:
            self.handleError(record)


class StructuredLogger:
    """
    Enterprise-grade structured logging with audit capabilities
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        self.logger = logging.getLogger(name)
        self.config = config
        self.setup_handlers()

    def setup_handlers(self):
        """Setup logging handlers based on configuration"""
        # Clear existing handlers
        self.logger.handlers.clear()
        self.logger.setLevel(logging.DEBUG)

        # File handler for general logs
        if self.config.get('file_logging', {}).get('enabled', True):
            log_dir = Path(self.config.get('file_logging', {}).get('directory', 'logs'))
            log_dir.mkdir(exist_ok=True)

            log_file = log_dir / f"{self.logger.name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(JsonFormatter())
            self.logger.addHandler(file_handler)

        # Console handler for development
        if self.config.get('console_logging', {}).get('enabled', True):
            console_handler = logging.StreamHandler()
            console_level = self.config.get('console_logging', {}).get('level', 'INFO')
            console_handler.setLevel(getattr(logging, console_level))
            console_handler.setFormatter(ColoredFormatter())
            self.logger.addHandler(console_handler)

        # Audit handler for security events
        if self.config.get('audit_logging', {}).get('enabled', True):
            audit_file = self.config.get('audit_logging', {}).get('file', 'logs/audit.log')
            audit_handler = AuditLogHandler(audit_file)
            audit_handler.setLevel(logging.INFO)
            self.logger.addHandler(audit_handler)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra={'extra_data': kwargs})

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra={'extra_data': kwargs})

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra={'extra_data': kwargs})

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra={'extra_data': kwargs})

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, extra={'extra_data': kwargs})

    def audit(self, action: str, context: Dict[str, Any], result: str):
        """Log audit events with structured format"""
        audit_data = {
            'event_type': 'audit',
            'action': action,
            'context': context,
            'result': result,
            'user_id': context.get('user_id', 'system'),
            'session_id': context.get('session_id', 'system')
        }

        self.logger.info(f"AUDIT: {action}", extra={'audit_data': audit_data})

    def security(self, violation_type: str, command: str, details: Dict[str, Any]):
        """Log security events"""
        security_data = {
            'event_type': 'security',
            'violation_type': violation_type,
            'command': command,
            'details': details,
            'severity': details.get('severity', 'medium')
        }

        self.logger.warning(f"SECURITY: {violation_type}", extra={'audit_data': security_data})

    def performance(self, operation: str, duration: float, metrics: Dict[str, Any]):
        """Log performance metrics"""
        performance_data = {
            'event_type': 'performance',
            'operation': operation,
            'duration_ms': duration * 1000,
            'metrics': metrics
        }

        self.logger.info(f"PERF: {operation} ({duration:.3f}s)", extra={'extra_data': performance_data})


def setup_logging(log_level: str = "INFO"):
    """Setup application-wide logging configuration"""

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configuration for structured logging
    logging_config = {
        'file_logging': {
            'enabled': True,
            'directory': 'logs',
            'level': 'INFO'
        },
        'console_logging': {
            'enabled': True,
            'level': log_level
        },
        'audit_logging': {
            'enabled': True,
            'file': 'logs/audit.log'
        }
    }

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(ColoredFormatter())
    root_logger.addHandler(console_handler)

    # Add file handler with JSON format
    file_handler = logging.handlers.RotatingFileHandler(
        logs_dir / "application.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    # Setup specific loggers
    loggers = {
        'gui_terminal': logging_config,
        'security': logging_config,
        'audit': {**logging_config, 'console_logging': {'enabled': False, 'level': 'CRITICAL'}},
        'performance': logging_config
    }

    structured_loggers = {}
    for name, config in loggers.items():
        structured_loggers[name] = StructuredLogger(name, config)

    logging.info(f"Logging initialized with level: {log_level}")
    return structured_loggers


def get_logger(name: str) -> logging.Logger:
    """Get logger instance for module"""
    return logging.getLogger(name)


def calculate_hash(data: str) -> str:
    """Calculate SHA256 hash for integrity checking"""
    return hashlib.sha256(data.encode()).hexdigest()


def verify_log_integrity(log_file: str) -> tuple[bool, list]:
    """Verify integrity of audit log file"""
    errors = []

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())

                    if 'integrity_hash' in entry:
                        # Recalculate hash without the integrity_hash field
                        entry_copy = entry.copy()
                        stored_hash = entry_copy.pop('integrity_hash')

                        calculated_hash = hashlib.sha256(
                            json.dumps(entry_copy, sort_keys=True).encode()
                        ).hexdigest()

                        if stored_hash != calculated_hash:
                            errors.append(f"Integrity violation at line {line_num}")

                except json.JSONDecodeError:
                    errors.append(f"Invalid JSON at line {line_num}")

    except FileNotFoundError:
        errors.append(f"Log file not found: {log_file}")
    except Exception as e:
        errors.append(f"Error reading log file: {e}")

    return len(errors) == 0, errors