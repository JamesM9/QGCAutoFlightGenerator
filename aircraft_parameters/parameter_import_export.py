#!/usr/bin/env python3
"""
Parameter Import/Export System
Enhanced functionality for importing and exporting aircraft parameters
"""

import os
import json
import csv
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QPushButton, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QComboBox, QCheckBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QTabWidget, QFormLayout, QSpinBox, QDoubleSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime
import xml.etree.ElementTree as ET


class ParameterImportExportWidget(QWidget):
    """Widget for importing and exporting aircraft parameters"""
    
    parameters_imported = pyqtSignal(dict)  # Emitted when parameters are imported
    configuration_exported = pyqtSignal(str)  # Emitted when configuration is exported
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.imported_parameters = {}
        self.import_history = []
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Parameter Import/Export")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Import tab
        import_tab = self.create_import_tab()
        tab_widget.addTab(import_tab, "Import Parameters")
        
        # Export tab
        export_tab = self.create_export_tab()
        tab_widget.addTab(export_tab, "Export Configuration")
        
        # History tab
        history_tab = self.create_history_tab()
        tab_widget.addTab(history_tab, "Import History")
        
    def create_import_tab(self):
        """Create the import parameters tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Import options group
        options_group = QGroupBox("Import Options")
        options_layout = QFormLayout(options_group)
        
        # File format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "ArduPilot .param file",
            "PX4 .txt file", 
            "JSON configuration",
            "CSV parameters",
            "Auto-detect format"
        ])
        options_layout.addRow("File Format:", self.format_combo)
        
        # Import mode
        self.import_mode_combo = QComboBox()
        self.import_mode_combo.addItems([
            "Create new configuration",
            "Update existing configuration",
            "Merge with existing parameters"
        ])
        options_layout.addRow("Import Mode:", self.import_mode_combo)
        
        # Validation options
        self.validate_params_checkbox = QCheckBox("Validate parameters")
        self.validate_params_checkbox.setChecked(True)
        options_layout.addRow("", self.validate_params_checkbox)
        
        self.auto_create_config_checkbox = QCheckBox("Auto-create configuration")
        self.auto_create_config_checkbox.setChecked(True)
        options_layout.addRow("", self.auto_create_config_checkbox)
        
        layout.addWidget(options_group)
        
        # Import buttons
        button_layout = QHBoxLayout()
        
        self.import_file_btn = QPushButton("Import from File")
        self.import_file_btn.clicked.connect(self.import_from_file)
        button_layout.addWidget(self.import_file_btn)
        
        self.import_clipboard_btn = QPushButton("Import from Clipboard")
        self.import_clipboard_btn.clicked.connect(self.import_from_clipboard)
        button_layout.addWidget(self.import_clipboard_btn)
        
        self.clear_import_btn = QPushButton("Clear Import")
        self.clear_import_btn.clicked.connect(self.clear_import)
        button_layout.addWidget(self.clear_import_btn)
        
        layout.addLayout(button_layout)
        
        # Import progress
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        layout.addWidget(self.import_progress)
        
        # Import results
        results_group = QGroupBox("Import Results")
        results_layout = QVBoxLayout(results_group)
        
        self.import_results = QTextEdit()
        self.import_results.setMaximumHeight(200)
        self.import_results.setReadOnly(True)
        results_layout.addWidget(self.import_results)
        
        layout.addWidget(results_group)
        
        return widget
        
    def create_export_tab(self):
        """Create the export configuration tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export options group
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout(options_group)
        
        # Export format
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems([
            "ArduPilot .param file",
            "PX4 .txt file",
            "JSON configuration",
            "CSV parameters",
            "QGroundControl .plan file"
        ])
        options_layout.addRow("Export Format:", self.export_format_combo)
        
        # Include options
        self.include_metadata_checkbox = QCheckBox("Include metadata")
        self.include_metadata_checkbox.setChecked(True)
        options_layout.addRow("", self.include_metadata_checkbox)
        
        self.include_validation_checkbox = QCheckBox("Include validation info")
        self.include_validation_checkbox.setChecked(True)
        options_layout.addRow("", self.include_validation_checkbox)
        
        self.include_comments_checkbox = QCheckBox("Include parameter comments")
        self.include_comments_checkbox.setChecked(True)
        options_layout.addRow("", self.include_comments_checkbox)
        
        layout.addWidget(options_group)
        
        # Export buttons
        button_layout = QHBoxLayout()
        
        self.export_file_btn = QPushButton("Export to File")
        self.export_file_btn.clicked.connect(self.export_to_file)
        button_layout.addWidget(self.export_file_btn)
        
        self.export_clipboard_btn = QPushButton("Copy to Clipboard")
        self.export_clipboard_btn.clicked.connect(self.export_to_clipboard)
        button_layout.addWidget(self.export_clipboard_btn)
        
        self.preview_export_btn = QPushButton("Preview Export")
        self.preview_export_btn.clicked.connect(self.preview_export)
        button_layout.addWidget(self.preview_export_btn)
        
        layout.addLayout(button_layout)
        
        # Export preview
        preview_group = QGroupBox("Export Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.export_preview = QTextEdit()
        self.export_preview.setMaximumHeight(300)
        self.export_preview.setReadOnly(True)
        preview_layout.addWidget(self.export_preview)
        
        layout.addWidget(preview_group)
        
        return widget
        
    def create_history_tab(self):
        """Create the import history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # History list
        history_group = QGroupBox("Import History")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.load_from_history)
        history_layout.addWidget(self.history_list)
        
        # History actions
        history_actions = QHBoxLayout()
        
        self.clear_history_btn = QPushButton("Clear History")
        self.clear_history_btn.clicked.connect(self.clear_history)
        history_actions.addWidget(self.clear_history_btn)
        
        self.export_history_btn = QPushButton("Export History")
        self.export_history_btn.clicked.connect(self.export_history)
        history_actions.addWidget(self.export_history_btn)
        
        history_layout.addLayout(history_actions)
        
        layout.addWidget(history_group)
        
        # History details
        details_group = QGroupBox("History Details")
        details_layout = QVBoxLayout(details_group)
        
        self.history_details = QTextEdit()
        self.history_details.setMaximumHeight(200)
        self.history_details.setReadOnly(True)
        details_layout.addWidget(self.history_details)
        
        layout.addWidget(details_group)
        
        return widget
        
    def import_from_file(self):
        """Import parameters from a file"""
        file_format = self.format_combo.currentText()
        
        # Set file filter based on format
        if "ArduPilot" in file_format:
            file_filter = "ArduPilot Parameter Files (*.param *.params);;All Files (*)"
        elif "PX4" in file_format:
            file_filter = "PX4 Parameter Files (*.txt);;All Files (*)"
        elif "JSON" in file_format:
            file_filter = "JSON Files (*.json);;All Files (*)"
        elif "CSV" in file_format:
            file_filter = "CSV Files (*.csv);;All Files (*)"
        else:
            file_filter = "All Files (*)"
            
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Parameters", "", file_filter
        )
        
        if filename:
            self.import_parameters_from_file(filename)
            
    def import_parameters_from_file(self, filename: str):
        """Import parameters from a specific file"""
        try:
            self.import_progress.setVisible(True)
            self.import_progress.setValue(0)
            
            # Detect file format if auto-detect is selected
            if "Auto-detect" in self.format_combo.currentText():
                file_format = self.detect_file_format(filename)
            else:
                file_format = self.format_combo.currentText()
                
            # Import based on format
            if "ArduPilot" in file_format:
                parameters = self.import_ardupilot_file(filename)
            elif "PX4" in file_format:
                parameters = self.import_px4_file(filename)
            elif "JSON" in file_format:
                parameters = self.import_json_file(filename)
            elif "CSV" in file_format:
                parameters = self.import_csv_file(filename)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
            # Validate parameters if requested
            if self.validate_params_checkbox.isChecked():
                validation_results = self.validate_parameters(parameters)
                if not validation_results["valid"]:
                    self.show_validation_warnings(validation_results)
                    
            # Store in history
            self.add_to_history(filename, parameters, file_format)
            
            # Emit signal
            self.parameters_imported.emit(parameters)
            
            # Update results
            self.import_results.setText(f"Successfully imported {len(parameters)} parameters from {filename}")
            
            self.import_progress.setValue(100)
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import parameters: {str(e)}")
            self.import_results.setText(f"Import failed: {str(e)}")
        finally:
            self.import_progress.setVisible(False)
            
    def detect_file_format(self, filename: str) -> str:
        """Detect the file format based on extension and content"""
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in [".param", ".params"]:
            return "ArduPilot .param file"
        elif ext == ".txt":
            # Check if it's a PX4 file by reading first few lines
            try:
                with open(filename, 'r') as f:
                    first_line = f.readline().strip()
                    if "PARAM" in first_line or "PARAM_" in first_line:
                        return "PX4 .txt file"
            except:
                pass
        elif ext == ".json":
            return "JSON configuration"
        elif ext == ".csv":
            return "CSV parameters"
            
        return "Unknown format"
        
    def import_ardupilot_file(self, filename: str) -> Dict[str, Any]:
        """Import ArduPilot .param file"""
        parameters = {}
        
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    # Parse ArduPilot parameter format: PARAM_NAME,VALUE
                    if ',' in line:
                        param_name, param_value = line.split(',', 1)
                        param_name = param_name.strip()
                        param_value = param_value.strip()
                        
                        # Convert value to appropriate type
                        if param_value.lower() in ['true', 'false']:
                            parameters[param_name] = param_value.lower() == 'true'
                        elif '.' in param_value:
                            parameters[param_name] = float(param_value)
                        else:
                            parameters[param_name] = int(param_value)
                            
                except Exception as e:
                    print(f"Warning: Failed to parse line {line_num}: {line}")
                    
        return parameters
        
    def import_px4_file(self, filename: str) -> Dict[str, Any]:
        """Import PX4 .txt file"""
        parameters = {}
        
        with open(filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                try:
                    # Parse PX4 parameter format: PARAM_NAME VALUE
                    parts = line.split()
                    if len(parts) >= 2:
                        param_name = parts[0]
                        param_value = parts[1]
                        
                        # Convert value to appropriate type
                        if param_value.lower() in ['true', 'false']:
                            parameters[param_name] = param_value.lower() == 'true'
                        elif '.' in param_value:
                            parameters[param_name] = float(param_value)
                        else:
                            parameters[param_name] = int(param_value)
                            
                except Exception as e:
                    print(f"Warning: Failed to parse line {line_num}: {line}")
                    
        return parameters
        
    def import_json_file(self, filename: str) -> Dict[str, Any]:
        """Import JSON configuration file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            
        # Extract parameters from JSON structure
        if isinstance(data, dict):
            if "parameters" in data:
                return data["parameters"]
            elif "aircraft_parameters" in data:
                return data["aircraft_parameters"]
            else:
                return data
        else:
            raise ValueError("Invalid JSON structure")
            
    def import_csv_file(self, filename: str) -> Dict[str, Any]:
        """Import CSV parameters file"""
        parameters = {}
        
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "parameter" in row and "value" in row:
                    param_name = row["parameter"]
                    param_value = row["value"]
                    
                    # Convert value to appropriate type
                    if param_value.lower() in ['true', 'false']:
                        parameters[param_name] = param_value.lower() == 'true'
                    elif '.' in param_value:
                        parameters[param_name] = float(param_value)
                    else:
                        parameters[param_name] = int(param_value)
                        
        return parameters
        
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate imported parameters"""
        # This would integrate with the parameter validator
        # For now, return a basic validation result
        return {
            "valid": True,
            "warnings": [],
            "errors": [],
            "validated_count": len(parameters)
        }
        
    def show_validation_warnings(self, validation_results: Dict[str, Any]):
        """Show validation warnings to the user"""
        if validation_results["warnings"]:
            warning_text = "Validation Warnings:\n" + "\n".join(validation_results["warnings"])
            QMessageBox.warning(self, "Validation Warnings", warning_text)
            
    def add_to_history(self, filename: str, parameters: Dict[str, Any], format: str):
        """Add import to history"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "format": format,
            "parameter_count": len(parameters),
            "parameters": parameters
        }
        
        self.import_history.append(history_entry)
        self.update_history_display()
        
    def update_history_display(self):
        """Update the history list display"""
        self.history_list.clear()
        
        for i, entry in enumerate(self.import_history):
            item_text = f"{entry['timestamp'][:19]} - {entry['filename']} ({entry['parameter_count']} params)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, i)
            self.history_list.addItem(item)
            
    def load_from_history(self, item: QListWidgetItem):
        """Load parameters from history entry"""
        index = item.data(Qt.UserRole)
        if index < len(self.import_history):
            entry = self.import_history[index]
            self.parameters_imported.emit(entry["parameters"])
            
            # Update details
            details = f"File: {entry['filename']}\n"
            details += f"Format: {entry['format']}\n"
            details += f"Parameters: {entry['parameter_count']}\n"
            details += f"Timestamp: {entry['timestamp']}\n"
            self.history_details.setText(details)
            
    def clear_history(self):
        """Clear import history"""
        self.import_history.clear()
        self.update_history_display()
        self.history_details.clear()
        
    def export_history(self):
        """Export import history to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export History", "", "JSON Files (*.json)"
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(self.import_history, f, indent=2)
            QMessageBox.information(self, "Export Complete", f"History exported to {filename}")
            
    def import_from_clipboard(self):
        """Import parameters from clipboard"""
        # This would implement clipboard import functionality
        QMessageBox.information(self, "Clipboard Import", "Clipboard import not yet implemented")
        
    def clear_import(self):
        """Clear current import"""
        self.imported_parameters.clear()
        self.import_results.clear()
        
    def export_to_file(self):
        """Export configuration to file"""
        # This would implement file export functionality
        QMessageBox.information(self, "Export", "Export functionality not yet implemented")
        
    def export_to_clipboard(self):
        """Export configuration to clipboard"""
        # This would implement clipboard export functionality
        QMessageBox.information(self, "Clipboard Export", "Clipboard export not yet implemented")
        
    def preview_export(self):
        """Preview export content"""
        # This would implement export preview functionality
        self.export_preview.setText("Export preview not yet implemented")
