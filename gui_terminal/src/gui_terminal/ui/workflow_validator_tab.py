"""
Workflow Validator Tab
Validates APF JSON inputs and AI workflow configurations
"""

from __future__ import annotations
import json
import os
import subprocess
from typing import Dict, List, Any, Optional

try:
    from PyQt6 import QtWidgets, QtGui, QtCore  # type: ignore
    from PyQt6.QtCore import Qt, pyqtSignal  # type: ignore
    from PyQt6.QtWidgets import QMessageBox  # type: ignore
except Exception:  # pragma: no cover
    QtWidgets = None
    QtGui = None
    QtCore = None
    Qt = None
    pyqtSignal = None
    QMessageBox = None


class APFValidatorWidget(QtWidgets.QWidget):
    """Widget for validating APF JSON inputs"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Input section
        input_group = QtWidgets.QGroupBox("APF JSON Input")
        input_layout = QtWidgets.QVBoxLayout(input_group)

        # File selection
        file_layout = QtWidgets.QHBoxLayout()
        self.file_path = QtWidgets.QLineEdit()
        self.file_path.setPlaceholderText("Select APF JSON file or paste content below")
        file_layout.addWidget(self.file_path)

        self.browse_btn = QtWidgets.QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(self.browse_btn)

        input_layout.addLayout(file_layout)

        # JSON editor
        self.json_editor = QtWidgets.QTextEdit()
        self.json_editor.setMinimumHeight(200)
        self.json_editor.setPlaceholderText("""Paste APF JSON here, for example:
{
  "schema_version": "apf.phased_repo_plan.v1",
  "tasks": [
    {
      "action": "create_file",
      "path": "src/example.py",
      "instructions": "Create a simple Python module",
      "commands": ["touch src/example.py"]
    }
  ],
  "commit_message": "feat: add example module"
}""")
        input_layout.addWidget(self.json_editor)

        layout.addWidget(input_group)

        # Validation controls
        controls_layout = QtWidgets.QHBoxLayout()

        self.validate_btn = QtWidgets.QPushButton("Validate APF JSON")
        self.validate_btn.clicked.connect(self._validate_apf)
        controls_layout.addWidget(self.validate_btn)

        self.format_btn = QtWidgets.QPushButton("Format JSON")
        self.format_btn.clicked.connect(self._format_json)
        controls_layout.addWidget(self.format_btn)

        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.clicked.connect(self._clear_input)
        controls_layout.addWidget(self.clear_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Results section
        results_group = QtWidgets.QGroupBox("Validation Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)

        self.results_table = QtWidgets.QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Path", "Rule", "Severity", "Message"])

        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 150)  # Path
        header.resizeSection(1, 100)  # Rule
        header.resizeSection(2, 100)  # Severity

        results_layout.addWidget(self.results_table)

        # Summary
        self.summary_label = QtWidgets.QLabel("Ready to validate")
        self.summary_label.setStyleSheet("font-weight: bold; padding: 5px;")
        results_layout.addWidget(self.summary_label)

        layout.addWidget(results_group)

    def _browse_file(self):
        """Browse for APF JSON file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select APF JSON File", "", "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.file_path.setText(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.json_editor.setPlainText(content)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read file: {e}")

    def _format_json(self):
        """Format JSON content"""
        try:
            content = self.json_editor.toPlainText()
            if content.strip():
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.json_editor.setPlainText(formatted)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "JSON Error", f"Invalid JSON: {e}")

    def _clear_input(self):
        """Clear input fields"""
        self.file_path.clear()
        self.json_editor.clear()
        self.results_table.setRowCount(0)
        self.summary_label.setText("Ready to validate")

    def _validate_apf(self):
        """Validate APF JSON against schema"""
        content = self.json_editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Warning", "No content to validate")
            return

        try:
            # Parse JSON
            apf_data = json.loads(content)

            # Basic APF validation (placeholder)
            validation_results = self._run_apf_validation(apf_data)

            # Display results
            self._display_validation_results(validation_results)

        except json.JSONDecodeError as e:
            # JSON syntax error
            self.results_table.setRowCount(1)
            self.results_table.setItem(0, 0, QtWidgets.QTableWidgetItem("JSON Syntax"))
            self.results_table.setItem(0, 1, QtWidgets.QTableWidgetItem("parse_error"))
            self.results_table.setItem(0, 2, QtWidgets.QTableWidgetItem("Error"))
            self.results_table.setItem(0, 3, QtWidgets.QTableWidgetItem(str(e)))

            # Set error styling
            for col in range(4):
                item = self.results_table.item(0, col)
                if item:
                    item.setBackground(QtGui.QColor(255, 200, 200))

            self.summary_label.setText("❌ JSON Syntax Error")
            self.summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: red;")

    def _run_apf_validation(self, apf_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Run APF validation checks"""
        results = []

        # Check required fields
        required_fields = ["schema_version", "tasks"]
        for field in required_fields:
            if field not in apf_data:
                results.append({
                    "path": f"/{field}",
                    "rule": "required",
                    "severity": "Error",
                    "message": f"Missing required field: {field}"
                })

        # Check schema version
        if "schema_version" in apf_data:
            if apf_data["schema_version"] != "apf.phased_repo_plan.v1":
                results.append({
                    "path": "/schema_version",
                    "rule": "version",
                    "severity": "Warning",
                    "message": f"Unsupported schema version: {apf_data['schema_version']}"
                })

        # Check tasks structure
        if "tasks" in apf_data:
            if not isinstance(apf_data["tasks"], list):
                results.append({
                    "path": "/tasks",
                    "rule": "type",
                    "severity": "Error",
                    "message": "Tasks must be an array"
                })
            else:
                for i, task in enumerate(apf_data["tasks"]):
                    if not isinstance(task, dict):
                        results.append({
                            "path": f"/tasks/{i}",
                            "rule": "type",
                            "severity": "Error",
                            "message": "Each task must be an object"
                        })
                        continue

                    # Check required task fields
                    required_task_fields = ["action"]
                    for field in required_task_fields:
                        if field not in task:
                            results.append({
                                "path": f"/tasks/{i}/{field}",
                                "rule": "required",
                                "severity": "Error",
                                "message": f"Missing required task field: {field}"
                            })

        # If no errors, add success message
        if not results:
            results.append({
                "path": "/",
                "rule": "validation",
                "severity": "Success",
                "message": "APF JSON is valid"
            })

        return results

    def _display_validation_results(self, results: List[Dict[str, str]]):
        """Display validation results in table"""
        self.results_table.setRowCount(len(results))

        error_count = 0
        warning_count = 0
        success_count = 0

        for row, result in enumerate(results):
            self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(result["path"]))
            self.results_table.setItem(row, 1, QtWidgets.QTableWidgetItem(result["rule"]))
            self.results_table.setItem(row, 2, QtWidgets.QTableWidgetItem(result["severity"]))
            self.results_table.setItem(row, 3, QtWidgets.QTableWidgetItem(result["message"]))

            # Apply styling based on severity
            severity = result["severity"]
            if severity == "Error":
                color = QtGui.QColor(255, 200, 200)
                error_count += 1
            elif severity == "Warning":
                color = QtGui.QColor(255, 255, 200)
                warning_count += 1
            elif severity == "Success":
                color = QtGui.QColor(200, 255, 200)
                success_count += 1
            else:
                color = QtGui.QColor(240, 240, 240)

            for col in range(4):
                item = self.results_table.item(row, col)
                if item:
                    item.setBackground(color)

        # Update summary
        if error_count > 0:
            self.summary_label.setText(f"❌ {error_count} errors, {warning_count} warnings")
            self.summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: red;")
        elif warning_count > 0:
            self.summary_label.setText(f"⚠️ {warning_count} warnings, validation passed")
            self.summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: orange;")
        else:
            self.summary_label.setText("✅ Validation passed successfully")
            self.summary_label.setStyleSheet("font-weight: bold; padding: 5px; color: green;")


class AIConfigValidatorWidget(QtWidgets.QWidget):
    """Widget for validating AI workflow configuration"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Config file section
        config_group = QtWidgets.QGroupBox("AI Workflow Configuration")
        config_layout = QtWidgets.QVBoxLayout(config_group)

        # File path
        file_layout = QtWidgets.QHBoxLayout()
        self.config_path = QtWidgets.QLineEdit()
        self.config_path.setText(".github/ai-workflow-config.yml")
        file_layout.addWidget(QtWidgets.QLabel("Config File:"))
        file_layout.addWidget(self.config_path)

        self.browse_config_btn = QtWidgets.QPushButton("Browse...")
        self.browse_config_btn.clicked.connect(self._browse_config)
        file_layout.addWidget(self.browse_config_btn)

        config_layout.addLayout(file_layout)

        # Config editor
        self.config_editor = QtWidgets.QTextEdit()
        self.config_editor.setMinimumHeight(250)
        self.config_editor.setPlaceholderText("""AI Workflow Config (YAML):
ai_tools:
  planner: "claude-3.5-sonnet"
  implementer: "kodex-2.1"
quality_gates:
  require_jsonl_logs: true
  vuln_cutoff: "high"
notifications:
  slack_webhook_secret: "SLACK_WEBHOOK_URL"
timeouts:
  plan_s: 300
  implement_s: 1200
  validate_s: 600""")
        config_layout.addWidget(self.config_editor)

        layout.addWidget(config_group)

        # Validation controls
        controls_layout = QtWidgets.QHBoxLayout()

        self.validate_config_btn = QtWidgets.QPushButton("Validate Config")
        self.validate_config_btn.clicked.connect(self._validate_config)
        controls_layout.addWidget(self.validate_config_btn)

        self.load_config_btn = QtWidgets.QPushButton("Load from File")
        self.load_config_btn.clicked.connect(self._load_config)
        controls_layout.addWidget(self.load_config_btn)

        self.save_config_btn = QtWidgets.QPushButton("Save to File")
        self.save_config_btn.clicked.connect(self._save_config)
        controls_layout.addWidget(self.save_config_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Quick fixes section
        fixes_group = QtWidgets.QGroupBox("Quick Fixes")
        fixes_layout = QtWidgets.QHBoxLayout(fixes_group)

        self.apply_defaults_btn = QtWidgets.QPushButton("Apply Defaults")
        self.apply_defaults_btn.clicked.connect(self._apply_defaults)
        fixes_layout.addWidget(self.apply_defaults_btn)

        self.check_secrets_btn = QtWidgets.QPushButton("Check Secrets")
        self.check_secrets_btn.clicked.connect(self._check_secrets)
        fixes_layout.addWidget(self.check_secrets_btn)

        fixes_layout.addStretch()
        layout.addWidget(fixes_group)

        # Status
        self.config_status = QtWidgets.QLabel("Ready to validate AI workflow configuration")
        self.config_status.setStyleSheet("padding: 10px; background: #f5f5f5; border: 1px solid #ddd;")
        layout.addWidget(self.config_status)

    def _browse_config(self):
        """Browse for AI config file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select AI Config File", ".github/", "YAML Files (*.yml *.yaml);;All Files (*)"
        )

        if file_path:
            self.config_path.setText(file_path)

    def _load_config(self):
        """Load config from file"""
        file_path = self.config_path.text()
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.config_editor.setPlainText(content)
                self.config_status.setText(f"✅ Loaded config from {file_path}")
        except FileNotFoundError:
            self.config_status.setText(f"❌ File not found: {file_path}")
        except Exception as e:
            self.config_status.setText(f"❌ Failed to load config: {e}")

    def _save_config(self):
        """Save config to file"""
        file_path = self.config_path.text()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please specify a file path")
            return

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.config_editor.toPlainText())

            self.config_status.setText(f"✅ Saved config to {file_path}")
        except Exception as e:
            self.config_status.setText(f"❌ Failed to save config: {e}")

    def _validate_config(self):
        """Validate AI workflow configuration"""
        # Placeholder validation
        content = self.config_editor.toPlainText()
        if not content.strip():
            self.config_status.setText("❌ No configuration to validate")
            return

        try:
            import yaml
            config_data = yaml.safe_load(content)

            # Basic validation
            required_sections = ["ai_tools", "quality_gates", "timeouts"]
            missing_sections = [s for s in required_sections if s not in config_data]

            if missing_sections:
                self.config_status.setText(f"❌ Missing sections: {', '.join(missing_sections)}")
            else:
                self.config_status.setText("✅ Configuration is valid")

        except yaml.YAMLError as e:
            self.config_status.setText(f"❌ YAML syntax error: {e}")
        except Exception as e:
            self.config_status.setText(f"❌ Validation error: {e}")

    def _apply_defaults(self):
        """Apply default configuration"""
        default_config = """ai_tools:
  planner: "claude-3.5-sonnet"
  implementer: "kodex-2.1"
  validator: "claude-3.5-sonnet"

quality_gates:
  require_jsonl_logs: true
  vuln_cutoff: "high"
  test_coverage_min: 80
  linting_required: true

notifications:
  slack_webhook_secret: "SLACK_WEBHOOK_URL"
  email_on_failure: true

timeouts:
  plan_s: 300
  implement_s: 1200
  validate_s: 600

retry_policy:
  max_attempts: 3
  backoff_multiplier: 2"""

        self.config_editor.setPlainText(default_config)
        self.config_status.setText("✅ Default configuration applied")

    def _check_secrets(self):
        """Check if required secrets are configured"""
        # Placeholder implementation
        self.config_status.setText("ℹ️ Secret checking would verify GitHub secrets are configured")


class WorkflowValidatorTab(QtWidgets.QWidget):
    """Main Workflow Validator tab widget"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("Workflow Validator")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Tab widget for different validation types
        tab_widget = QtWidgets.QTabWidget()

        # APF validator tab
        self.apf_validator = APFValidatorWidget()
        tab_widget.addTab(self.apf_validator, "APF JSON Validator")

        # AI config validator tab
        self.ai_config_validator = AIConfigValidatorWidget()
        tab_widget.addTab(self.ai_config_validator, "AI Config Validator")

        layout.addWidget(tab_widget)

        # Global status
        self.global_status = QtWidgets.QLabel("Select a validator to begin")
        self.global_status.setStyleSheet("border: 1px solid #ccc; padding: 8px; background: #f9f9f9;")
        layout.addWidget(self.global_status)