#!/usr/bin/env python3
"""
Parameter UI Component
Provides UI components for aircraft parameter file selection and management
"""

import os
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QGroupBox, QPushButton, QFileDialog, 
                              QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon
from .parameter_file_manager import ParameterFileManager
from .flight_characteristics_analyzer import FlightCharacteristicsAnalyzer


class ParameterAwareUIComponent(QWidget):
    """UI component for aircraft parameter file selection and management"""
    
    # Signals
    parameter_usage_changed = pyqtSignal(bool)
    parameter_file_loaded = pyqtSignal(str, str)  # filename, aircraft_type
    parameter_file_error = pyqtSignal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameter_manager = ParameterFileManager()
        self.characteristics_analyzer = FlightCharacteristicsAnalyzer()
        self.active_aircraft_config = None
        self.use_parameters = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the parameter UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Parameter file group box
        param_group = QGroupBox("Aircraft Parameters")
        param_group.setFont(QFont("Arial", 11, QFont.Bold))
        param_group.setStyleSheet("""
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
        
        param_layout = QVBoxLayout(param_group)
        param_layout.setSpacing(10)
        
        # Enable/disable parameter usage
        self.use_params_checkbox = QCheckBox("Use Aircraft Parameters")
        self.use_params_checkbox.setFont(QFont("Arial", 10))
        self.use_params_checkbox.setStyleSheet("""
            QCheckBox {
                color: #e2e8f0;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4a5568;
                border-radius: 3px;
                background-color: #2d3748;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #00d4aa;
                border-radius: 3px;
                background-color: #00d4aa;
            }
        """)
        self.use_params_checkbox.toggled.connect(self.toggle_parameter_usage)
        param_layout.addWidget(self.use_params_checkbox)
        
        # Parameter file selection
        param_file_layout = QHBoxLayout()
        self.param_file_label = QLabel("No parameter file loaded")
        self.param_file_label.setFont(QFont("Arial", 9))
        self.param_file_label.setStyleSheet("color: #888; font-style: italic;")
        self.param_file_label.setWordWrap(True)
        
        self.load_param_btn = QPushButton("Load Parameter File")
        self.load_param_btn.setFont(QFont("Arial", 9))
        self.load_param_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a5568;
                color: white;
                border: 1px solid #2d3748;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d3748;
            }
            QPushButton:pressed {
                background-color: #1a202c;
            }
            QPushButton:disabled {
                background-color: #2d3748;
                color: #888;
            }
        """)
        self.load_param_btn.clicked.connect(self.load_parameter_file)
        self.load_param_btn.setEnabled(False)
        
        param_file_layout.addWidget(self.param_file_label, 1)
        param_file_layout.addWidget(self.load_param_btn)
        param_layout.addLayout(param_file_layout)
        
        # Aircraft info display
        self.aircraft_info_label = QLabel("")
        self.aircraft_info_label.setFont(QFont("Arial", 9))
        self.aircraft_info_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        self.aircraft_info_label.setWordWrap(True)
        param_layout.addWidget(self.aircraft_info_label)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #4a5568;")
        param_layout.addWidget(separator)
        
        # Mission optimization info
        self.optimization_info_label = QLabel("")
        self.optimization_info_label.setFont(QFont("Arial", 9))
        self.optimization_info_label.setStyleSheet("color: #60a5fa; font-size: 9px;")
        self.optimization_info_label.setWordWrap(True)
        param_layout.addWidget(self.optimization_info_label)
        
        layout.addWidget(param_group)
    
    def toggle_parameter_usage(self, enabled: bool):
        """Toggle parameter-aware mission generation"""
        self.use_parameters = enabled
        self.load_param_btn.setEnabled(enabled)
        
        if enabled:
            self.param_file_label.setText("Parameter file required")
            self.param_file_label.setStyleSheet("color: #FF9800;")
            self.aircraft_info_label.setText("")
            self.optimization_info_label.setText("")
        else:
            self.param_file_label.setText("No parameter file loaded")
            self.param_file_label.setStyleSheet("color: #888; font-style: italic;")
            self.aircraft_info_label.setText("")
            self.optimization_info_label.setText("")
            self.active_aircraft_config = None
        
        self.parameter_usage_changed.emit(enabled)
    
    def load_parameter_file(self):
        """Load aircraft parameter file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Load Aircraft Parameter File",
            "",
            "Parameter Files (*.params *.param *.parm *.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                # Parse the parameter file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Detect firmware type
                firmware_type = self.parameter_manager.detect_firmware_type(content)
                if not firmware_type:
                    QMessageBox.warning(self, "Error", "Could not detect firmware type from parameter file.")
                    return
                
                # Parse parameters
                if firmware_type == "px4":
                    parameters = self.parameter_manager.parse_px4_parameters(content)
                elif firmware_type in ["arducopter", "arduplane"]:
                    parameters = self.parameter_manager.parse_ardupilot_parameters(content)
                else:
                    QMessageBox.warning(self, "Error", f"Unsupported firmware type: {firmware_type}")
                    return
                
                # Extract flight characteristics
                characteristics = self.parameter_manager.extract_flight_characteristics(parameters, firmware_type)
                
                # Create aircraft configuration
                self.active_aircraft_config = {
                    'filename': os.path.basename(file_path),
                    'file_path': file_path,
                    'firmware_type': firmware_type,
                    'parameters': parameters,
                    'characteristics': characteristics
                }
                
                # Update UI
                aircraft_type = characteristics.get('aircraft_type', 'Unknown')
                self.param_file_label.setText(f"Loaded: {os.path.basename(file_path)}")
                self.param_file_label.setStyleSheet("color: #4CAF50;")
                
                # Display aircraft info
                info_text = f"Aircraft: {aircraft_type} | "
                info_text += f"Max Speed: {characteristics.get('max_speed', 'N/A')} m/s | "
                info_text += f"Climb Rate: {characteristics.get('max_climb_rate', 'N/A')} m/s"
                self.aircraft_info_label.setText(info_text)
                
                # Display optimization info
                optimization_settings = self.characteristics_analyzer.get_mission_optimization_settings(characteristics)
                opt_text = f"Optimization: {optimization_settings.get('energy_management', 'Direct')} | "
                opt_text += f"Waypoint Spacing: {optimization_settings.get('waypoint_spacing', 'Auto')}m | "
                opt_text += f"Turn Strategy: {optimization_settings.get('turn_strategy', 'Standard')}"
                self.optimization_info_label.setText(opt_text)
                
                # Emit signal
                self.parameter_file_loaded.emit(os.path.basename(file_path), aircraft_type)
                
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Aircraft parameters loaded successfully!\nType: {aircraft_type}\nFirmware: {firmware_type.title()}"
                )
                
            except Exception as e:
                error_msg = f"Failed to load parameter file: {str(e)}"
                QMessageBox.warning(self, "Error", error_msg)
                self.parameter_file_error.emit(error_msg)
    
    def get_aircraft_characteristics(self) -> Optional[Dict[str, Any]]:
        """Get current aircraft characteristics"""
        if self.active_aircraft_config:
            return self.active_aircraft_config.get('characteristics', {})
        return None
    
    def get_mission_settings(self) -> Dict[str, Any]:
        """Get mission settings based on current aircraft configuration"""
        if self.use_parameters and self.active_aircraft_config:
            characteristics = self.active_aircraft_config.get('characteristics', {})
            return {
                'max_speed': characteristics.get('max_speed', 15.0),
                'cruise_speed': characteristics.get('cruise_speed', 10.0),
                'max_climb_rate': characteristics.get('max_climb_rate', 3.0),
                'max_descent_rate': characteristics.get('max_descent_rate', 2.0),
                'waypoint_radius': characteristics.get('waypoint_radius', 5.0),
                'turn_radius': characteristics.get('turn_radius', 50.0),
                'altitude_limits': characteristics.get('altitude_limits', {}),
                'energy_characteristics': characteristics.get('energy_characteristics', {}),
                'aircraft_type': characteristics.get('aircraft_type', 'Unknown')
            }
        else:
            # Return default settings
            return {
                'max_speed': 15.0,
                'cruise_speed': 10.0,
                'max_climb_rate': 3.0,
                'max_descent_rate': 2.0,
                'waypoint_radius': 5.0,
                'turn_radius': 50.0,
                'altitude_limits': {'min_altitude': 10.0, 'max_altitude': 1000.0},
                'energy_characteristics': {'energy_management': 'Direct'},
                'aircraft_type': 'Unknown'
            }
    
    def is_parameter_aware_enabled(self) -> bool:
        """Check if parameter-aware mission generation is enabled"""
        return self.use_parameters and self.active_aircraft_config is not None
    
    def get_aircraft_info_for_export(self) -> Dict[str, Any]:
        """Get aircraft information for mission export"""
        if not self.is_parameter_aware_enabled():
            return {
                'aircraft_type': 'Unknown',
                'firmware': 'Unknown',
                'configuration': 'None',
                'parameters_used': False,
                'cruiseSpeed': 15.0,
                'hoverSpeed': 5.0,
                'firmwareType': 'arducopter',
                'vehicleType': 'multicopter',
                'aircraftParameters': {}
            }
        
        config = self.active_aircraft_config
        characteristics = config.get('characteristics', {})
        parameters = config.get('parameters', {})
        
        aircraft_type = characteristics.get('aircraft_type', 'Unknown')
        firmware_type = config.get('firmware_type', 'Unknown')
        
        # Determine vehicle type for export
        if 'fixed' in aircraft_type.lower() or 'wing' in aircraft_type.lower():
            vehicle_type = 'fixedwing'
        elif 'vtol' in aircraft_type.lower():
            vehicle_type = 'vtol'
        else:
            vehicle_type = 'multicopter'
        
        return {
            'aircraft_type': aircraft_type,
            'firmware': firmware_type,
            'configuration': config.get('filename', 'Unknown'),
            'parameters_used': True,
            'parameter_count': len(parameters),
            'cruiseSpeed': characteristics.get('cruise_speed', 15.0),
            'hoverSpeed': characteristics.get('hover_speed', characteristics.get('cruise_speed', 5.0)),
            'firmwareType': firmware_type.lower(),
            'vehicleType': vehicle_type,
            'aircraftParameters': parameters
        }
