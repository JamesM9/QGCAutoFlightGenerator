#!/usr/bin/env python3
"""
Configuration Editor Dialog
Provides UI for creating, editing, and managing aircraft configurations
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QTextEdit, QComboBox, QPushButton, 
                              QTableWidget, QTableWidgetItem, QTabWidget,
                              QGroupBox, QFormLayout, QMessageBox, QHeaderView,
                              QDialogButtonBox, QSplitter, QListWidget, QListWidgetItem,
                              QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .configuration_manager import configuration_manager, AircraftConfiguration
from .parameter_file_manager import parameter_file_manager
from .parameter_validator import parameter_validator


class ConfigurationEditor(QDialog):
    """Dialog for editing aircraft configurations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aircraft Configuration Manager")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.current_config = None
        self.setup_ui()
        self.load_configurations()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Aircraft Configuration Manager")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Main content area
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Configuration list
        left_panel = self.create_configuration_list_panel()
        main_splitter.addWidget(left_panel)
        
        # Right panel - Configuration editor
        right_panel = self.create_configuration_editor_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 700])
        layout.addWidget(main_splitter)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_configuration_list_panel(self):
        """Create the configuration list panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 10, 0)
        
        # Panel title
        title_label = QLabel("Configurations")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Configuration list
        self.config_list = QListWidget()
        self.config_list.setFont(QFont("Arial", 10))
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
        self.config_list.itemClicked.connect(self.on_configuration_selected)
        layout.addWidget(self.config_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New")
        self.new_btn.setFont(QFont("Arial", 10))
        self.new_btn.setMinimumHeight(35)
        self.new_btn.setStyleSheet("""
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
        self.new_btn.clicked.connect(self.create_new_configuration)
        button_layout.addWidget(self.new_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFont(QFont("Arial", 10))
        self.delete_btn.setMinimumHeight(35)
        self.delete_btn.setStyleSheet("""
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
        self.delete_btn.clicked.connect(self.delete_configuration)
        button_layout.addWidget(self.delete_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_configuration_editor_panel(self):
        """Create the configuration editor panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Panel title
        self.editor_title_label = QLabel("Select a configuration to edit")
        self.editor_title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.editor_title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(self.editor_title_label)
        
        # Editor tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #4a5568;
                border-radius: 5px;
                background-color: #2d3748;
            }
            QTabBar::tab {
                background-color: #374151;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #2d3748;
                border-bottom: 2px solid #00d4aa;
            }
            QTabBar::tab:hover {
                background-color: #4a5568;
            }
        """)
        
        # Basic info tab
        self.basic_info_tab = self.create_basic_info_tab()
        self.editor_tabs.addTab(self.basic_info_tab, "Basic Info")
        
        # Parameters tab
        self.parameters_tab = self.create_parameters_tab()
        self.editor_tabs.addTab(self.parameters_tab, "Parameters")
        
        # Flight characteristics tab
        self.characteristics_tab = self.create_characteristics_tab()
        self.editor_tabs.addTab(self.characteristics_tab, "Flight Characteristics")
        
        layout.addWidget(self.editor_tabs)
        
        # Save button
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4aa;
                color: #1a2332;
                border: 2px solid #00d4aa;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00b894;
                border-color: #00b894;
            }
            QPushButton:pressed {
                background-color: #00a085;
            }
            QPushButton:disabled {
                background-color: #4a5568;
                color: #9ca3af;
                border-color: #4a5568;
            }
        """)
        self.save_btn.clicked.connect(self.save_configuration)
        self.save_btn.setEnabled(False)
        layout.addWidget(self.save_btn)
        
        return panel
    
    def create_basic_info_tab(self):
        """Create the basic info tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Basic info group
        info_group = QGroupBox("Configuration Information")
        info_group.setFont(QFont("Arial", 12, QFont.Bold))
        info_group.setStyleSheet("""
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
        
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(15)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setFont(QFont("Arial", 11))
        self.name_edit.setMinimumHeight(35)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        info_layout.addRow("Name:", self.name_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setFont(QFont("Arial", 11))
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setStyleSheet("""
            QTextEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QTextEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        info_layout.addRow("Description:", self.description_edit)
        
        # Firmware type
        self.firmware_combo = QComboBox()
        self.firmware_combo.setFont(QFont("Arial", 11))
        self.firmware_combo.setMinimumHeight(35)
        self.firmware_combo.addItems(["arducopter", "arduplane", "px4"])
        self.firmware_combo.setStyleSheet("""
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
        info_layout.addRow("Firmware Type:", self.firmware_combo)
        
        # Vehicle type
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setFont(QFont("Arial", 11))
        self.vehicle_combo.setMinimumHeight(35)
        self.vehicle_combo.addItems(["multicopter", "fixedwing", "vtol"])
        self.vehicle_combo.setStyleSheet("""
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
        info_layout.addRow("Vehicle Type:", self.vehicle_combo)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return tab
    
    def create_parameters_tab(self):
        """Create the parameters tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Parameters table
        self.parameters_table = QTableWidget()
        self.parameters_table.setFont(QFont("Arial", 10))
        self.parameters_table.setColumnCount(2)
        self.parameters_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.parameters_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parameters_table.setStyleSheet("""
            QTableWidget {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                gridline-color: #4a5568;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a5568;
            }
            QTableWidget::item:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QHeaderView::section {
                background-color: #374151;
                color: white;
                padding: 8px;
                border: 1px solid #4a5568;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.parameters_table)
        
        # Parameter actions
        param_actions_layout = QHBoxLayout()
        
        self.add_param_btn = QPushButton("Add Parameter")
        self.add_param_btn.setFont(QFont("Arial", 10))
        self.add_param_btn.setMinimumHeight(35)
        self.add_param_btn.setStyleSheet("""
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
        self.add_param_btn.clicked.connect(self.add_parameter)
        param_actions_layout.addWidget(self.add_param_btn)
        
        self.remove_param_btn = QPushButton("Remove Parameter")
        self.remove_param_btn.setFont(QFont("Arial", 10))
        self.remove_param_btn.setMinimumHeight(35)
        self.remove_param_btn.setStyleSheet("""
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
        self.remove_param_btn.clicked.connect(self.remove_parameter)
        param_actions_layout.addWidget(self.remove_param_btn)
        
        self.suggest_params_btn = QPushButton("Suggest Defaults")
        self.suggest_params_btn.setFont(QFont("Arial", 10))
        self.suggest_params_btn.setMinimumHeight(35)
        self.suggest_params_btn.setStyleSheet("""
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
        self.suggest_params_btn.clicked.connect(self.suggest_default_parameters)
        param_actions_layout.addWidget(self.suggest_params_btn)
        
        layout.addLayout(param_actions_layout)
        
        return tab
    
    def create_characteristics_tab(self):
        """Create the flight characteristics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Flight characteristics group
        char_group = QGroupBox("Flight Characteristics")
        char_group.setFont(QFont("Arial", 12, QFont.Bold))
        char_group.setStyleSheet("""
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
        
        char_layout = QFormLayout(char_group)
        char_layout.setSpacing(15)
        
        # Max speed
        self.max_speed_edit = QLineEdit()
        self.max_speed_edit.setFont(QFont("Arial", 11))
        self.max_speed_edit.setMinimumHeight(35)
        self.max_speed_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        char_layout.addRow("Max Speed (m/s):", self.max_speed_edit)
        
        # Max climb rate
        self.max_climb_edit = QLineEdit()
        self.max_climb_edit.setFont(QFont("Arial", 11))
        self.max_climb_edit.setMinimumHeight(35)
        self.max_climb_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        char_layout.addRow("Max Climb Rate (m/s):", self.max_climb_edit)
        
        # Max descent rate
        self.max_descent_edit = QLineEdit()
        self.max_descent_edit.setFont(QFont("Arial", 11))
        self.max_descent_edit.setMinimumHeight(35)
        self.max_descent_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        char_layout.addRow("Max Descent Rate (m/s):", self.max_descent_edit)
        
        # Waypoint radius
        self.waypoint_radius_edit = QLineEdit()
        self.waypoint_radius_edit.setFont(QFont("Arial", 11))
        self.waypoint_radius_edit.setMinimumHeight(35)
        self.waypoint_radius_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        char_layout.addRow("Waypoint Radius (m):", self.waypoint_radius_edit)
        
        # Turn radius
        self.turn_radius_edit = QLineEdit()
        self.turn_radius_edit.setFont(QFont("Arial", 11))
        self.turn_radius_edit.setMinimumHeight(35)
        self.turn_radius_edit.setStyleSheet("""
            QLineEdit {
                background-color: #374151;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
            }
        """)
        char_layout.addRow("Turn Radius (m):", self.turn_radius_edit)
        
        layout.addWidget(char_group)
        layout.addStretch()
        
        return tab
    
    def load_configurations(self):
        """Load configurations into the list"""
        self.config_list.clear()
        
        configurations = configuration_manager.get_configurations()
        for config in configurations:
            item = QListWidgetItem(config.name)
            item.setData(Qt.UserRole, config.id)
            self.config_list.addItem(item)
    
    def on_configuration_selected(self, item):
        """Handle configuration selection"""
        config_id = item.data(Qt.UserRole)
        config = configuration_manager.get_configuration(config_id)
        
        if config:
            self.current_config = config
            self.load_configuration_data(config)
            self.editor_title_label.setText(f"Editing: {config.name}")
            self.save_btn.setEnabled(True)
    
    def load_configuration_data(self, config: AircraftConfiguration):
        """Load configuration data into the editor"""
        # Basic info
        self.name_edit.setText(config.name)
        self.description_edit.setPlainText(config.description)
        
        firmware_index = self.firmware_combo.findText(config.firmware_type)
        if firmware_index >= 0:
            self.firmware_combo.setCurrentIndex(firmware_index)
        
        vehicle_index = self.vehicle_combo.findText(config.vehicle_type)
        if vehicle_index >= 0:
            self.vehicle_combo.setCurrentIndex(vehicle_index)
        
        # Parameters
        self.load_parameters_table(config.parameters)
        
        # Flight characteristics
        self.max_speed_edit.setText(str(config.flight_characteristics.get("max_speed", "")))
        self.max_climb_edit.setText(str(config.flight_characteristics.get("max_climb_rate", "")))
        self.max_descent_edit.setText(str(config.flight_characteristics.get("max_descent_rate", "")))
        self.waypoint_radius_edit.setText(str(config.flight_characteristics.get("waypoint_radius", "")))
        self.turn_radius_edit.setText(str(config.flight_characteristics.get("turn_radius", "")))
    
    def load_parameters_table(self, parameters: dict):
        """Load parameters into the table"""
        self.parameters_table.setRowCount(len(parameters))
        
        for row, (param_name, param_value) in enumerate(parameters.items()):
            name_item = QTableWidgetItem(param_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.parameters_table.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(param_value))
            self.parameters_table.setItem(row, 1, value_item)
    
    def create_new_configuration(self):
        """Create a new configuration"""
        self.current_config = AircraftConfiguration()
        self.current_config.name = "New Configuration"
        self.current_config.firmware_type = "arducopter"
        self.current_config.vehicle_type = "multicopter"
        
        self.load_configuration_data(self.current_config)
        self.editor_title_label.setText("Creating: New Configuration")
        self.save_btn.setEnabled(True)
    
    def delete_configuration(self):
        """Delete the selected configuration"""
        current_item = self.config_list.currentItem()
        if not current_item:
            return
        
        config_id = current_item.data(Qt.UserRole)
        config = configuration_manager.get_configuration(config_id)
        
        if config:
            reply = QMessageBox.question(
                self,
                "Delete Configuration",
                f"Are you sure you want to delete '{config.name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                configuration_manager.delete_configuration(config_id)
                self.load_configurations()
                self.current_config = None
                self.editor_title_label.setText("Select a configuration to edit")
                self.save_btn.setEnabled(False)
    
    def add_parameter(self):
        """Add a new parameter to the table"""
        row_count = self.parameters_table.rowCount()
        self.parameters_table.insertRow(row_count)
        
        name_item = QTableWidgetItem("NEW_PARAM")
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.parameters_table.setItem(row_count, 0, name_item)
        
        value_item = QTableWidgetItem("0")
        self.parameters_table.setItem(row_count, 1, value_item)
    
    def remove_parameter(self):
        """Remove selected parameter from the table"""
        current_row = self.parameters_table.currentRow()
        if current_row >= 0:
            self.parameters_table.removeRow(current_row)
    
    def suggest_default_parameters(self):
        """Suggest default parameters for the current firmware type"""
        firmware_type = self.firmware_combo.currentText()
        vehicle_type = self.vehicle_combo.currentText()
        
        suggestions = parameter_validator.suggest_parameter_values(firmware_type, vehicle_type)
        
        self.parameters_table.setRowCount(len(suggestions))
        for row, (param_name, param_value) in enumerate(suggestions.items()):
            name_item = QTableWidgetItem(param_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.parameters_table.setItem(row, 0, name_item)
            
            value_item = QTableWidgetItem(str(param_value))
            self.parameters_table.setItem(row, 1, value_item)
    
    def save_configuration(self):
        """Save the current configuration"""
        if not self.current_config:
            return
        
        # Validate configuration
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Configuration name cannot be empty")
            return
        
        # Collect parameters from table
        parameters = {}
        for row in range(self.parameters_table.rowCount()):
            name_item = self.parameters_table.item(row, 0)
            value_item = self.parameters_table.item(row, 1)
            
            if name_item and value_item:
                param_name = name_item.text().strip()
                param_value = value_item.text().strip()
                
                if param_name and param_value:
                    # Try to convert to appropriate type
                    try:
                        if '.' not in param_value:
                            parameters[param_name] = int(param_value)
                        else:
                            parameters[param_name] = float(param_value)
                    except ValueError:
                        parameters[param_name] = param_value
        
        # Collect flight characteristics
        flight_characteristics = {}
        try:
            if self.max_speed_edit.text():
                flight_characteristics["max_speed"] = float(self.max_speed_edit.text())
            if self.max_climb_edit.text():
                flight_characteristics["max_climb_rate"] = float(self.max_climb_edit.text())
            if self.max_descent_edit.text():
                flight_characteristics["max_descent_rate"] = float(self.max_descent_edit.text())
            if self.waypoint_radius_edit.text():
                flight_characteristics["waypoint_radius"] = float(self.waypoint_radius_edit.text())
            if self.turn_radius_edit.text():
                flight_characteristics["turn_radius"] = float(self.turn_radius_edit.text())
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Invalid numeric values in flight characteristics")
            return
        
        # Validate configuration
        firmware_type = self.firmware_combo.currentText()
        vehicle_type = self.vehicle_combo.currentText()
        
        is_valid, errors, warnings = parameter_validator.validate_configuration(
            name, firmware_type, vehicle_type, parameters
        )
        
        if not is_valid:
            error_msg = "Configuration validation failed:\n" + "\n".join(errors)
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        if warnings:
            warning_msg = "Configuration warnings:\n" + "\n".join(warnings)
            QMessageBox.information(self, "Configuration Warnings", warning_msg)
        
        # Update configuration
        self.current_config.name = name
        self.current_config.description = self.description_edit.toPlainText().strip()
        self.current_config.firmware_type = firmware_type
        self.current_config.vehicle_type = vehicle_type
        self.current_config.parameters = parameters
        self.current_config.flight_characteristics = flight_characteristics
        
        # Save to manager
        if self.current_config.id in configuration_manager.configurations:
            configuration_manager.update_configuration(self.current_config)
        else:
            configuration_manager.add_configuration(self.current_config)
        
        self.load_configurations()
        QMessageBox.information(self, "Success", "Configuration saved successfully!")
    
    def apply_theme(self):
        """Apply the dark theme to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a2332;
                color: white;
            }
        """)
