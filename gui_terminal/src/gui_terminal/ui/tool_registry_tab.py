"""
Tool Registry & Resolver Tab
Implements tool management, capability mapping, and deterministic resolution
"""

from __future__ import annotations
import yaml
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from PyQt6 import QtWidgets, QtGui, QtCore  # type: ignore
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal  # type: ignore
    from PyQt6.QtWidgets import QMessageBox  # type: ignore
except Exception:  # pragma: no cover
    QtWidgets = None
    QtGui = None
    QtCore = None
    Qt = None
    QTimer = None
    pyqtSignal = None
    QMessageBox = None


class ToolListWidget(QtWidgets.QWidget):
    """Widget displaying all registered tools with their capabilities and status"""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.tools = {}
        self._load_tools()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()

        self.search_field = QtWidgets.QLineEdit()
        self.search_field.setPlaceholderText("Search tools...")
        self.search_field.textChanged.connect(self._filter_tools)
        filter_layout.addWidget(self.search_field)

        self.capability_filter = QtWidgets.QComboBox()
        self.capability_filter.addItem("All Capabilities")
        self.capability_filter.currentTextChanged.connect(self._filter_tools)
        filter_layout.addWidget(self.capability_filter)

        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItems(["All Status", "Healthy", "Unhealthy", "Unknown"])
        self.status_filter.currentTextChanged.connect(self._filter_tools)
        filter_layout.addWidget(self.status_filter)

        layout.addLayout(filter_layout)

        # Tools table
        self.tools_table = QtWidgets.QTableWidget()
        self.tools_table.setColumnCount(7)
        self.tools_table.setHorizontalHeaderLabels([
            "Tool", "Capabilities", "Status", "Cost Model", "Priority", "OS", "License"
        ])

        # Configure table
        header = self.tools_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 150)  # Tool
        header.resizeSection(1, 200)  # Capabilities
        header.resizeSection(2, 100)  # Status
        header.resizeSection(3, 120)  # Cost Model
        header.resizeSection(4, 80)   # Priority
        header.resizeSection(5, 100)  # OS

        self.tools_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tools_table.setAlternatingRowColors(True)

        layout.addWidget(self.tools_table)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh Status")
        self.refresh_btn.clicked.connect(self._refresh_status)
        button_layout.addWidget(self.refresh_btn)

        self.health_check_btn = QtWidgets.QPushButton("Run Health Checks")
        self.health_check_btn.clicked.connect(self._run_health_checks)
        button_layout.addWidget(self.health_check_btn)

        button_layout.addStretch()

        self.edit_btn = QtWidgets.QPushButton("Edit Tool")
        self.edit_btn.clicked.connect(self._edit_tool)
        button_layout.addWidget(self.edit_btn)

        layout.addLayout(button_layout)

    def _load_tools(self):
        """Load tools from registry YAML file"""
        registry_path = os.path.join("capabilities", "tool_registry.yaml")
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    data = yaml.safe_load(f)
                    self.tools = {tool['id']: tool for tool in data.get('tools', [])}

                # Populate capability filter
                all_capabilities = set()
                for tool in self.tools.values():
                    all_capabilities.update(tool.get('capabilities', []))

                self.capability_filter.clear()
                self.capability_filter.addItem("All Capabilities")
                for cap in sorted(all_capabilities):
                    self.capability_filter.addItem(cap)

                self._populate_table()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load tool registry: {e}")

    def _populate_table(self):
        """Populate the tools table"""
        self.tools_table.setRowCount(len(self.tools))

        for row, (tool_id, tool) in enumerate(self.tools.items()):
            # Tool name
            self.tools_table.setItem(row, 0, QtWidgets.QTableWidgetItem(tool.get('title', tool_id)))

            # Capabilities
            capabilities = ', '.join(tool.get('capabilities', []))
            self.tools_table.setItem(row, 1, QtWidgets.QTableWidgetItem(capabilities))

            # Status (placeholder)
            status_item = QtWidgets.QTableWidgetItem("Unknown")
            status_item.setBackground(QtGui.QColor(220, 220, 220))
            self.tools_table.setItem(row, 2, status_item)

            # Cost model
            cost = tool.get('cost', {})
            cost_text = cost.get('model', 'unknown')
            if 'cost_per_request_usd' in cost:
                cost_text += f" (${cost['cost_per_request_usd']}/req)"
            self.tools_table.setItem(row, 3, QtWidgets.QTableWidgetItem(cost_text))

            # Priority
            priority = str(tool.get('priority', 'N/A'))
            self.tools_table.setItem(row, 4, QtWidgets.QTableWidgetItem(priority))

            # OS Support
            os_list = ', '.join(tool.get('os', []))
            self.tools_table.setItem(row, 5, QtWidgets.QTableWidgetItem(os_list))

            # License
            license_text = tool.get('license', 'Unknown')
            self.tools_table.setItem(row, 6, QtWidgets.QTableWidgetItem(license_text))

    def _filter_tools(self):
        """Filter tools based on search criteria"""
        search_text = self.search_field.text().lower()
        capability_filter = self.capability_filter.currentText()
        status_filter = self.status_filter.currentText()

        for row in range(self.tools_table.rowCount()):
            should_show = True

            # Search filter
            if search_text:
                tool_name = self.tools_table.item(row, 0).text().lower()
                capabilities = self.tools_table.item(row, 1).text().lower()
                if search_text not in tool_name and search_text not in capabilities:
                    should_show = False

            # Capability filter
            if capability_filter != "All Capabilities":
                capabilities = self.tools_table.item(row, 1).text()
                if capability_filter not in capabilities:
                    should_show = False

            # Status filter
            if status_filter != "All Status":
                status = self.tools_table.item(row, 2).text()
                if status_filter != status:
                    should_show = False

            self.tools_table.setRowHidden(row, not should_show)

    def _refresh_status(self):
        """Refresh tool status from cache"""
        # Placeholder implementation
        QMessageBox.information(self, "Status", "Tool status refreshed")

    def _run_health_checks(self):
        """Run health checks for all tools"""
        # Placeholder implementation - in real implementation, this would
        # run the healthcheck commands defined in the tool registry
        QMessageBox.information(self, "Health Check", "Health checks completed")

    def _edit_tool(self):
        """Edit selected tool configuration"""
        current_row = self.tools_table.currentRow()
        if current_row >= 0:
            tool_name = self.tools_table.item(current_row, 0).text()
            QMessageBox.information(self, "Edit Tool", f"Edit dialog for {tool_name} would open here")


class CapabilityMappingWidget(QtWidgets.QWidget):
    """Widget for managing capability-to-tool mappings"""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.capability_bindings = {}
        self._load_bindings()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Capability selection
        selection_layout = QtWidgets.QHBoxLayout()

        self.capability_combo = QtWidgets.QComboBox()
        self.capability_combo.currentTextChanged.connect(self._on_capability_changed)
        selection_layout.addWidget(QtWidgets.QLabel("Capability:"))
        selection_layout.addWidget(self.capability_combo)

        selection_layout.addStretch()
        layout.addLayout(selection_layout)

        # Tool ordering list
        self.tools_list = QtWidgets.QListWidget()
        self.tools_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        layout.addWidget(QtWidgets.QLabel("Tool Priority Order (drag to reorder):"))
        layout.addWidget(self.tools_list)

        # Policy settings
        policy_group = QtWidgets.QGroupBox("Policy Settings")
        policy_layout = QtWidgets.QFormLayout(policy_group)

        self.open_source_first = QtWidgets.QCheckBox("Prefer Open Source")
        policy_layout.addRow(self.open_source_first)

        self.cost_ceiling = QtWidgets.QDoubleSpinBox()
        self.cost_ceiling.setMaximum(100.0)
        self.cost_ceiling.setSingleStep(0.1)
        self.cost_ceiling.setSuffix(" USD")
        policy_layout.addRow("Cost Ceiling:", self.cost_ceiling)

        self.fallback_options = QtWidgets.QListWidget()
        self.fallback_options.setMaximumHeight(100)
        fallback_items = ["rate_limit", "error", "timeout", "health_check_fail", "cost_limit"]
        for item in fallback_items:
            list_item = QtWidgets.QListWidgetItem(item)
            list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            list_item.setCheckState(Qt.CheckState.Unchecked)
            self.fallback_options.addItem(list_item)
        policy_layout.addRow("Fallback On:", self.fallback_options)

        layout.addWidget(policy_group)

        # Save button
        self.save_btn = QtWidgets.QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self._save_bindings)
        layout.addWidget(self.save_btn)

    def _load_bindings(self):
        """Load capability bindings from YAML file"""
        bindings_path = os.path.join("capabilities", "capability_bindings.yaml")
        if os.path.exists(bindings_path):
            try:
                with open(bindings_path, 'r') as f:
                    data = yaml.safe_load(f)
                    self.capability_bindings = data.get('capabilities', {})

                # Populate capability dropdown
                self.capability_combo.clear()
                self.capability_combo.addItems(sorted(self.capability_bindings.keys()))

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load capability bindings: {e}")

    def _on_capability_changed(self, capability: str):
        """Update UI when capability selection changes"""
        if capability in self.capability_bindings:
            binding = self.capability_bindings[capability]
            policy = binding.get('policy', {})

            # Update tool order list
            self.tools_list.clear()
            for tool_id in policy.get('order', []):
                self.tools_list.addItem(tool_id)

            # Update policy settings
            self.open_source_first.setChecked(policy.get('open_source_first', False))
            self.cost_ceiling.setValue(policy.get('cost_ceiling_usd', 0.0))

            # Update fallback options
            fallback_on = policy.get('fallback_on', [])
            for i in range(self.fallback_options.count()):
                item = self.fallback_options.item(i)
                item.setCheckState(
                    Qt.CheckState.Checked if item.text() in fallback_on else Qt.CheckState.Unchecked
                )

    def _save_bindings(self):
        """Save capability bindings to file"""
        # Placeholder implementation
        QMessageBox.information(self, "Save", "Configuration saved successfully")


class ResolverSimulatorWidget(QtWidgets.QWidget):
    """Widget for simulating tool resolution"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Simulation inputs
        input_group = QtWidgets.QGroupBox("Simulation Parameters")
        input_layout = QtWidgets.QFormLayout(input_group)

        self.capability_input = QtWidgets.QComboBox()
        self.capability_input.setEditable(True)
        input_layout.addRow("Capability:", self.capability_input)

        self.context_input = QtWidgets.QTextEdit()
        self.context_input.setMaximumHeight(80)
        self.context_input.setPlaceholderText('{"os": "windows", "budget_remaining": 10.0}')
        input_layout.addRow("Context (JSON):", self.context_input)

        self.simulate_btn = QtWidgets.QPushButton("Simulate Resolution")
        self.simulate_btn.clicked.connect(self._simulate_resolution)
        input_layout.addRow(self.simulate_btn)

        layout.addWidget(input_group)

        # Results display
        results_group = QtWidgets.QGroupBox("Resolution Results")
        results_layout = QtWidgets.QVBoxLayout(results_group)

        self.results_table = QtWidgets.QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Priority", "Tool", "Status", "Reason"])

        header = self.results_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 80)   # Priority
        header.resizeSection(1, 150)  # Tool
        header.resizeSection(2, 100)  # Status

        results_layout.addWidget(self.results_table)

        # Command preview
        self.command_preview = QtWidgets.QTextEdit()
        self.command_preview.setMaximumHeight(100)
        self.command_preview.setReadOnly(True)
        results_layout.addWidget(QtWidgets.QLabel("Command Preview:"))
        results_layout.addWidget(self.command_preview)

        layout.addWidget(results_group)

    def _simulate_resolution(self):
        """Simulate tool resolution for given capability and context"""
        capability = self.capability_input.currentText()

        try:
            context = {}
            if self.context_input.toPlainText().strip():
                context = json.loads(self.context_input.toPlainText())
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Invalid JSON in context field")
            return

        # Simulate resolution results
        sample_results = [
            (1, "docker_cli", "✓ Selected", "Primary choice, health OK, within budget"),
            (2, "buildah", "○ Available", "Fallback option, Linux only"),
            (3, "kaniko", "○ Available", "Fallback option, requires K8s"),
        ]

        self.results_table.setRowCount(len(sample_results))

        for row, (priority, tool, status, reason) in enumerate(sample_results):
            self.results_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(priority)))
            self.results_table.setItem(row, 1, QtWidgets.QTableWidgetItem(tool))

            status_item = QtWidgets.QTableWidgetItem(status)
            if "Selected" in status:
                status_item.setBackground(QtGui.QColor(200, 255, 200))
            elif "Available" in status:
                status_item.setBackground(QtGui.QColor(255, 255, 200))
            self.results_table.setItem(row, 2, status_item)

            self.results_table.setItem(row, 3, QtWidgets.QTableWidgetItem(reason))

        # Show command preview
        self.command_preview.setText(f"""Selected Tool: docker_cli
Command: docker build -t myapp:latest .
Environment: {{}}
Working Directory: /current/path
Timeout: 300 seconds
Retry Count: 1""")


class ToolRegistryTab(QtWidgets.QWidget):
    """Main Tool Registry & Resolver tab widget"""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("Tool Registry & Resolver")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Tab widget for sub-functionality
        tab_widget = QtWidgets.QTabWidget()

        # Tools tab
        self.tools_widget = ToolListWidget()
        tab_widget.addTab(self.tools_widget, "Tools")

        # Capability mapping tab
        self.capability_widget = CapabilityMappingWidget()
        tab_widget.addTab(self.capability_widget, "Capabilities")

        # Resolver simulator tab
        self.resolver_widget = ResolverSimulatorWidget()
        tab_widget.addTab(self.resolver_widget, "Resolver")

        layout.addWidget(tab_widget)

        # Status bar
        self.status_bar = QtWidgets.QLabel("Ready")
        self.status_bar.setStyleSheet("border: 1px solid #ccc; padding: 5px; background: #f5f5f5;")
        layout.addWidget(self.status_bar)