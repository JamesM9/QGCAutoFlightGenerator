#!/usr/bin/env python3
"""
Mission Tool Integration Base Class
Provides base functionality for integrating aircraft parameters into mission tools
"""

from typing import Dict, List, Any
from PyQt5.QtWidgets import (QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, 
                              QCheckBox, QComboBox, QGroupBox, QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from .configuration_manager import configuration_manager
from .parameter_file_manager import ParameterFileManager
from .flight_characteristics_analyzer import FlightCharacteristicsAnalyzer
from settings_manager import settings_manager
from mission_file_generator import create_file_generator


class MissionToolBase(QMainWindow):
    """Base class for mission tools with aircraft parameter integration"""
    
    # Signals
    parameters_enabled_changed = pyqtSignal(bool)
    configuration_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parameter_enabled = False
        self.current_config = None
        self.use_parameters = False  # User choice flag
        
        # Initialize parameter management components
        self.parameter_manager = ParameterFileManager()
        self.characteristics_analyzer = FlightCharacteristicsAnalyzer()
        self.active_aircraft_config = None
        
        # Connect to configuration manager signals
        configuration_manager.active_configuration_changed.connect(self.on_active_configuration_changed)
    
    def create_parameter_controls(self, parent_layout):
        """Create simplified aircraft parameter info display (no controls)"""
        # Aircraft Configuration info group
        param_group = QGroupBox("Aircraft Configuration")
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
        
        # Configuration info display
        self.config_info_label = QLabel("Parameters disabled - Enable from Dashboard")
        self.config_info_label.setFont(QFont("Arial", 10))
        self.config_info_label.setStyleSheet("color: #a0aec0; font-style: italic;")
        self.config_info_label.setWordWrap(True)
        param_layout.addWidget(self.config_info_label)
        
        # Add to parent layout
        parent_layout.addWidget(param_group)
        
        # Load initial state
        self.load_parameter_state()
    
    def load_parameter_state(self):
        """Load the current parameter state from global settings"""
        # Check if parameters are globally enabled
        self.parameter_enabled = configuration_manager.is_parameters_enabled()
        
        # Get active configuration if parameters are enabled
        if self.parameter_enabled:
            self.current_config = configuration_manager.get_active_configuration()
            if self.current_config:
                self.update_configuration_info(self.current_config)
            else:
                self.config_info_label.setText("Parameters enabled - No configuration selected")
                self.config_info_label.setStyleSheet("color: #fbbf24; font-style: italic;")
        else:
            self.config_info_label.setText("Parameters disabled - Enable from Dashboard")
            self.config_info_label.setStyleSheet("color: #a0aec0; font-style: italic;")
    
    def update_configuration_info(self, config):
        """Update the configuration info display"""
        if config:
            aircraft_type = self.detect_aircraft_type(config)
            info_text = f"Using: {config.name}\nType: {aircraft_type}\nFirmware: {config.firmware_type.title()}"
            self.config_info_label.setText(info_text)
            self.config_info_label.setStyleSheet("color: #00d4aa; font-style: normal;")
        else:
            self.config_info_label.setText("Parameters enabled - No configuration selected")
            self.config_info_label.setStyleSheet("color: #fbbf24; font-style: italic;")
    
    def detect_aircraft_type(self, config):
        """Detect aircraft type from configuration parameters"""
        if not config or not config.parameters:
            return "Unknown"
        
        params = config.parameters
        
        # Check for ArduCopter (multicopter) indicators
        if any(param in params for param in ['MC_', 'WPNAV_', 'PILOT_ALT_MAX']):
            return "Multicopter"
        
        # Check for ArduPlane (fixed-wing) indicators
        if any(param in params for param in ['FW_', 'AIRSPEED_', 'FW_AIRSPD_']):
            return "Fixed-wing"
        
        # Check for VTOL indicators
        if any(param in params for param in ['VT_', 'VTOL_', 'VT_FW_']):
            return "VTOL"
        
        # Check for PX4 indicators
        if any(param in params for param in ['MPC_', 'EKF2_', 'NAV_']):
            # Try to determine PX4 vehicle type
            if 'MPC_' in str(params):
                return "Multicopter (PX4)"
            elif 'FW_' in str(params):
                return "Fixed-wing (PX4)"
            else:
                return "PX4 Vehicle"
        
        return "Unknown"
    
    def is_parameters_enabled(self):
        """Check if parameters are globally enabled"""
        return configuration_manager.is_parameters_enabled()
    
    def get_aircraft_aware_altitude(self, mission_type, default_altitude):
        """Get altitude adjusted for aircraft parameters if enabled"""
        if not self.is_parameters_enabled() or not self.current_config:
            return default_altitude
        
        # Get altitude limits from parameters
        params = self.current_config.parameters
        
        # Check for altitude limits
        max_alt = params.get('PILOT_ALT_MAX', params.get('MPC_ALT_MODE', default_altitude))
        if isinstance(max_alt, (int, float)) and max_alt > 0:
            # Use 80% of max altitude as safe operating altitude
            return min(default_altitude, max_alt * 0.8)
        
        return default_altitude
    
    def get_aircraft_aware_waypoint_spacing(self, mission_type, default_spacing):
        """Get waypoint spacing adjusted for aircraft parameters if enabled"""
        if not self.is_parameters_enabled() or not self.current_config:
            return default_spacing
        
        params = self.current_config.parameters
        
        # Check for waypoint navigation parameters
        wp_radius = params.get('WPNAV_RADIUS', params.get('NAV_ACC_RAD', default_spacing))
        if isinstance(wp_radius, (int, float)) and wp_radius > 0:
            # Use waypoint radius as minimum spacing
            return max(default_spacing, wp_radius)
        
        return default_spacing
    
    def get_aircraft_aware_speed(self, default_speed):
        """Get speed adjusted for aircraft parameters if enabled"""
        if not self.is_parameters_enabled() or not self.current_config:
            return default_speed
        
        params = self.current_config.parameters
        
        # Check for speed parameters
        cruise_speed = params.get('WPNAV_SPEED', params.get('MPC_XY_CRUISE', params.get('AIRSPEED_CRUISE', default_speed)))
        if isinstance(cruise_speed, (int, float)) and cruise_speed > 0:
            return cruise_speed
        
        return default_speed
    
    def get_aircraft_info_for_export(self):
        """Get aircraft information for mission export"""
        if not self.is_parameters_enabled() or not self.current_config:
            return {
                'aircraft_type': 'Unknown',
                'firmware': 'Unknown',
                'configuration': 'None',
                'parameters_used': False,
                'cruiseSpeed': 15.0,  # Default cruise speed m/s
                'hoverSpeed': 5.0,    # Default hover speed m/s
                'firmwareType': 'arducopter',  # Default firmware
                'vehicleType': 'multicopter',  # Default vehicle type
                'aircraftParameters': {}
            }
        
        aircraft_type = self.detect_aircraft_type(self.current_config)
        params = self.current_config.parameters
        
        # Get aircraft-specific speeds from parameters
        cruise_speed = self.get_aircraft_aware_speed(15.0)  # Default 15 m/s
        hover_speed = params.get('PILOT_SPEED_UP', params.get('MPC_XY_P', 5.0))  # Default 5 m/s
        
        # Determine firmware type
        firmware_type = self.current_config.firmware_type.lower()
        if 'arduplane' in firmware_type:
            firmware_type = 'arduplane'
        elif 'arducopter' in firmware_type:
            firmware_type = 'arducopter'
        else:
            firmware_type = 'arducopter'  # Default
        
        # Determine vehicle type
        if 'fixed' in aircraft_type.lower() or 'plane' in aircraft_type.lower():
            vehicle_type = 'fixedwing'
        else:
            vehicle_type = 'multicopter'  # Default
        
        return {
            'aircraft_type': aircraft_type,
            'firmware': self.current_config.firmware_type,
            'configuration': self.current_config.name,
            'parameters_used': True,
            'parameter_count': len(self.current_config.parameters) if self.current_config.parameters else 0,
            'cruiseSpeed': cruise_speed,
            'hoverSpeed': hover_speed,
            'firmwareType': firmware_type,
            'vehicleType': vehicle_type,
            'aircraftParameters': params if params else {}
        }
    
    def on_active_configuration_changed(self, config_id: str):
        """Handle active configuration change from manager"""
        if config_id and self.is_parameters_enabled():
            config = configuration_manager.get_configuration(config_id)
            self.current_config = config
            self.update_configuration_info(config)
            self.configuration_changed.emit(config_id)
        else:
            self.current_config = None
            self.load_parameter_state()
    
    def refresh_parameter_state(self):
        """Refresh parameter state (called when global settings change)"""
        self.load_parameter_state()
    
    def get_file_generator(self):
        """Get file generator for current ground control station"""
        gcs_type = settings_manager.get_ground_control_station()
        return create_file_generator(gcs_type)
    
    def get_file_extension(self):
        """Get file extension based on current GCS"""
        return settings_manager.get_file_extension()
    
    def get_file_filter(self):
        """Get file filter based on current GCS"""
        return settings_manager.get_file_filter()
    
    def save_mission_file(self, mission_data, default_filename="mission"):
        """
        Save mission file using the appropriate format for the selected GCS
        
        Args:
            mission_data (dict): Mission data structure
            default_filename (str): Default filename (without extension)
            
        Returns:
            str: Path to saved file if successful, None otherwise
        """
        try:
            # Get file dialog
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Mission File", 
                f"{default_filename}{self.get_file_extension()}", 
                self.get_file_filter()
            )
            
            if not filename:
                return None
            
            # Ensure correct extension
            if not filename.endswith(self.get_file_extension()):
                filename += self.get_file_extension()
            
            # Generate file using appropriate generator
            generator = self.get_file_generator()
            success = generator.generate_file(mission_data, filename)
            
            if success:
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Mission file saved successfully!\n{filename}"
                )
                return filename
            else:
                QMessageBox.critical(
                    self, 
                    "Error", 
                    f"Failed to save mission file:\n{filename}"
                )
                return None
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Error saving mission file: {str(e)}"
            )
            return None
    
    # Enhanced Parameter-Aware Methods
    
    def set_parameter_usage(self, use_parameters: bool):
        """Allow user to enable/disable parameter-aware mission generation"""
        self.use_parameters = use_parameters
        if use_parameters and not self.active_aircraft_config:
            self.load_default_aircraft_config()
    
    def load_aircraft_parameters(self, file_path: str) -> bool:
        """Load and analyze aircraft parameters"""
        try:
            # Import parameter file
            success = self.parameter_manager.import_parameter_file(file_path)
            if success:
                # Get the imported configuration
                configs = self.parameter_manager.get_aircraft_configurations()
                if configs:
                    self.active_aircraft_config = configs[-1]  # Most recent
                    return True
            return False
        except Exception as e:
            print(f"Error loading aircraft parameters: {e}")
            return False
    
    def get_aircraft_aware_mission_settings(self) -> Dict[str, Any]:
        """Get mission settings based on aircraft parameters or defaults"""
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
                'energy_characteristics': characteristics.get('energy_characteristics', {})
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
                'energy_characteristics': {'energy_management': 'Direct'}
            }
    
    def generate_parameter_aware_mission(self, waypoints: List[Dict], mission_type: str) -> Dict[str, Any]:
        """Generate mission with aircraft-specific parameters"""
        settings = self.get_aircraft_aware_mission_settings()
        
        # Adjust mission generation based on aircraft characteristics
        if settings['energy_characteristics'].get('energy_management') == 'TECS':
            # Fixed wing/VTOL: Consider energy management
            return self._generate_energy_aware_mission(waypoints, settings, mission_type)
        else:
            # Multicopter: Direct control
            return self._generate_direct_control_mission(waypoints, settings, mission_type)
    
    def _generate_energy_aware_mission(self, waypoints: List[Dict], settings: Dict, mission_type: str) -> Dict[str, Any]:
        """Generate mission with energy management considerations"""
        # Implement TECS-aware mission generation
        # Consider climb/descent efficiency, transition energy for VTOL
        pass
    
    def _generate_direct_control_mission(self, waypoints: List[Dict], settings: Dict, mission_type: str) -> Dict[str, Any]:
        """Generate mission with direct control (multicopter)"""
        # Implement direct control mission generation
        # Consider hover characteristics, precise positioning
        pass
    
    def load_default_aircraft_config(self):
        """Load default aircraft configuration if none is set"""
        # This could load a default configuration or prompt user to select one
        pass