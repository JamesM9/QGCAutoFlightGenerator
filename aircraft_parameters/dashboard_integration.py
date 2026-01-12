#!/usr/bin/env python3
"""
Dashboard Integration for Aircraft Parameters
Provides UI components for the main dashboard
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QComboBox, QPushButton, QFrame,
                              QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .configuration_manager import configuration_manager
from .configuration_editor import ConfigurationEditor


class ParameterManagementWidget(QWidget):
    """Widget for parameter management in the dashboard sidebar"""
    
    # Signals
    configuration_changed = pyqtSignal(str)  # config_id
    parameters_enabled_changed = pyqtSignal(bool)  # enabled
    global_parameter_state_changed = pyqtSignal()  # Notify all tools of state change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.load_configurations()
        
        # Connect to configuration manager signals
        configuration_manager.configuration_updated.connect(self.on_configuration_updated)
        configuration_manager.configuration_deleted.connect(self.on_configuration_deleted)
        configuration_manager.active_configuration_changed.connect(self.on_active_configuration_changed)
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create parameter management group
        self.param_group = QGroupBox("Aircraft Parameters")
        self.param_group.setFont(QFont("Arial", 12, QFont.Bold))
        self.param_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2d3748;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                padding-bottom: 15px;
                padding-left: 15px;
                padding-right: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00d4aa;
            }
        """)
        
        param_layout = QVBoxLayout(self.param_group)
        param_layout.setSpacing(8)
        
        # Global enable checkbox
        self.enable_checkbox = QCheckBox("Enable Aircraft Parameters")
        self.enable_checkbox.setFont(QFont("Arial", 11))
        self.enable_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 8px;
                font-size: 11px;
                padding: 5px 0px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4a5568;
                background-color: #1a2332;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #00d4aa;
                background-color: #00d4aa;
                border-radius: 3px;
            }
            QCheckBox::indicator:hover {
                border-color: #00d4aa;
            }
        """)
        param_layout.addWidget(self.enable_checkbox)
        
        # Configuration selector
        config_layout = QHBoxLayout()
        config_layout.setSpacing(5)
        
        config_label = QLabel("Configuration:")
        config_label.setFont(QFont("Arial", 10))
        config_label.setStyleSheet("color: #CCCCCC;")
        config_label.setMinimumWidth(80)
        config_layout.addWidget(config_label)
        
        self.config_combo = QComboBox()
        self.config_combo.setFont(QFont("Arial", 10))
        self.config_combo.setMinimumHeight(30)
        self.config_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QComboBox:focus {
                border-color: #00d4aa;
                background-color: #374151;
            }
            QComboBox:hover {
                border-color: #6b7280;
                background-color: #374151;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid white;
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                selection-background-color: #00d4aa;
            }
        """)
        config_layout.addWidget(self.config_combo)
        
        param_layout.addLayout(config_layout)
        
        # Configuration info label
        self.config_info_label = QLabel("No configuration selected")
        self.config_info_label.setFont(QFont("Arial", 9))
        self.config_info_label.setStyleSheet("color: #888888;")
        self.config_info_label.setWordWrap(True)
        param_layout.addWidget(self.config_info_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.manage_btn = QPushButton("Manage")
        self.manage_btn.setFont(QFont("Arial", 9))
        self.manage_btn.setMinimumHeight(28)
        self.manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        button_layout.addWidget(self.manage_btn)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setFont(QFont("Arial", 9))
        self.import_btn.setMinimumHeight(28)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        button_layout.addWidget(self.import_btn)
        
        param_layout.addLayout(button_layout)
        
        layout.addWidget(self.param_group)
        
        # Initially disable the group
        self.set_parameters_enabled(False)
    
    def connect_signals(self):
        """Connect UI signals"""
        self.enable_checkbox.toggled.connect(self.on_enable_toggled)
        self.config_combo.currentTextChanged.connect(self.on_configuration_changed)
        self.manage_btn.clicked.connect(self.open_configuration_manager)
        self.import_btn.clicked.connect(self.import_parameter_file)
    
    def load_configurations(self):
        """Load configurations into the combo box"""
        self.config_combo.clear()
        
        configurations = configuration_manager.get_configurations()
        for config in configurations:
            self.config_combo.addItem(config.name, config.id)
        
        # Set active configuration
        active_config = configuration_manager.get_active_configuration()
        if active_config:
            index = self.config_combo.findData(active_config.id)
            if index >= 0:
                self.config_combo.setCurrentIndex(index)
                self.update_configuration_info(active_config)
    
    def update_configuration_info(self, config):
        """Update the configuration info label"""
        if config:
            info_text = f"{config.firmware_type.upper()} - {config.vehicle_type.title()}"
            if config.description:
                info_text += f"\n{config.description}"
            self.config_info_label.setText(info_text)
        else:
            self.config_info_label.setText("No configuration selected")
    
    def set_parameters_enabled(self, enabled: bool):
        """Enable or disable the parameter system"""
        self.enable_checkbox.setChecked(enabled)
        self.config_combo.setEnabled(enabled)
        self.manage_btn.setEnabled(enabled)
        self.import_btn.setEnabled(enabled)
        
        if not enabled:
            self.config_info_label.setText("Parameters disabled")
    
    def on_enable_toggled(self, enabled: bool):
        """Handle enable checkbox toggle"""
        self.set_parameters_enabled(enabled)
        self.parameters_enabled_changed.emit(enabled)
        self.global_parameter_state_changed.emit()  # Notify all tools
        
        if enabled:
            self.load_configurations()
    
    def on_configuration_changed(self, config_name: str):
        """Handle configuration selection change"""
        if config_name:
            config_id = self.config_combo.currentData()
            if config_id:
                configuration_manager.set_active_configuration(config_id)
                config = configuration_manager.get_configuration(config_id)
                self.update_configuration_info(config)
                self.configuration_changed.emit(config_id)
    
    def on_configuration_updated(self, config_id: str):
        """Handle configuration update from manager"""
        self.load_configurations()
    
    def on_configuration_deleted(self, config_id: str):
        """Handle configuration deletion from manager"""
        self.load_configurations()
    
    def on_active_configuration_changed(self, config_id: str):
        """Handle active configuration change from manager"""
        if config_id:
            index = self.config_combo.findData(config_id)
            if index >= 0:
                self.config_combo.setCurrentIndex(index)
                config = configuration_manager.get_configuration(config_id)
                self.update_configuration_info(config)
    
    def open_configuration_manager(self):
        """Open the configuration manager dialog"""
        try:
            dialog = ConfigurationEditor(self)
            if dialog.exec_() == dialog.Accepted:
                self.load_configurations()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open configuration manager: {str(e)}")
    
    def import_parameter_file(self):
        """Import a new parameter file"""
        try:
            from .parameter_file_manager import parameter_file_manager
            
            result = parameter_file_manager.import_parameter_file(self)
            if result:
                filename, firmware_type, parameters = result
                
                # Create a new configuration from the imported file
                from .configuration_manager import AircraftConfiguration
                
                config = AircraftConfiguration()
                config.name = f"Imported {filename}"
                config.description = f"Configuration imported from {filename}"
                config.firmware_type = firmware_type
                config.parameter_file = filename
                config.parameters = parameters
                
                # Set vehicle type based on firmware
                if firmware_type == "arducopter":
                    config.vehicle_type = "multicopter"
                elif firmware_type == "arduplane":
                    config.vehicle_type = "fixedwing"
                elif firmware_type == "px4":
                    config.vehicle_type = "multicopter"  # Default for PX4
                
                # Extract flight characteristics
                from .parameter_file_manager import parameter_file_manager
                config.flight_characteristics = parameter_file_manager.extract_flight_characteristics(
                    parameters, firmware_type
                )
                
                # Add to configuration manager
                configuration_manager.add_configuration(config)
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Parameter file '{filename}' imported successfully!\n"
                    f"Created configuration: {config.name}"
                )
                
                self.load_configurations()
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import parameter file: {str(e)}")
    
    def get_active_configuration(self):
        """Get the currently active configuration"""
        if self.enable_checkbox.isChecked():
            return configuration_manager.get_active_configuration()
        return None
    
    def is_parameters_enabled(self) -> bool:
        """Check if parameters are enabled"""
        return self.enable_checkbox.isChecked()
