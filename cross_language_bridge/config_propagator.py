"""
Unified Configuration Management
===============================

Manages configuration propagation across Python, MQL4, and PowerShell systems.
Ensures consistent settings across all language bridges.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class UnifiedConfigManager:
    """Manages unified configuration across Python, MQL4, and PowerShell systems."""
    
    def __init__(self, config_root: Optional[Path] = None):
        """Initialize unified configuration manager.
        
        Args:
            config_root: Root directory for configuration files
        """
        self.config_root = config_root or Path("config")
        self.config_root.mkdir(exist_ok=True)
        
        # Configuration file paths
        self.python_config = self.config_root / "python_config.json"
        self.mql4_config = self.config_root / "mql4_config.mqh"
        self.powershell_config = self.config_root / "powershell_config.ps1"
        self.unified_config = self.config_root / "unified_config.json"
        
        logger.info(f"UnifiedConfigManager initialized with root: {self.config_root}")
    
    def load_unified_config(self) -> Dict[str, Any]:
        """Load the unified configuration from JSON file.
        
        Returns:
            Dictionary containing unified configuration
        """
        if not self.unified_config.exists():
            return self._create_default_config()
        
        try:
            with open(self.unified_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("Unified configuration loaded successfully")
            return config
        except Exception as exc:
            logger.error(f"Failed to load unified config: {exc}")
            return self._create_default_config()
    
    def save_unified_config(self, config: Dict[str, Any]) -> bool:
        """Save unified configuration to JSON file.
        
        Args:
            config: Configuration dictionary to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.unified_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info("Unified configuration saved successfully")
            return True
        except Exception as exc:
            logger.error(f"Failed to save unified config: {exc}")
            return False
    
    def propagate_to_python(self, config: Dict[str, Any]) -> bool:
        """Propagate configuration to Python format.
        
        Args:
            config: Unified configuration dictionary
            
        Returns:
            True if propagated successfully
        """
        try:
            python_settings = {
                "database": config.get("database", {}),
                "api": config.get("api", {}),
                "logging": config.get("logging", {}),
                "features": config.get("features", {}),
            }
            
            with open(self.python_config, 'w', encoding='utf-8') as f:
                json.dump(python_settings, f, indent=2)
            
            logger.info("Configuration propagated to Python successfully")
            return True
        except Exception as exc:
            logger.error(f"Failed to propagate to Python: {exc}")
            return False
    
    def propagate_to_mql4(self, config: Dict[str, Any]) -> bool:
        """Propagate configuration to MQL4 format (.mqh header file).
        
        Args:
            config: Unified configuration dictionary
            
        Returns:
            True if propagated successfully
        """
        try:
            mql4_content = self._generate_mql4_config(config)
            
            with open(self.mql4_config, 'w', encoding='utf-8') as f:
                f.write(mql4_content)
            
            logger.info("Configuration propagated to MQL4 successfully")
            return True
        except Exception as exc:
            logger.error(f"Failed to propagate to MQL4: {exc}")
            return False
    
    def propagate_to_powershell(self, config: Dict[str, Any]) -> bool:
        """Propagate configuration to PowerShell format.
        
        Args:
            config: Unified configuration dictionary
            
        Returns:
            True if propagated successfully
        """
        try:
            ps_content = self._generate_powershell_config(config)
            
            with open(self.powershell_config, 'w', encoding='utf-8') as f:
                f.write(ps_content)
            
            logger.info("Configuration propagated to PowerShell successfully")
            return True
        except Exception as exc:
            logger.error(f"Failed to propagate to PowerShell: {exc}")
            return False
    
    def propagate_all(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
        """Propagate configuration to all language formats.
        
        Args:
            config: Configuration dictionary, loads unified if None
            
        Returns:
            Dictionary with success status for each language
        """
        if config is None:
            config = self.load_unified_config()
        
        results = {
            "python": self.propagate_to_python(config),
            "mql4": self.propagate_to_mql4(config),
            "powershell": self.propagate_to_powershell(config),
        }
        
        success_count = sum(results.values())
        logger.info(f"Configuration propagated to {success_count}/3 languages successfully")
        
        return results
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate unified configuration for completeness and correctness.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        required_sections = ["database", "api", "logging", "features", "bridge"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")
        
        # Validate database configuration
        if "database" in config:
            db_config = config["database"]
            if not db_config.get("host"):
                errors.append("Database host is required")
            if not db_config.get("name"):
                errors.append("Database name is required")
        
        # Validate API configuration  
        if "api" in config:
            api_config = config["api"]
            port = api_config.get("port")
            if port and not (1024 <= port <= 65535):
                errors.append("API port must be between 1024 and 65535")
        
        # Validate bridge configuration
        if "bridge" in config:
            bridge_config = config["bridge"]
            if not bridge_config.get("enabled", True):
                errors.append("Cross-language bridge must be enabled")
        
        return errors
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default unified configuration.
        
        Returns:
            Default configuration dictionary
        """
        default_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "cli_multi_rapid",
                "username": "user",
                "password": "password"
            },
            "api": {
                "host": "localhost",
                "port": 8000,
                "debug": False
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "application.log"
            },
            "features": {
                "workflow_validation": True,
                "compliance_checking": True,
                "cross_language_bridge": True
            },
            "bridge": {
                "enabled": True,
                "timeout": 30,
                "retry_attempts": 3,
                "health_check_interval": 60
            }
        }
        
        # Save default configuration
        self.save_unified_config(default_config)
        logger.info("Default unified configuration created")
        
        return default_config
    
    def _generate_mql4_config(self, config: Dict[str, Any]) -> str:
        """Generate MQL4 configuration header file content.
        
        Args:
            config: Unified configuration dictionary
            
        Returns:
            MQL4 header file content string
        """
        mql4_content = """//+------------------------------------------------------------------+
//| Cross-Language Bridge Configuration for MQL4                     |
//| Auto-generated from unified configuration                        |
//+------------------------------------------------------------------+

#ifndef CLI_MULTI_RAPID_CONFIG_H
#define CLI_MULTI_RAPID_CONFIG_H

// Database Configuration
"""
        
        db_config = config.get("database", {})
        mql4_content += f'#define DB_HOST "{db_config.get("host", "localhost")}"\n'
        mql4_content += f'#define DB_PORT {db_config.get("port", 5432)}\n'
        mql4_content += f'#define DB_NAME "{db_config.get("name", "cli_multi_rapid")}"\n'
        
        api_config = config.get("api", {})
        mql4_content += f'\n// API Configuration\n'
        mql4_content += f'#define API_HOST "{api_config.get("host", "localhost")}"\n'
        mql4_content += f'#define API_PORT {api_config.get("port", 8000)}\n'
        
        bridge_config = config.get("bridge", {})
        mql4_content += f'\n// Bridge Configuration\n'
        mql4_content += f'#define BRIDGE_ENABLED {"true" if bridge_config.get("enabled", True) else "false"}\n'
        mql4_content += f'#define BRIDGE_TIMEOUT {bridge_config.get("timeout", 30)}\n'
        mql4_content += f'#define BRIDGE_RETRY_ATTEMPTS {bridge_config.get("retry_attempts", 3)}\n'
        
        mql4_content += '\n#endif // CLI_MULTI_RAPID_CONFIG_H\n'
        
        return mql4_content
    
    def _generate_powershell_config(self, config: Dict[str, Any]) -> str:
        """Generate PowerShell configuration script content.
        
        Args:
            config: Unified configuration dictionary
            
        Returns:
            PowerShell script content string
        """
        ps_content = """# Cross-Language Bridge Configuration for PowerShell
# Auto-generated from unified configuration

# Database Configuration
"""
        
        db_config = config.get("database", {})
        ps_content += f'$DB_HOST = "{db_config.get("host", "localhost")}"\n'
        ps_content += f'$DB_PORT = {db_config.get("port", 5432)}\n'
        ps_content += f'$DB_NAME = "{db_config.get("name", "cli_multi_rapid")}"\n'
        
        api_config = config.get("api", {})
        ps_content += f'\n# API Configuration\n'
        ps_content += f'$API_HOST = "{api_config.get("host", "localhost")}"\n'
        ps_content += f'$API_PORT = {api_config.get("port", 8000)}\n'
        
        bridge_config = config.get("bridge", {})
        ps_content += f'\n# Bridge Configuration\n'
        ps_content += f'$BRIDGE_ENABLED = ${"true" if bridge_config.get("enabled", True) else "false"}\n'
        ps_content += f'$BRIDGE_TIMEOUT = {bridge_config.get("timeout", 30)}\n'
        ps_content += f'$BRIDGE_RETRY_ATTEMPTS = {bridge_config.get("retry_attempts", 3)}\n'
        
        features_config = config.get("features", {})
        ps_content += f'\n# Feature Configuration\n'
        ps_content += f'$WORKFLOW_VALIDATION = ${"true" if features_config.get("workflow_validation", True) else "false"}\n'
        ps_content += f'$COMPLIANCE_CHECKING = ${"true" if features_config.get("compliance_checking", True) else "false"}\n'
        
        ps_content += '\n# Export configuration variables\n'
        ps_content += 'Export-ModuleMember -Variable *\n'
        
        return ps_content