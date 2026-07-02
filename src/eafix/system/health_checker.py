"""
System Health Checker
Monitors system health, performance metrics, and component status
"""

import os
import sys
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class HealthChecker:
    """Comprehensive system health monitoring and reporting"""
    
    def __init__(self):
        self.start_time = datetime.now()
        
    def get_quick_status(self) -> Dict[str, str]:
        """Get quick system status for CLI status command"""
        try:
            status = {
                'overall_health': 'healthy',
                'database': 'unknown',
                'guardian': 'unknown', 
                'mt4_connection': 'unknown'
            }
            
            # Check database files
            db_files = ['trading_system.db', 'huey_project_organizer.db']
            db_exists = any(Path(db).exists() for db in db_files)
            status['database'] = 'connected' if db_exists else 'missing'
            
            # Check Guardian system (basic check)
            guardian_path = Path('src/eafix/guardian')
            status['guardian'] = 'available' if guardian_path.exists() else 'missing'
            
            # Check MT4 connection (placeholder)
            status['mt4_connection'] = 'checking'
            
            # Determine overall health
            if status['database'] == 'missing' or status['guardian'] == 'missing':
                status['overall_health'] = 'warning'
            
            return status
            
        except Exception as e:
            return {
                'overall_health': 'error',
                'database': 'error',
                'guardian': 'error',
                'mt4_connection': 'error'
            }
    
    def get_full_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'healthy',
                'components': {},
                'metrics': {},
                'recommendations': []
            }
            
            # System metrics
            report['metrics'] = self._get_system_metrics()
            
            # Component health checks
            components = {
                'database': self._check_database_health(),
                'guardian': self._check_guardian_health(),
                'configuration': self._check_configuration_health(),
                'file_system': self._check_file_system_health(),
                'python_environment': self._check_python_environment()
            }
            
            report['components'] = components
            
            # Determine overall health
            unhealthy_components = [k for k, v in components.items() if v != 'healthy']
            
            if len(unhealthy_components) == 0:
                report['overall_health'] = 'healthy'
            elif len(unhealthy_components) <= 2:
                report['overall_health'] = 'warning'
                report['recommendations'].append(f"Address issues with: {', '.join(unhealthy_components)}")
            else:
                report['overall_health'] = 'critical'
                report['recommendations'].append("Multiple system components need attention")
            
            # Performance-based recommendations
            if report['metrics']['memory_percent'] > 80:
                report['recommendations'].append("High memory usage detected")
            
            if report['metrics']['cpu_percent'] > 90:
                report['recommendations'].append("High CPU usage detected")
            
            if report['metrics']['disk_percent'] > 85:
                report['recommendations'].append("Low disk space - consider cleanup")
            
            return report
            
        except Exception as e:
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_health': 'error',
                'error': str(e),
                'components': {},
                'metrics': {},
                'recommendations': ['System health check failed - investigate errors']
            }
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network connections
            connections = len(psutil.net_connections())
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent, 
                'disk_percent': disk_percent,
                'connections': connections,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
            
        except Exception:
            return {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'connections': 0,
                'uptime_seconds': 0
            }
    
    def _check_database_health(self) -> str:
        """Check database component health"""
        try:
            db_files = [
                'trading_system.db',
                'huey_project_organizer.db',
                'e2e_trading.db',
                'e2e_guardian.db'
            ]
            
            existing_dbs = [db for db in db_files if Path(db).exists()]
            
            if len(existing_dbs) >= 2:
                # Check if databases are readable
                try:
                    import sqlite3
                    for db in existing_dbs[:2]:  # Check first 2
                        conn = sqlite3.connect(db)
                        conn.execute("SELECT 1")
                        conn.close()
                    return 'healthy'
                except sqlite3.Error:
                    return 'warning'
            elif len(existing_dbs) >= 1:
                return 'warning'
            else:
                return 'missing'
                
        except Exception:
            return 'error'
    
    def _check_guardian_health(self) -> str:
        """Check Guardian system health"""
        try:
            guardian_path = Path('src/eafix/guardian')
            
            if not guardian_path.exists():
                return 'missing'
            
            # Check for key Guardian files
            required_files = [
                'constraints.py',
                'agents.py', 
                'gates.py'
            ]
            
            existing_files = [f for f in required_files if (guardian_path / f).exists()]
            
            if len(existing_files) == len(required_files):
                return 'healthy'
            elif len(existing_files) > 0:
                return 'warning'
            else:
                return 'missing'
                
        except Exception:
            return 'error'
    
    def _check_configuration_health(self) -> str:
        """Check configuration file health"""
        try:
            config_file = Path('settings.json')
            
            if not config_file.exists():
                return 'missing'
            
            # Validate JSON
            import json
            with open(config_file) as f:
                config = json.load(f)
            
            # Check for required sections
            required_sections = ['signals', 'dde']
            missing_sections = [s for s in required_sections if s not in config]
            
            if len(missing_sections) == 0:
                return 'healthy'
            elif len(missing_sections) <= 1:
                return 'warning'
            else:
                return 'incomplete'
                
        except json.JSONDecodeError:
            return 'corrupt'
        except Exception:
            return 'error'
    
    def _check_file_system_health(self) -> str:
        """Check file system permissions and accessibility"""
        try:
            # Check write permissions
            test_file = Path('health_check_test.tmp')
            try:
                test_file.write_text('test')
                test_file.unlink()
                write_ok = True
            except Exception:
                write_ok = False
            
            # Check critical paths
            critical_paths = [
                Path('src/eafix/apps/cli/main.py'),
                Path('settings.json'),
                Path('CLAUDE.md')
            ]
            
            accessible_paths = [p for p in critical_paths if p.exists()]
            
            if write_ok and len(accessible_paths) >= 2:
                return 'healthy'
            elif write_ok or len(accessible_paths) >= 1:
                return 'warning'
            else:
                return 'limited'
                
        except Exception:
            return 'error'
    
    def _check_python_environment(self) -> str:
        """Check Python environment and dependencies"""
        try:
            # Check Python version
            version = sys.version_info
            if version < (3, 8):
                return 'outdated'
            
            # Check critical imports
            critical_modules = ['json', 'pathlib', 'datetime', 'subprocess']
            
            missing_modules = []
            for module in critical_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if len(missing_modules) == 0:
                return 'healthy'
            elif len(missing_modules) <= 2:
                return 'warning' 
            else:
                return 'incomplete'
                
        except Exception:
            return 'error'