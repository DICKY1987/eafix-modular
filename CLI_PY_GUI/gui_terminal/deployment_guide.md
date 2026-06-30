# Enhanced GUI Terminal - Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying the Enhanced GUI Terminal system in production environments, including security hardening, performance optimization, and operational procedures.

## 🎯 Pre-Deployment Checklist

### ✅ **System Requirements**
- [ ] Python 3.8+ installed
- [ ] PyQt6 or PyQt5 available
- [ ] Windows: `pywinpty` package installed
- [ ] Unix/Linux: PTY support available
- [ ] Minimum 4GB RAM, 2 CPU cores
- [ ] 1GB available disk space

### ✅ **Security Requirements**
- [ ] Security configuration reviewed and approved
- [ ] Compliance rules configured for environment
- [ ] Audit logging destination configured  
- [ ] Resource limits defined and tested
- [ ] Network security policies applied

### ✅ **Testing Requirements**
- [ ] Comprehensive test suite passed (>90% success rate)
- [ ] Security tests all passing
- [ ] Performance benchmarks within limits
- [ ] Platform-specific testing completed
- [ ] User acceptance testing signed off

## 🚀 Installation Steps

### 1. **Environment Setup**

```bash
# Create dedicated user account
sudo useradd -m -s /bin/bash gui-terminal
sudo usermod -aG sudo gui-terminal

# Create application directory
sudo mkdir -p /opt/gui-terminal
sudo chown gui-terminal:gui-terminal /opt/gui-terminal

# Switch to application user
sudo su - gui-terminal
```

### 2. **Python Environment**

```bash
# Create virtual environment
cd /opt/gui-terminal
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install PyQt6 psutil winpty  # winpty only on Windows
pip install pytest pytest-asyncio  # for testing

# Verify installation
python -c "import PyQt6; print('PyQt6 OK')"
```

### 3. **Application Deployment**

```bash
# Copy application files
mkdir -p /opt/gui-terminal/{src,config,logs,data}

# Copy main application files
cp enhanced_pty_terminal.py /opt/gui-terminal/src/
cp security_configuration.py /opt/gui-terminal/src/
cp comprehensive_testing_suite.py /opt/gui-terminal/src/

# Set permissions
chmod 755 /opt/gui-terminal/src/*.py
chmod 750 /opt/gui-terminal/config
chmod 750 /opt/gui-terminal/logs
```

### 4. **Configuration Setup**

Create production configuration files:

**`/opt/gui-terminal/config/production_config.json`**:
```json
{
  "security": {
    "level": "strict",
    "allowed_commands": [
      "ls", "dir", "pwd", "cd", "echo", "cat", "type", "grep", "find",
      "python", "pip", "git", "node", "npm", "cli-multi-rapid"
    ],
    "blocked_commands": [
      "rm", "del", "format", "fdisk", "dd", "mkfs", "sudo", "su"
    ],
    "max_execution_time": 300,
    "max_memory_mb": 512,
    "audit_commands": true,
    "require_confirmation": ["rm", "del", "format", "sudo"]
  },
  "terminal": {
    "font_family": "Consolas",
    "font_size": 10,
    "theme": "dark",
    "max_history": 1000,
    "auto_scroll": true
  },
  "gui": {
    "window_width": 1200,
    "window_height": 800,
    "show_command_preview": true,
    "show_history": true,
    "confirm_dangerous_commands": true
  }
}
```

**`/opt/gui-terminal/config/compliance_rules.json`**:
```json
[
  {
    "rule_id": "CR001",
    "name": "Privilege Escalation Prevention",
    "description": "Block commands that attempt privilege escalation",
    "enabled": true,
    "violation_patterns": ["sudo", "su ", "runas", "elevate"],
    "allowed_exceptions": [],
    "severity": "high",
    "action": "block"
  },
  {
    "rule_id": "CR002", 
    "name": "System File Protection",
    "description": "Prevent modification of critical system files",
    "enabled": true,
    "violation_patterns": ["/etc/", "/boot/", "/sys/", "C:\\Windows\\System32"],
    "allowed_exceptions": [],
    "severity": "critical",
    "action": "block"
  }
]
```

### 5. **Service Configuration** (Linux)

Create systemd service file:

**`/etc/systemd/system/gui-terminal.service`**:
```ini
[Unit]
Description=Enhanced GUI Terminal Service
After=network.target

[Service]
Type=simple
User=gui-terminal
Group=gui-terminal
WorkingDirectory=/opt/gui-terminal
Environment=PATH=/opt/gui-terminal/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/opt/gui-terminal/src
ExecStart=/opt/gui-terminal/venv/bin/python src/enhanced_pty_terminal.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=gui-terminal

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
MemoryLimit=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl enable gui-terminal
sudo systemctl start gui-terminal
sudo systemctl status gui-terminal
```

## 🔒 Security Configuration

### 1. **File Permissions**

```bash
# Application files
sudo chown -R gui-terminal:gui-terminal /opt/gui-terminal
sudo chmod 755 /opt/gui-terminal
sudo chmod 750 /opt/gui-terminal/{config,logs,data}
sudo chmod 644 /opt/gui-terminal/config/*.json
sudo chmod 640 /opt/gui-terminal/logs/*

# Log rotation
sudo tee /etc/logrotate.d/gui-terminal << EOF
/opt/gui-terminal/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su gui-terminal gui-terminal
}
EOF
```

### 2. **Firewall Configuration**

```bash
# Allow only necessary ports (if applicable)
sudo ufw allow from 127.0.0.1 to any port 8080
sudo ufw enable
```

### 3. **SELinux/AppArmor** (if applicable)

Create AppArmor profile for additional security:

**`/etc/apparmor.d/gui-terminal`**:
```
#include <tunables/global>

/opt/gui-terminal/venv/bin/python {
  #include <abstractions/base>
  #include <abstractions/python>
  
  /opt/gui-terminal/** r,
  /opt/gui-terminal/src/** r,
  /opt/gui-terminal/logs/* w,
  /opt/gui-terminal/data/* rw,
  
  /usr/bin/python3* ix,
  /bin/bash ix,
  /bin/sh ix,
  
  deny /etc/shadow r,
  deny /root/** rwx,
}
```

## 📊 Monitoring & Logging

### 1. **Application Monitoring**

Create monitoring script:

**`/opt/gui-terminal/scripts/health_check.py`**:
```python
#!/usr/bin/env python3
"""
Health check script for GUI Terminal
"""
import sys
import json
import time
import psutil
from pathlib import Path

def check_application_health():
    """Check application health status"""
    health = {
        "timestamp": time.time(),
        "status": "healthy",
        "checks": {}
    }
    
    try:
        # Check if application is running
        gui_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                        if 'enhanced_pty_terminal' in ' '.join(p.info['cmdline'] or [])]
        
        health["checks"]["process_running"] = len(gui_processes) > 0
        
        # Check memory usage
        if gui_processes:
            process = psutil.Process(gui_processes[0].info['pid'])
            memory_mb = process.memory_info().rss / (1024 * 1024)
            health["checks"]["memory_usage_mb"] = memory_mb
            health["checks"]["memory_ok"] = memory_mb < 1000  # Less than 1GB
        
        # Check log file size
        log_file = Path("/opt/gui-terminal/logs/gui_terminal.log")
        if log_file.exists():
            log_size_mb = log_file.stat().st_size / (1024 * 1024)
            health["checks"]["log_size_mb"] = log_size_mb
            health["checks"]["log_size_ok"] = log_size_mb < 100  # Less than 100MB
        
        # Check disk space
        disk_usage = psutil.disk_usage('/opt/gui-terminal')
        free_space_gb = disk_usage.free / (1024 * 1024 * 1024)
        health["checks"]["disk_free_gb"] = free_space_gb
        health["checks"]["disk_ok"] = free_space_gb > 1  # At least 1GB free
        
        # Overall status
        all_checks_ok = all(
            check for check_name, check in health["checks"].items()
            if check_name.endswith("_ok")
        )
        
        health["status"] = "healthy" if all_checks_ok else "degraded"
        
    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)
    
    return health

if __name__ == "__main__":
    health = check_application_health()
    print(json.dumps(health, indent=2))
    
    # Exit with error code if unhealthy
    sys.exit(0 if health["status"] == "healthy" else 1)
```

### 2. **Log Configuration**

**`/opt/gui-terminal/config/logging_config.json`**:
```json
{
  "version": 1,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    },
    "security": {
      "format": "%(asctime)s - SECURITY - %(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "/opt/gui-terminal/logs/gui_terminal.log",
      "maxBytes": 10485760,
      "backupCount": 10,
      "formatter": "detailed"
    },
    "security_file": {
      "class": "logging.handlers.RotatingFileHandler", 
      "filename": "/opt/gui-terminal/logs/security_audit.log",
      "maxBytes": 10485760,
      "backupCount": 50,
      "formatter": "security"
    },
    "syslog": {
      "class": "logging.handlers.SysLogHandler",
      "address": "/dev/log",
      "formatter": "detailed"
    }
  },
  "loggers": {
    "": {
      "level": "INFO",
      "handlers": ["file", "syslog"]
    },
    "security_audit": {
      "level": "INFO",
      "handlers": ["security_file", "syslog"],
      "propagate": false
    }
  }
}
```

### 3. **Prometheus Metrics** (Optional)

Create metrics endpoint:

**`/opt/gui-terminal/src/metrics_server.py`**:
```python
#!/usr/bin/env python3
"""
Prometheus metrics server for GUI Terminal
"""
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import time
import threading

# Metrics
commands_executed = Counter('terminal_commands_executed_total', 'Total commands executed')
command_duration = Histogram('terminal_command_duration_seconds', 'Command execution duration')
active_terminals = Gauge('terminal_active_count', 'Number of active terminals')
security_violations = Counter('terminal_security_violations_total', 'Security violations detected')

def start_metrics_server(port=8080):
    """Start Prometheus metrics server"""
    start_http_server(port)
    print(f"Metrics server started on port {port}")

# Export metrics for use in main application
__all__ = ['commands_executed', 'command_duration', 'active_terminals', 'security_violations', 'start_metrics_server']
```

## 🔧 Performance Optimization

### 1. **System Tuning**

```bash
# Increase file descriptor limits
echo "gui-terminal soft nofile 65536" >> /etc/security/limits.conf
echo "gui-terminal hard nofile 65536" >> /etc/security/limits.conf

# Optimize for interactive processes
echo "vm.swappiness = 1" >> /etc/sysctl.conf
echo "kernel.sched_autogroup_enabled = 1" >> /etc/sysctl.conf

# Apply changes
sysctl -p
```

### 2. **Application Optimization**

Create optimized startup script:

**`/opt/gui-terminal/scripts/start_optimized.py`**:
```python
#!/usr/bin/env python3
"""
Optimized startup script with preloading and caching
"""
import os
import sys
import gc
import threading
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def optimize_python():
    """Optimize Python runtime"""
    # Disable garbage collection during startup
    gc.disable()
    
    # Set optimizations
    os.environ["PYTHONOPTIMIZE"] = "2"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    
    # Pre-import heavy modules
    import PyQt6.QtWidgets
    import PyQt6.QtCore
    import PyQt6.QtGui
    
    # Re-enable garbage collection
    gc.enable()

def main():
    """Main optimized startup"""
    print("Starting Enhanced GUI Terminal (Optimized)...")
    
    # Apply optimizations
    optimize_python()
    
    # Import and start main application
    from enhanced_pty_terminal import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()
```

## 🧪 Testing in Production

### 1. **Smoke Tests**

Create production smoke test:

**`/opt/gui-terminal/scripts/smoke_test.py`**:
```python
#!/usr/bin/env python3
"""
Production smoke test
"""
import subprocess
import sys
import json
import time
from pathlib import Path

def run_smoke_tests():
    """Run basic smoke tests"""
    tests = []
    
    # Test 1: Application starts
    print("Testing application startup...")
    try:
        # This would test GUI startup in headless mode
        result = subprocess.run([
            sys.executable, "/opt/gui-terminal/src/enhanced_pty_terminal.py", "--test-mode"
        ], capture_output=True, text=True, timeout=30)
        
        tests.append({
            "test": "application_startup",
            "passed": result.returncode == 0,
            "details": result.stdout
        })
    except Exception as e:
        tests.append({
            "test": "application_startup", 
            "passed": False,
            "error": str(e)
        })
    
    # Test 2: Configuration loading
    print("Testing configuration loading...")
    try:
        config_file = Path("/opt/gui-terminal/config/production_config.json")
        config_exists = config_file.exists()
        
        if config_exists:
            with open(config_file) as f:
                config = json.load(f)
            valid_config = "security" in config and "terminal" in config
        else:
            valid_config = False
        
        tests.append({
            "test": "configuration_loading",
            "passed": config_exists and valid_config,
            "details": f"Config exists: {config_exists}, Valid: {valid_config}"
        })
    except Exception as e:
        tests.append({
            "test": "configuration_loading",
            "passed": False,
            "error": str(e)
        })
    
    # Test 3: Security system
    print("Testing security system...")
    try:
        from security_configuration import EnhancedSecurityManager
        security = EnhancedSecurityManager()
        
        # Test command validation
        allowed, violations, _ = security.validate_and_execute(
            "echo test", "/tmp", {}, "smoke_test", "smoke_test"
        )
        
        security.shutdown()
        
        tests.append({
            "test": "security_system",
            "passed": allowed and len(violations) == 0,
            "details": f"Command allowed: {allowed}, Violations: {len(violations)}"
        })
    except Exception as e:
        tests.append({
            "test": "security_system",
            "passed": False,
            "error": str(e)
        })
    
    return tests

def main():
    """Main smoke test runner"""
    print("🔥 Production Smoke Test Suite")
    print("=" * 40)
    
    tests = run_smoke_tests()
    
    passed_count = sum(1 for t in tests if t["passed"])
    total_count = len(tests)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    
    for test in tests:
        status = "✅" if test["passed"] else "❌"
        print(f"{status} {test['test']}")
        
        if not test["passed"] and "error" in test:
            print(f"   Error: {test['error']}")
    
    # Exit with appropriate code
    sys.exit(0 if passed_count == total_count else 1)

if __name__ == "__main__":
    main()
```

### 2. **Automated Testing**

Create cron job for regular testing:

```bash
# Add to crontab for gui-terminal user
crontab -e

# Run smoke tests every hour
0 * * * * /opt/gui-terminal/venv/bin/python /opt/gui-terminal/scripts/smoke_test.py >> /opt/gui-terminal/logs/smoke_test.log 2>&1

# Run health check every 5 minutes  
*/5 * * * * /opt/gui-terminal/venv/bin/python /opt/gui-terminal/scripts/health_check.py >> /opt/gui-terminal/logs/health_check.log 2>&1
```

## 🚨 Incident Response

### 1. **Common Issues**

| Issue | Symptoms | Resolution |
|-------|----------|------------|
| High Memory Usage | System slowdown, OOM errors | Restart service, check for memory leaks |
| Security Violations | Blocked commands, audit alerts | Review security logs, update rules |
| Performance Degradation | Slow response times | Check system resources, optimize |
| Configuration Errors | Application won't start | Validate config files, check logs |
| PTY Issues | Terminal not working | Check PTY permissions, restart |

### 2. **Emergency Procedures**

**Service Restart**:
```bash
sudo systemctl restart gui-terminal
sudo systemctl status gui-terminal
tail -f /opt/gui-terminal/logs/gui_terminal.log
```

**Emergency Shutdown**:
```bash
sudo systemctl stop gui-terminal
sudo pkill -f enhanced_pty_terminal
```

**Configuration Rollback**:
```bash
# Restore from backup
sudo cp /opt/gui-terminal/config/production_config.json.backup /opt/gui-terminal/config/production_config.json
sudo systemctl restart gui-terminal
```

## 📊 Operational Metrics

### Key Performance Indicators (KPIs)

1. **Availability**: 99.9% uptime target
2. **Response Time**: < 100ms for command execution
3. **Memory Usage**: < 1GB per instance
4. **Security**: 0 critical violations per day
5. **Error Rate**: < 0.1% command failures

### Monitoring Dashboard

Create Grafana dashboard configuration:

**`/opt/gui-terminal/config/grafana_dashboard.json`**:
```json
{
  "dashboard": {
    "title": "GUI Terminal Production Metrics",
    "panels": [
      {
        "title": "Commands Executed",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(terminal_commands_executed_total[5m])"
          }
        ]
      },
      {
        "title": "Active Terminals",
        "type": "stat", 
        "targets": [
          {
            "expr": "terminal_active_count"
          }
        ]
      },
      {
        "title": "Security Violations",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(terminal_security_violations_total[1h])"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "timeseries",
        "targets": [
          {
            "expr": "process_resident_memory_bytes{job=\"gui-terminal\"}"
          }
        ]
      },
      {
        "title": "Command Duration",
        "type": "heatmap",
        "targets": [
          {
            "expr": "terminal_command_duration_seconds_bucket"
          }
        ]
      }
    ]
  }
}
```

## 🔄 Backup & Recovery

### 1. **Backup Strategy**

Create backup script:

**`/opt/gui-terminal/scripts/backup.sh`**:
```bash
#!/bin/bash
"""
GUI Terminal Backup Script
"""

BACKUP_DIR="/opt/backups/gui-terminal"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="gui-terminal_${DATE}"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

echo "Starting GUI Terminal backup: ${BACKUP_NAME}"

# Stop service
sudo systemctl stop gui-terminal

# Create backup archive
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
  --exclude='/opt/gui-terminal/logs/*' \
  --exclude='/opt/gui-terminal/venv/*' \
  /opt/gui-terminal/

# Backup database/state files if any
if [ -d "/opt/gui-terminal/data" ]; then
  tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz" /opt/gui-terminal/data/
fi

# Start service
sudo systemctl start gui-terminal

# Cleanup old backups (keep 30 days)
find "${BACKUP_DIR}" -name "gui-terminal_*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
```

### 2. **Recovery Procedures**

**Full System Recovery**:
```bash
#!/bin/bash
# Recovery script

BACKUP_FILE="/opt/backups/gui-terminal/gui-terminal_20241201_120000.tar.gz"
RECOVERY_DIR="/opt/gui-terminal-recovery"

echo "Starting system recovery from: ${BACKUP_FILE}"

# Stop current service
sudo systemctl stop gui-terminal

# Create recovery directory
sudo mkdir -p "${RECOVERY_DIR}"

# Extract backup
sudo tar -xzf "${BACKUP_FILE}" -C "${RECOVERY_DIR}"

# Move current installation to backup
sudo mv /opt/gui-terminal /opt/gui-terminal-$(date +%Y%m%d_%H%M%S)

# Restore from backup
sudo mv "${RECOVERY_DIR}/opt/gui-terminal" /opt/

# Restore permissions
sudo chown -R gui-terminal:gui-terminal /opt/gui-terminal
sudo chmod 755 /opt/gui-terminal
sudo chmod 750 /opt/gui-terminal/{config,logs,data}

# Recreate virtual environment
sudo -u gui-terminal python3 -m venv /opt/gui-terminal/venv
sudo -u gui-terminal /opt/gui-terminal/venv/bin/pip install -r /opt/gui-terminal/requirements.txt

# Start service
sudo systemctl start gui-terminal

echo "Recovery completed"
```

## 🔐 Security Hardening

### 1. **Additional Security Measures**

**Network Security**:
```bash
# Configure iptables
sudo iptables -A INPUT -p tcp --dport 8080 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8080 -j DROP

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

**File Integrity Monitoring**:
```bash
# Install and configure AIDE
sudo apt-get install aide
sudo aideinit

# Add GUI Terminal to monitoring
echo "/opt/gui-terminal R" >> /etc/aide/aide.conf

# Create daily check
echo "0 2 * * * root aide --check" >> /etc/crontab
```

### 2. **Audit Configuration**

**Configure auditd**:
```bash
# Add audit rules for GUI Terminal
echo "-w /opt/gui-terminal/src/ -p wa -k gui-terminal-code" >> /etc/audit/rules.d/gui-terminal.rules
echo "-w /opt/gui-terminal/config/ -p wa -k gui-terminal-config" >> /etc/audit/rules.d/gui-terminal.rules

# Restart auditd
sudo systemctl restart auditd
```

## 🌐 Multi-Environment Setup

### 1. **Environment-Specific Configurations**

**Development Environment**:
```json
{
  "security": {
    "level": "basic",
    "audit_commands": false,
    "max_execution_time": 600
  },
  "terminal": {
    "font_size": 12
  },
  "gui": {
    "confirm_dangerous_commands": false
  }
}
```

**Staging Environment**:
```json
{
  "security": {
    "level": "strict", 
    "audit_commands": true,
    "max_execution_time": 300
  },
  "terminal": {
    "font_size": 10
  },
  "gui": {
    "confirm_dangerous_commands": true
  }
}
```

**Production Environment**:
```json
{
  "security": {
    "level": "paranoid",
    "audit_commands": true,
    "max_execution_time": 180
  },
  "terminal": {
    "font_size": 10
  },
  "gui": {
    "confirm_dangerous_commands": true
  }
}
```

### 2. **Deployment Pipeline**

Create deployment pipeline:

**`/opt/gui-terminal/scripts/deploy.py`**:
```python
#!/usr/bin/env python3
"""
Automated deployment script
"""
import subprocess
import sys
import json
import time
from pathlib import Path

def deploy_to_environment(environment, version):
    """Deploy to specific environment"""
    print(f"Deploying version {version} to {environment}...")
    
    steps = [
        ("Backup current version", backup_current),
        ("Download new version", lambda: download_version(version)),
        ("Run tests", run_tests),
        ("Update configuration", lambda: update_config(environment)),
        ("Deploy application", deploy_application),
        ("Restart services", restart_services),
        ("Verify deployment", verify_deployment),
        ("Run smoke tests", run_smoke_tests)
    ]
    
    for step_name, step_func in steps:
        print(f"  {step_name}...")
        try:
            if not step_func():
                raise Exception(f"Step failed: {step_name}")
            print(f"  ✅ {step_name} completed")
        except Exception as e:
            print(f"  ❌ {step_name} failed: {e}")
            rollback_deployment()
            return False
    
    print(f"✅ Deployment to {environment} completed successfully")
    return True

def backup_current():
    """Backup current installation"""
    result = subprocess.run([
        "/opt/gui-terminal/scripts/backup.sh"
    ], capture_output=True)
    return result.returncode == 0

def download_version(version):
    """Download specific version"""
    # Implementation would download from repository/artifact store
    return True

def run_tests():
    """Run comprehensive tests"""
    result = subprocess.run([
        "/opt/gui-terminal/venv/bin/python",
        "/opt/gui-terminal/src/comprehensive_testing_suite.py"
    ], capture_output=True)
    return result.returncode == 0

def update_config(environment):
    """Update configuration for environment"""
    config_file = f"/opt/gui-terminal/config/{environment}_config.json"
    target_file = "/opt/gui-terminal/config/production_config.json"
    
    if Path(config_file).exists():
        subprocess.run(["cp", config_file, target_file])
        return True
    return False

def deploy_application():
    """Deploy application files"""
    # Implementation would copy new application files
    return True

def restart_services():
    """Restart services"""
    result = subprocess.run([
        "sudo", "systemctl", "restart", "gui-terminal"
    ])
    return result.returncode == 0

def verify_deployment():
    """Verify deployment"""
    time.sleep(5)  # Wait for service to start
    result = subprocess.run([
        "sudo", "systemctl", "is-active", "gui-terminal"
    ], capture_output=True, text=True)
    return result.stdout.strip() == "active"

def run_smoke_tests():
    """Run smoke tests"""
    result = subprocess.run([
        "/opt/gui-terminal/venv/bin/python",
        "/opt/gui-terminal/scripts/smoke_test.py"
    ])
    return result.returncode == 0

def rollback_deployment():
    """Rollback deployment"""
    print("Rolling back deployment...")
    # Implementation would restore from backup
    subprocess.run(["sudo", "systemctl", "restart", "gui-terminal"])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: deploy.py <environment> <version>")
        sys.exit(1)
    
    environment = sys.argv[1]
    version = sys.argv[2]
    
    success = deploy_to_environment(environment, version)
    sys.exit(0 if success else 1)
```

## 📋 Maintenance Procedures

### 1. **Regular Maintenance Tasks**

**Daily Tasks**:
- [ ] Check service status
- [ ] Review security audit logs
- [ ] Monitor resource usage
- [ ] Verify backup completion

**Weekly Tasks**:
- [ ] Rotate logs
- [ ] Update security rules
- [ ] Performance analysis
- [ ] Capacity planning review

**Monthly Tasks**:
- [ ] Security vulnerability scan
- [ ] Performance optimization
- [ ] Configuration review
- [ ] Disaster recovery testing

### 2. **Maintenance Scripts**

**`/opt/gui-terminal/scripts/maintenance.py`**:
```python
#!/usr/bin/env python3
"""
Automated maintenance tasks
"""
import subprocess
import os
import time
from pathlib import Path
import json

def log_rotation():
    """Rotate log files"""
    log_dir = Path("/opt/gui-terminal/logs")
    max_size_mb = 100
    
    for log_file in log_dir.glob("*.log"):
        size_mb = log_file.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            # Rotate log
            timestamp = int(time.time())
            rotated_name = log_file.with_suffix(f".{timestamp}.log")
            log_file.rename(rotated_name)
            
            # Compress rotated log
            subprocess.run(["gzip", str(rotated_name)])
            
            # Create new log file
            log_file.touch()
            os.chown(log_file, os.getuid(), os.getgid())

def cleanup_temp_files():
    """Clean up temporary files"""
    temp_dirs = [
        "/tmp",
        "/var/tmp", 
        "/opt/gui-terminal/temp"
    ]
    
    for temp_dir in temp_dirs:
        if Path(temp_dir).exists():
            # Remove files older than 7 days
            subprocess.run([
                "find", temp_dir, "-type", "f", "-mtime", "+7",
                "-name", "*gui-terminal*", "-delete"
            ])

def check_disk_space():
    """Check disk space and alert if low"""
    import shutil
    
    total, used, free = shutil.disk_usage("/opt/gui-terminal")
    free_gb = free / (1024 ** 3)
    
    if free_gb < 5:  # Less than 5GB free
        print(f"WARNING: Low disk space - {free_gb:.1f}GB remaining")
        return False
    
    return True

def security_scan():
    """Run security scan"""
    # Check for suspicious processes
    result = subprocess.run([
        "ps", "aux"
    ], capture_output=True, text=True)
    
    # Look for suspicious activity
    suspicious_patterns = ["nc ", "netcat", "/bin/sh", "bash -i"]
    alerts = []
    
    for line in result.stdout.split('\n'):
        for pattern in suspicious_patterns:
            if pattern in line and "gui-terminal" in line:
                alerts.append(f"Suspicious process: {line}")
    
    if alerts:
        print("SECURITY ALERT:")
        for alert in alerts:
            print(f"  {alert}")
        return False
    
    return True

def main():
    """Main maintenance routine"""
    print("🔧 Starting maintenance tasks...")
    
    tasks = [
        ("Log rotation", log_rotation),
        ("Cleanup temp files", cleanup_temp_files), 
        ("Check disk space", check_disk_space),
        ("Security scan", security_scan)
    ]
    
    results = []
    for task_name, task_func in tasks:
        print(f"  Running: {task_name}")
        try:
            success = task_func()
            results.append((task_name, success))
            status = "✅" if success else "⚠️"
            print(f"  {status} {task_name}")
        except Exception as e:
            results.append((task_name, False))
            print(f"  ❌ {task_name}: {e}")
    
    # Summary
    successful = len([r for r in results if r[1]])
    total = len(results)
    print(f"\nMaintenance completed: {successful}/{total} tasks successful")
    
    return successful == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
```

## 📞 Support & Troubleshooting

### 1. **Support Contacts**

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Critical Security | security-team@company.com | 15 minutes |
| Service Down | ops-team@company.com | 30 minutes |
| Performance Issues | performance-team@company.com | 2 hours |
| General Support | support@company.com | 24 hours |

### 2. **Common Troubleshooting**

**Service Won't Start**:
```bash
# Check service status
sudo systemctl status gui-terminal

# Check logs
journalctl -u gui-terminal -f

# Check configuration
python -m json.tool /opt/gui-terminal/config/production_config.json

# Test configuration loading
cd /opt/gui-terminal
./venv/bin/python -c "from src.enhanced_pty_terminal import ConfigurationManager; cm = ConfigurationManager(); print('Config OK')"
```

**High Memory Usage**:
```bash
# Check memory usage
ps aux | grep gui-terminal

# Check for memory leaks
valgrind --tool=massif ./venv/bin/python src/enhanced_pty_terminal.py

# Restart service
sudo systemctl restart gui-terminal
```

**Security Issues**:
```bash
# Check security logs
tail -f /opt/gui-terminal/logs/security_audit.log

# Review recent violations
grep "SECURITY VIOLATION" /opt/gui-terminal/logs/security_audit.log | tail -20

# Check compliance rules
cat /opt/gui-terminal/config/compliance_rules.json
```

## 📈 Scaling & Performance

### 1. **Horizontal Scaling**

For high-load environments, deploy multiple instances:

```bash
# Create additional service instances
sudo cp /etc/systemd/system/gui-terminal.service /etc/systemd/system/gui-terminal-2.service

# Modify port and config
sudo sed -i 's/8080/8081/g' /etc/systemd/system/gui-terminal-2.service
sudo sed -i 's/production_config/production_config_2/g' /etc/systemd/system/gui-terminal-2.service

# Enable and start
sudo systemctl enable gui-terminal-2
sudo systemctl start gui-terminal-2
```

### 2. **Load Balancer Configuration**

**Nginx Configuration**:
```nginx
upstream gui_terminal_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name gui-terminal.company.com;
    
    location / {
        proxy_pass http://gui_terminal_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /health {
        access_log off;
        proxy_pass http://gui_terminal_backend/health;
    }
}
```

## ✅ Go-Live Checklist

### Pre-Production
- [ ] All tests passing (>95% success rate)
- [ ] Security review completed
- [ ] Performance benchmarks met
- [ ] Configuration reviewed and approved
- [ ] Backup/recovery procedures tested
- [ ] Monitoring/alerting configured
- [ ] Documentation completed
- [ ] Team training completed

### Production Deployment
- [ ] Maintenance window scheduled
- [ ] Backup completed
- [ ] Application deployed
- [ ] Configuration updated
- [ ] Services started
- [ ] Smoke tests passed
- [ ] Monitoring active
- [ ] Team notified

### Post-Deployment
- [ ] Monitor for 24 hours
- [ ] Verify all functionality
- [ ] Check performance metrics
- [ ] Review security logs
- [ ] Update documentation
- [ ] Conduct retrospective

---

## 📞 Emergency Contacts

**Critical Issues (24/7)**:
- On-call Engineer: +1-555-ONCALL
- Security Team: security-emergency@company.com
- Operations Manager: ops-manager@company.com

**Escalation Path**:
1. On-call Engineer (0-15 minutes)
2. Team Lead (15-30 minutes)  
3. Engineering Manager (30-60 minutes)
4. CTO (1+ hours for critical business impact)

---

*Last Updated: December 2024*  
*Version: 1.0*  
*Next Review: March 2025*