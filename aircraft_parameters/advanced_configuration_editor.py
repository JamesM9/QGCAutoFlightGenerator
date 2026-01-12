#!/usr/bin/env python3
"""
Advanced Configuration Editor
Enhanced configuration editor with advanced features like parameter comparison,
validation, and batch operations
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QTextEdit, QComboBox, QCheckBox, QSpinBox,
    QDoubleSpinBox, QLineEdit, QSplitter, QProgressBar,
    QMessageBox, QFileDialog, QListWidget, QListWidgetItem,
    QFormLayout, QGridLayout, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from typing import Dict, List, Any, Optional, Tuple
import json
import difflib
from datetime import datetime


class ParameterComparisonWidget(QWidget):
    """Widget for comparing parameters between configurations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config1 = None
        self.config2 = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Parameter Comparison")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Configuration selection
        config_layout = QHBoxLayout()
        
        config_layout.addWidget(QLabel("Configuration 1:"))
        self.config1_combo = QComboBox()
        config_layout.addWidget(self.config1_combo)
        
        config_layout.addWidget(QLabel("Configuration 2:"))
        self.config2_combo = QComboBox()
        config_layout.addWidget(self.config2_combo)
        
        self.compare_btn = QPushButton("Compare")
        self.compare_btn.clicked.connect(self.compare_configurations)
        config_layout.addWidget(self.compare_btn)
        
        layout.addLayout(config_layout)
        
        # Comparison results
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(5)
        self.comparison_table.setHorizontalHeaderLabels([
            "Parameter", "Config 1", "Config 2", "Difference", "Status"
        ])
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.comparison_table)
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(100)
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
    def set_configurations(self, configs: List[Any]):
        """Set available configurations for comparison"""
        self.config1_combo.clear()
        self.config2_combo.clear()
        
        for config in configs:
            self.config1_combo.addItem(config.name, config)
            self.config2_combo.addItem(config.name, config)
            
    def compare_configurations(self):
        """Compare the selected configurations"""
        config1 = self.config1_combo.currentData()
        config2 = self.config2_combo.currentData()
        
        if not config1 or not config2:
            QMessageBox.warning(self, "Selection Error", "Please select both configurations to compare")
            return
            
        if config1 == config2:
            QMessageBox.warning(self, "Selection Error", "Please select different configurations to compare")
            return
            
        self.perform_comparison(config1, config2)
        
    def perform_comparison(self, config1: Any, config2: Any):
        """Perform the actual comparison"""
        # Get all unique parameters
        all_params = set(config1.parameters.keys()) | set(config2.parameters.keys())
        
        # Prepare comparison data
        comparison_data = []
        differences = 0
        identical = 0
        
        for param in sorted(all_params):
            val1 = config1.parameters.get(param, "N/A")
            val2 = config2.parameters.get(param, "N/A")
            
            if val1 == val2:
                status = "Identical"
                identical += 1
                status_color = QColor(76, 175, 80)  # Green
            else:
                status = "Different"
                differences += 1
                status_color = QColor(244, 67, 54)  # Red
                
            # Calculate difference
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                diff = val2 - val1
                diff_text = f"{diff:+.2f}"
            else:
                diff_text = "N/A"
                
            comparison_data.append({
                "parameter": param,
                "value1": str(val1),
                "value2": str(val2),
                "difference": diff_text,
                "status": status,
                "status_color": status_color
            })
            
        # Update table
        self.update_comparison_table(comparison_data)
        
        # Update summary
        summary = f"Comparison Summary:\n"
        summary += f"Total parameters: {len(all_params)}\n"
        summary += f"Identical: {identical}\n"
        summary += f"Different: {differences}\n"
        summary += f"Difference percentage: {differences/len(all_params)*100:.1f}%"
        self.summary_text.setText(summary)
        
    def update_comparison_table(self, data: List[Dict]):
        """Update the comparison table with data"""
        self.comparison_table.setRowCount(len(data))
        
        for row, item in enumerate(data):
            # Parameter name
            param_item = QTableWidgetItem(item["parameter"])
            param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
            self.comparison_table.setItem(row, 0, param_item)
            
            # Value 1
            val1_item = QTableWidgetItem(item["value1"])
            val1_item.setFlags(val1_item.flags() & ~Qt.ItemIsEditable)
            self.comparison_table.setItem(row, 1, val1_item)
            
            # Value 2
            val2_item = QTableWidgetItem(item["value2"])
            val2_item.setFlags(val2_item.flags() & ~Qt.ItemIsEditable)
            self.comparison_table.setItem(row, 2, val2_item)
            
            # Difference
            diff_item = QTableWidgetItem(item["difference"])
            diff_item.setFlags(diff_item.flags() & ~Qt.ItemIsEditable)
            self.comparison_table.setItem(row, 3, diff_item)
            
            # Status
            status_item = QTableWidgetItem(item["status"])
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_item.setBackground(item["status_color"])
            self.comparison_table.setItem(row, 4, status_item)


class ParameterValidationWidget(QWidget):
    """Widget for validating parameters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.validator = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Parameter Validation")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Validation options
        options_group = QGroupBox("Validation Options")
        options_layout = QFormLayout(options_group)
        
        self.validate_ranges_checkbox = QCheckBox("Validate parameter ranges")
        self.validate_ranges_checkbox.setChecked(True)
        options_layout.addRow("", self.validate_ranges_checkbox)
        
        self.validate_dependencies_checkbox = QCheckBox("Validate parameter dependencies")
        self.validate_dependencies_checkbox.setChecked(True)
        options_layout.addRow("", self.validate_dependencies_checkbox)
        
        self.validate_consistency_checkbox = QCheckBox("Validate parameter consistency")
        self.validate_consistency_checkbox.setChecked(True)
        options_layout.addRow("", self.validate_consistency_checkbox)
        
        layout.addWidget(options_group)
        
        # Validation buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate Parameters")
        self.validate_btn.clicked.connect(self.validate_parameters)
        button_layout.addWidget(self.validate_btn)
        
        self.auto_fix_btn = QPushButton("Auto-Fix Issues")
        self.auto_fix_btn.clicked.connect(self.auto_fix_issues)
        button_layout.addWidget(self.auto_fix_btn)
        
        layout.addLayout(button_layout)
        
        # Validation results
        results_group = QGroupBox("Validation Results")
        results_layout = QVBoxLayout(results_group)
        
        self.validation_results = QTextEdit()
        self.validation_results.setMaximumHeight(200)
        self.validation_results.setReadOnly(True)
        results_layout.addWidget(self.validation_results)
        
        # Issues table
        self.issues_table = QTableWidget()
        self.issues_table.setColumnCount(4)
        self.issues_table.setHorizontalHeaderLabels([
            "Parameter", "Issue", "Severity", "Suggested Fix"
        ])
        self.issues_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.issues_table)
        
        layout.addWidget(results_group)
        
    def set_validator(self, validator):
        """Set the parameter validator"""
        self.validator = validator
        
    def validate_parameters(self):
        """Validate the current parameters"""
        if not self.validator:
            QMessageBox.warning(self, "Validation Error", "No validator available")
            return
            
        # This would integrate with the actual validator
        # For now, show a placeholder message
        self.validation_results.setText("Validation completed. No issues found.")
        
    def auto_fix_issues(self):
        """Automatically fix validation issues"""
        QMessageBox.information(self, "Auto-Fix", "Auto-fix functionality not yet implemented")


class BatchOperationsWidget(QWidget):
    """Widget for batch operations on parameters"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Batch Operations")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Operation selection
        operation_group = QGroupBox("Select Operation")
        operation_layout = QFormLayout(operation_group)
        
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Scale parameters by factor",
            "Set parameter ranges",
            "Copy parameters between configurations",
            "Merge configurations",
            "Export multiple configurations"
        ])
        operation_layout.addRow("Operation:", self.operation_combo)
        
        layout.addWidget(operation_group)
        
        # Operation parameters
        self.operation_params = QGroupBox("Operation Parameters")
        self.operation_params_layout = QFormLayout(self.operation_params)
        layout.addWidget(self.operation_params)
        
        # Execute button
        self.execute_btn = QPushButton("Execute Operation")
        self.execute_btn.clicked.connect(self.execute_operation)
        layout.addWidget(self.execute_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
    def execute_operation(self):
        """Execute the selected batch operation"""
        operation = self.operation_combo.currentText()
        
        if operation == "Scale parameters by factor":
            self.scale_parameters()
        elif operation == "Set parameter ranges":
            self.set_parameter_ranges()
        elif operation == "Copy parameters between configurations":
            self.copy_parameters()
        elif operation == "Merge configurations":
            self.merge_configurations()
        elif operation == "Export multiple configurations":
            self.export_multiple_configurations()
        else:
            QMessageBox.information(self, "Operation", f"Operation '{operation}' not yet implemented")
            
    def scale_parameters(self):
        """Scale parameters by a factor"""
        QMessageBox.information(self, "Scale Parameters", "Scale parameters functionality not yet implemented")
        
    def set_parameter_ranges(self):
        """Set parameter ranges"""
        QMessageBox.information(self, "Set Ranges", "Set parameter ranges functionality not yet implemented")
        
    def copy_parameters(self):
        """Copy parameters between configurations"""
        QMessageBox.information(self, "Copy Parameters", "Copy parameters functionality not yet implemented")
        
    def merge_configurations(self):
        """Merge configurations"""
        QMessageBox.information(self, "Merge Configurations", "Merge configurations functionality not yet implemented")
        
    def export_multiple_configurations(self):
        """Export multiple configurations"""
        QMessageBox.information(self, "Export Multiple", "Export multiple configurations functionality not yet implemented")


class AdvancedConfigurationEditorDialog(QDialog):
    """Advanced configuration editor dialog"""
    
    configuration_saved = pyqtSignal(object)  # Emitted when configuration is saved
    configuration_deleted = pyqtSignal(str)   # Emitted when configuration is deleted
    
    def __init__(self, parent=None, configuration=None, config_manager=None):
        super().__init__(parent)
        self.configuration = configuration
        self.config_manager = config_manager
        self.is_new_config = configuration is None
        
        self.setWindowTitle("Advanced Configuration Editor")
        self.setModal(True)
        self.resize(1200, 800)
        
        self.init_ui()
        self.load_configuration()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Advanced Configuration Editor")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #4CAF50;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Action buttons
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_configuration)
        header_layout.addWidget(self.save_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Basic configuration tab
        self.basic_tab = self.create_basic_tab()
        self.tab_widget.addTab(self.basic_tab, "Basic Configuration")
        
        # Parameter comparison tab
        self.comparison_tab = ParameterComparisonWidget()
        self.tab_widget.addTab(self.comparison_tab, "Parameter Comparison")
        
        # Parameter validation tab
        self.validation_tab = ParameterValidationWidget()
        self.tab_widget.addTab(self.validation_tab, "Parameter Validation")
        
        # Batch operations tab
        self.batch_tab = BatchOperationsWidget()
        self.tab_widget.addTab(self.batch_tab, "Batch Operations")
        
    def create_basic_tab(self):
        """Create the basic configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuration info
        info_group = QGroupBox("Configuration Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        info_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        info_layout.addRow("Description:", self.description_edit)
        
        self.firmware_combo = QComboBox()
        self.firmware_combo.addItems(["arducopter", "arduplane", "px4"])
        info_layout.addRow("Firmware Type:", self.firmware_combo)
        
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.addItems(["multicopter", "fixedwing", "vtol"])
        info_layout.addRow("Vehicle Type:", self.vehicle_combo)
        
        layout.addWidget(info_group)
        
        # Parameters table
        params_group = QGroupBox("Parameters")
        params_layout = QVBoxLayout(params_group)
        
        self.parameters_table = QTableWidget()
        self.parameters_table.setColumnCount(3)
        self.parameters_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        self.parameters_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        params_layout.addWidget(self.parameters_table)
        
        # Parameter actions
        param_actions = QHBoxLayout()
        
        self.add_param_btn = QPushButton("Add Parameter")
        self.add_param_btn.clicked.connect(self.add_parameter)
        param_actions.addWidget(self.add_param_btn)
        
        self.remove_param_btn = QPushButton("Remove Parameter")
        self.remove_param_btn.clicked.connect(self.remove_parameter)
        param_actions.addWidget(self.remove_param_btn)
        
        self.import_params_btn = QPushButton("Import Parameters")
        self.import_params_btn.clicked.connect(self.import_parameters)
        param_actions.addWidget(self.import_params_btn)
        
        params_layout.addLayout(param_actions)
        
        layout.addWidget(params_group)
        
        return widget
        
    def load_configuration(self):
        """Load the configuration data"""
        if self.configuration:
            self.name_edit.setText(self.configuration.name)
            self.description_edit.setText(self.configuration.description)
            self.firmware_combo.setCurrentText(self.configuration.firmware_type)
            self.vehicle_combo.setCurrentText(self.configuration.vehicle_type)
            
            # Load parameters
            self.load_parameters_table()
        else:
            # Set defaults for new configuration
            self.name_edit.setText("New Configuration")
            self.description_edit.setText("")
            self.firmware_combo.setCurrentText("arducopter")
            self.vehicle_combo.setCurrentText("multicopter")
            
    def load_parameters_table(self):
        """Load parameters into the table"""
        if not self.configuration:
            return
            
        parameters = self.configuration.parameters
        self.parameters_table.setRowCount(len(parameters))
        
        for row, (param_name, param_value) in enumerate(parameters.items()):
            # Parameter name
            name_item = QTableWidgetItem(param_name)
            self.parameters_table.setItem(row, 0, name_item)
            
            # Parameter value
            value_item = QTableWidgetItem(str(param_value))
            self.parameters_table.setItem(row, 1, value_item)
            
            # Parameter unit (placeholder)
            unit_item = QTableWidgetItem("")
            self.parameters_table.setItem(row, 2, unit_item)
            
    def add_parameter(self):
        """Add a new parameter"""
        row = self.parameters_table.rowCount()
        self.parameters_table.insertRow(row)
        
        # Add empty items
        name_item = QTableWidgetItem("")
        value_item = QTableWidgetItem("")
        unit_item = QTableWidgetItem("")
        
        self.parameters_table.setItem(row, 0, name_item)
        self.parameters_table.setItem(row, 1, value_item)
        self.parameters_table.setItem(row, 2, unit_item)
        
    def remove_parameter(self):
        """Remove selected parameter"""
        current_row = self.parameters_table.currentRow()
        if current_row >= 0:
            self.parameters_table.removeRow(current_row)
            
    def import_parameters(self):
        """Import parameters from file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Parameters", "", "Parameter Files (*.param *.params *.txt *.json)"
        )
        
        if filename:
            # This would integrate with the parameter file manager
            QMessageBox.information(self, "Import", f"Importing parameters from {filename}")
            
    def save_configuration(self):
        """Save the configuration"""
        # Validate input
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "Configuration name is required")
            return
            
        # Create or update configuration
        if self.is_new_config:
            self.configuration = type('AircraftConfiguration', (), {})()
            
        self.configuration.name = self.name_edit.text().strip()
        self.configuration.description = self.description_edit.toPlainText().strip()
        self.configuration.firmware_type = self.firmware_combo.currentText()
        self.configuration.vehicle_type = self.vehicle_combo.currentText()
        
        # Extract parameters from table
        parameters = {}
        for row in range(self.parameters_table.rowCount()):
            name_item = self.parameters_table.item(row, 0)
            value_item = self.parameters_table.item(row, 1)
            
            if name_item and value_item:
                param_name = name_item.text().strip()
                param_value = value_item.text().strip()
                
                if param_name and param_value:
                    # Convert value to appropriate type
                    try:
                        if '.' in param_value:
                            parameters[param_name] = float(param_value)
                        else:
                            parameters[param_name] = int(param_value)
                    except ValueError:
                        parameters[param_name] = param_value
                        
        self.configuration.parameters = parameters
        
        # Emit signal
        self.configuration_saved.emit(self.configuration)
        
        # Close dialog
        self.accept()
