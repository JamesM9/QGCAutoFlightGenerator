#!/usr/bin/env python3
"""
Settings Integration for Aircraft Parameters
Provides settings tab for aircraft parameter management
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QComboBox, QPushButton, QGroupBox,
                              QFormLayout, QListWidget, QListWidgetItem,
                              QMessageBox, QFileDialog, QLineEdit, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .configuration_manager import configuration_manager
from .parameter_file_manager import parameter_file_manager
from .configuration_editor import ConfigurationEditor


class AircraftParametersTab(QWidget):
    """Settings tab for aircraft parameter management"""
    
    # Signals
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title_label = QLabel("Aircraft Parameters")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Global settings group
        global_group = QGroupBox("Global Settings")
        global_group.setFont(QFont("Arial", 12, QFont.Bold))
        global_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
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
        
        global_layout = QFormLayout(global_group)
        global_layout.setSpacing(15)
        
        # Enable aircraft parameters
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
        global_layout.addRow("", self.enable_checkbox)
        
        # Default configuration
        self.default_config_combo = QComboBox()
        self.default_config_combo.setFont(QFont("Arial", 11))
        self.default_config_combo.setMinimumHeight(35)
        self.default_config_combo.setStyleSheet("""
            QComboBox {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QComboBox:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 8px;
            }
        """)
        global_layout.addRow("Default Configuration:", self.default_config_combo)
        
        layout.addWidget(global_group)
        
        # Configuration management group
        config_group = QGroupBox("Configuration Management")
        config_group.setFont(QFont("Arial", 12, QFont.Bold))
        config_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
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
        
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)
        
        # Configuration list
        self.config_list = QListWidget()
        self.config_list.setFont(QFont("Arial", 10))
        self.config_list.setMaximumHeight(150)
        self.config_list.setStyleSheet("""
            QListWidget {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a5568;
            }
            QListWidget::item:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QListWidget::item:hover {
                background-color: #374151;
            }
        """)
        config_layout.addWidget(self.config_list)
        
        # Configuration actions
        config_actions_layout = QHBoxLayout()
        
        self.manage_configs_btn = QPushButton("Manage Configurations")
        self.manage_configs_btn.setFont(QFont("Arial", 10))
        self.manage_configs_btn.setMinimumHeight(35)
        self.manage_configs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        config_actions_layout.addWidget(self.manage_configs_btn)
        
        self.refresh_configs_btn = QPushButton("Refresh")
        self.refresh_configs_btn.setFont(QFont("Arial", 10))
        self.refresh_configs_btn.setMinimumHeight(35)
        self.refresh_configs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        config_actions_layout.addWidget(self.refresh_configs_btn)
        
        config_layout.addLayout(config_actions_layout)
        layout.addWidget(config_group)
        
        # Parameter files group
        files_group = QGroupBox("Parameter Files")
        files_group.setFont(QFont("Arial", 12, QFont.Bold))
        files_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
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
        
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(10)
        
        # Parameter files list
        self.files_list = QListWidget()
        self.files_list.setFont(QFont("Arial", 10))
        self.files_list.setMaximumHeight(120)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a5568;
            }
            QListWidget::item:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QListWidget::item:hover {
                background-color: #374151;
            }
        """)
        files_layout.addWidget(self.files_list)
        
        # File actions
        file_actions_layout = QHBoxLayout()
        
        self.import_file_btn = QPushButton("Import File")
        self.import_file_btn.setFont(QFont("Arial", 10))
        self.import_file_btn.setMinimumHeight(35)
        self.import_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        file_actions_layout.addWidget(self.import_file_btn)
        
        self.delete_file_btn = QPushButton("Delete File")
        self.delete_file_btn.setFont(QFont("Arial", 10))
        self.delete_file_btn.setMinimumHeight(35)
        self.delete_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #f44336;
                color: white;
            }
        """)
        file_actions_layout.addWidget(self.delete_file_btn)
        
        self.refresh_files_btn = QPushButton("Refresh")
        self.refresh_files_btn.setFont(QFont("Arial", 10))
        self.refresh_files_btn.setMinimumHeight(35)
        self.refresh_files_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        file_actions_layout.addWidget(self.refresh_files_btn)
        
        files_layout.addLayout(file_actions_layout)
        layout.addWidget(files_group)
        
        # Data directory group
        data_group = QGroupBox("Data Management")
        data_group.setFont(QFont("Arial", 12, QFont.Bold))
        data_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
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
        
        data_layout = QVBoxLayout(data_group)
        data_layout.setSpacing(10)
        
        # Data directory info
        data_info_layout = QHBoxLayout()
        
        data_label = QLabel("Data Directory:")
        data_label.setFont(QFont("Arial", 10))
        data_label.setStyleSheet("color: #CCCCCC;")
        data_info_layout.addWidget(data_label)
        
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setFont(QFont("Arial", 10))
        self.data_dir_edit.setMinimumHeight(30)
        self.data_dir_edit.setReadOnly(True)
        self.data_dir_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 10px;
            }
        """)
        data_info_layout.addWidget(self.data_dir_edit)
        
        self.browse_data_btn = QPushButton("Browse")
        self.browse_data_btn.setFont(QFont("Arial", 10))
        self.browse_data_btn.setMinimumHeight(30)
        self.browse_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 6px 12px;
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
        data_info_layout.addWidget(self.browse_data_btn)
        
        data_layout.addLayout(data_info_layout)
        
        # Data actions
        data_actions_layout = QHBoxLayout()
        
        self.export_data_btn = QPushButton("Export All Data")
        self.export_data_btn.setFont(QFont("Arial", 10))
        self.export_data_btn.setMinimumHeight(35)
        self.export_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        data_actions_layout.addWidget(self.export_data_btn)
        
        self.import_data_btn = QPushButton("Import Data")
        self.import_data_btn.setFont(QFont("Arial", 10))
        self.import_data_btn.setMinimumHeight(35)
        self.import_data_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
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
        data_actions_layout.addWidget(self.import_data_btn)
        
        data_layout.addLayout(data_actions_layout)
        layout.addWidget(data_group)
        
        layout.addStretch()
    
    def connect_signals(self):
        """Connect UI signals"""
        self.enable_checkbox.toggled.connect(self.on_settings_changed)
        self.default_config_combo.currentTextChanged.connect(self.on_settings_changed)
        self.manage_configs_btn.clicked.connect(self.open_configuration_manager)
        self.refresh_configs_btn.clicked.connect(self.refresh_configurations)
        self.import_file_btn.clicked.connect(self.import_parameter_file)
        self.delete_file_btn.clicked.connect(self.delete_parameter_file)
        self.refresh_files_btn.clicked.connect(self.refresh_parameter_files)
        self.browse_data_btn.clicked.connect(self.browse_data_directory)
        self.export_data_btn.clicked.connect(self.export_all_data)
        self.import_data_btn.clicked.connect(self.import_data)
    
    def load_settings(self):
        """Load current settings"""
        # Load configurations
        self.refresh_configurations()
        
        # Load parameter files
        self.refresh_parameter_files()
        
        # Set data directory
        self.data_dir_edit.setText(configuration_manager.data_dir)
        
        # Load global settings (these would come from a settings manager)
        # For now, we'll use defaults
        self.enable_checkbox.setChecked(True)
    
    def refresh_configurations(self):
        """Refresh the configurations list"""
        self.config_list.clear()
        self.default_config_combo.clear()
        
        configurations = configuration_manager.get_configurations()
        for config in configurations:
            # Add to list
            item = QListWidgetItem(f"{config.name} ({config.firmware_type})")
            item.setData(Qt.UserRole, config.id)
            self.config_list.addItem(item)
            
            # Add to combo
            self.default_config_combo.addItem(config.name, config.id)
        
        # Set active configuration
        active_config = configuration_manager.get_active_configuration()
        if active_config:
            index = self.default_config_combo.findData(active_config.id)
            if index >= 0:
                self.default_config_combo.setCurrentIndex(index)
    
    def refresh_parameter_files(self):
        """Refresh the parameter files list"""
        self.files_list.clear()
        
        parameter_files = configuration_manager.get_parameter_files()
        for param_file in parameter_files:
            item = QListWidgetItem(f"{param_file.filename} ({param_file.firmware_type})")
            item.setData(Qt.UserRole, param_file.filename)
            self.files_list.addItem(item)
    
    def on_settings_changed(self):
        """Handle settings changes"""
        self.settings_changed.emit()
    
    def open_configuration_manager(self):
        """Open the configuration manager dialog"""
        try:
            dialog = ConfigurationEditor(self)
            if dialog.exec_() == dialog.Accepted:
                self.refresh_configurations()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open configuration manager: {str(e)}")
    
    def import_parameter_file(self):
        """Import a new parameter file"""
        try:
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
                
                self.refresh_configurations()
                self.refresh_parameter_files()
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import parameter file: {str(e)}")
    
    def delete_parameter_file(self):
        """Delete selected parameter file"""
        current_item = self.files_list.currentItem()
        if not current_item:
            return
        
        filename = current_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Delete Parameter File",
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if configuration_manager.delete_parameter_file(filename):
                self.refresh_parameter_files()
                QMessageBox.information(self, "Success", "Parameter file deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Cannot delete parameter file - it may be in use by a configuration")
    
    def browse_data_directory(self):
        """Browse for data directory"""
        current_dir = self.data_dir_edit.text()
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Data Directory",
            current_dir
        )
        
        if new_dir:
            self.data_dir_edit.setText(new_dir)
            # Note: In a real implementation, this would update the configuration manager's data directory
    
    def export_all_data(self):
        """Export all configuration data"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Configuration Data",
                "aircraft_configurations_backup.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                import json
                import shutil
                
                # Copy the configuration file
                shutil.copy2(configuration_manager.config_file, file_path)
                
                QMessageBox.information(self, "Success", "Configuration data exported successfully")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def import_data(self):
        """Import configuration data"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Import Configuration Data",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                reply = QMessageBox.question(
                    self,
                    "Import Data",
                    "This will replace all current configuration data. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    import shutil
                    
                    # Backup current data
                    backup_path = configuration_manager.config_file + ".backup"
                    shutil.copy2(configuration_manager.config_file, backup_path)
                    
                    try:
                        # Copy new data
                        shutil.copy2(file_path, configuration_manager.config_file)
                        
                        # Reload data
                        configuration_manager.load_data()
                        
                        # Refresh UI
                        self.refresh_configurations()
                        self.refresh_parameter_files()
                        
                        QMessageBox.information(self, "Success", "Configuration data imported successfully")
                        
                    except Exception as e:
                        # Restore backup
                        shutil.copy2(backup_path, configuration_manager.config_file)
                        configuration_manager.load_data()
                        raise e
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import data: {str(e)}")
    
    def get_settings(self):
        """Get current settings"""
        return {
            "enable_aircraft_parameters": self.enable_checkbox.isChecked(),
            "default_configuration": self.default_config_combo.currentData(),
            "data_directory": self.data_dir_edit.text()
        }
    
    def set_settings(self, settings):
        """Set settings"""
        self.enable_checkbox.setChecked(settings.get("enable_aircraft_parameters", True))
        
        default_config_id = settings.get("default_configuration")
        if default_config_id:
            index = self.default_config_combo.findData(default_config_id)
            if index >= 0:
                self.default_config_combo.setCurrentIndex(index)
        
        data_dir = settings.get("data_directory")
        if data_dir:
            self.data_dir_edit.setText(data_dir)
