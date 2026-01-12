#!/usr/bin/env python3
"""
Aircraft Configuration Manager
Manages aircraft configurations, parameter files, and database operations
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox


class AircraftConfiguration:
    """Represents an aircraft configuration with parameters and flight characteristics"""
    
    def __init__(self, config_id: str = None):
        self.id = config_id or str(uuid.uuid4())
        self.name = ""
        self.description = ""
        self.firmware_type = ""  # "arducopter", "arduplane", "px4"
        self.vehicle_type = ""   # "multicopter", "fixedwing", "vtol"
        self.parameter_file = ""
        self.parameters = {}
        self.flight_characteristics = {}
        self.created_date = datetime.now()
        self.last_modified = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON storage"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'firmware_type': self.firmware_type,
            'vehicle_type': self.vehicle_type,
            'parameter_file': self.parameter_file,
            'parameters': self.parameters,
            'flight_characteristics': self.flight_characteristics,
            'created_date': self.created_date.isoformat(),
            'last_modified': self.last_modified.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AircraftConfiguration':
        """Create configuration from dictionary"""
        config = cls(data.get('id', str(uuid.uuid4())))
        config.name = data.get('name', '')
        config.description = data.get('description', '')
        config.firmware_type = data.get('firmware_type', '')
        config.vehicle_type = data.get('vehicle_type', '')
        config.parameter_file = data.get('parameter_file', '')
        config.parameters = data.get('parameters', {})
        config.flight_characteristics = data.get('flight_characteristics', {})
        
        # Parse dates
        if 'created_date' in data:
            config.created_date = datetime.fromisoformat(data['created_date'])
        if 'last_modified' in data:
            config.last_modified = datetime.fromisoformat(data['last_modified'])
        
        return config


class ParameterFile:
    """Represents a parameter file with metadata"""
    
    def __init__(self, filename: str = "", path: str = ""):
        self.filename = filename
        self.path = path
        self.firmware_type = ""
        self.imported_date = datetime.now()
        self.configurations_using = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameter file to dictionary for JSON storage"""
        return {
            'filename': self.filename,
            'path': self.path,
            'firmware_type': self.firmware_type,
            'imported_date': self.imported_date.isoformat(),
            'configurations_using': self.configurations_using
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterFile':
        """Create parameter file from dictionary"""
        param_file = cls(data.get('filename', ''), data.get('path', ''))
        param_file.firmware_type = data.get('firmware_type', '')
        param_file.configurations_using = data.get('configurations_using', [])
        
        if 'imported_date' in data:
            param_file.imported_date = datetime.fromisoformat(data['imported_date'])
        
        return param_file


class AircraftConfigurationManager(QObject):
    """Main manager for aircraft configurations and parameter files"""
    
    # Signals
    configuration_updated = pyqtSignal(str)  # config_id
    configuration_deleted = pyqtSignal(str)  # config_id
    active_configuration_changed = pyqtSignal(str)  # config_id
    parameter_file_imported = pyqtSignal(str)  # filename
    
    def __init__(self, data_dir: str = "aircraft_parameters/data"):
        super().__init__()
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "aircraft_configurations.json")
        self.parameter_files_dir = os.path.join(data_dir, "parameter_files")
        
        # Ensure directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(self.parameter_files_dir, exist_ok=True)
        
        # Load data
        self.configurations: Dict[str, AircraftConfiguration] = {}
        self.parameter_files: Dict[str, ParameterFile] = {}
        self.active_configuration_id: Optional[str] = None
        
        self.load_data()
    
    def load_data(self):
        """Load configurations and parameter files from disk"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load configurations
                configs_data = data.get('aircraft_configurations', {})
                for config_id, config_data in configs_data.items():
                    self.configurations[config_id] = AircraftConfiguration.from_dict(config_data)
                
                # Load parameter files
                param_files_data = data.get('parameter_files', {})
                for filename, file_data in param_files_data.items():
                    self.parameter_files[filename] = ParameterFile.from_dict(file_data)
                
                # Load active configuration
                self.active_configuration_id = data.get('active_configuration')
                
        except Exception as e:
            print(f"Error loading aircraft configuration data: {e}")
            # Initialize with default data
            self._create_default_configurations()
    
    def save_data(self):
        """Save configurations and parameter files to disk"""
        try:
            data = {
                'aircraft_configurations': {
                    config_id: config.to_dict() 
                    for config_id, config in self.configurations.items()
                },
                'parameter_files': {
                    filename: param_file.to_dict()
                    for filename, param_file in self.parameter_files.items()
                },
                'active_configuration': self.active_configuration_id
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving aircraft configuration data: {e}")
    
    def _create_default_configurations(self):
        """Create default aircraft configurations"""
        # Default ArduCopter configuration
        arducopter_config = AircraftConfiguration()
        arducopter_config.name = "Default ArduCopter"
        arducopter_config.description = "Default configuration for ArduCopter multicopters"
        arducopter_config.firmware_type = "arducopter"
        arducopter_config.vehicle_type = "multicopter"
        arducopter_config.parameters = {
            "RTL_ALT": 10000,  # 100m in cm
            "RTL_SPEED": 500,  # 5 m/s in cm/s
            "WPNAV_SPEED": 1000,  # 10 m/s in cm/s
            "LAND_SPEED": 50,  # 0.5 m/s in cm/s
            "PILOT_SPEED_UP": 300,  # 3 m/s in cm/s
            "PILOT_SPEED_DN": 200,  # 2 m/s in cm/s
            "ANGLE_MAX": 4500,  # 45 degrees in centidegrees
            "WP_RADIUS": 200,  # 2m in cm
        }
        arducopter_config.flight_characteristics = {
            "max_speed": 15.0,  # m/s
            "max_climb_rate": 3.0,  # m/s
            "max_descent_rate": 2.0,  # m/s
            "waypoint_radius": 2.0,  # m
            "turn_radius": 5.0,  # m
        }
        self.configurations[arducopter_config.id] = arducopter_config
        
        # Default ArduPlane configuration
        arduplane_config = AircraftConfiguration()
        arduplane_config.name = "Default ArduPlane"
        arduplane_config.description = "Default configuration for ArduPlane fixed-wing aircraft"
        arduplane_config.firmware_type = "arduplane"
        arduplane_config.vehicle_type = "fixedwing"
        arduplane_config.parameters = {
            "RTL_ALT": 10000,  # 100m in cm
            "RTL_SPEED": 1000,  # 10 m/s in cm/s
            "AIRSPEED_CRUISE": 15.0,  # m/s
            "AIRSPEED_MIN": 10.0,  # m/s
            "AIRSPEED_MAX": 25.0,  # m/s
            "WP_RADIUS": 1000,  # 10m in cm
            "LAND_SPEED": 80,  # 0.8 m/s in cm/s
        }
        arduplane_config.flight_characteristics = {
            "max_speed": 25.0,  # m/s
            "max_climb_rate": 5.0,  # m/s
            "max_descent_rate": 3.0,  # m/s
            "waypoint_radius": 10.0,  # m
            "turn_radius": 50.0,  # m
        }
        self.configurations[arduplane_config.id] = arduplane_config
        
        # Default PX4 configuration
        px4_config = AircraftConfiguration()
        px4_config.name = "Default PX4"
        px4_config.description = "Default configuration for PX4 multicopters"
        px4_config.firmware_type = "px4"
        px4_config.vehicle_type = "multicopter"
        px4_config.parameters = {
            "MPC_XY_VEL_MAX": 5.0,  # m/s
            "MPC_Z_VEL_MAX_UP": 3.0,  # m/s
            "MPC_Z_VEL_MAX_DN": 1.0,  # m/s
            "NAV_ACC_RAD": 2.0,  # m
            "RTL_RETURN_ALT": 60.0,  # m
            "MIS_TAKEOFF_ALT": 2.5,  # m
        }
        px4_config.flight_characteristics = {
            "max_speed": 15.0,  # m/s
            "max_climb_rate": 3.0,  # m/s
            "max_descent_rate": 1.0,  # m/s
            "waypoint_radius": 2.0,  # m
            "turn_radius": 5.0,  # m
        }
        self.configurations[px4_config.id] = px4_config
        
        # Set first configuration as active
        self.active_configuration_id = arducopter_config.id
        
        # Save default data
        self.save_data()
    
    def get_configurations(self) -> List[AircraftConfiguration]:
        """Get all aircraft configurations"""
        return list(self.configurations.values())
    
    def get_configuration(self, config_id: str) -> Optional[AircraftConfiguration]:
        """Get a specific configuration by ID"""
        return self.configurations.get(config_id)
    
    def get_active_configuration(self) -> Optional[AircraftConfiguration]:
        """Get the currently active configuration"""
        if self.active_configuration_id:
            return self.configurations.get(self.active_configuration_id)
        return None
    
    def is_parameters_enabled(self) -> bool:
        """Check if parameters are globally enabled"""
        # For now, parameters are enabled if there's an active configuration
        # In the future, this could be a separate global setting
        return self.active_configuration_id is not None
    
    def set_active_configuration(self, config_id: str):
        """Set the active configuration"""
        if config_id in self.configurations:
            self.active_configuration_id = config_id
            self.save_data()
            self.active_configuration_changed.emit(config_id)
    
    def add_configuration(self, config: AircraftConfiguration) -> str:
        """Add a new configuration"""
        self.configurations[config.id] = config
        self.save_data()
        self.configuration_updated.emit(config.id)
        return config.id
    
    def update_configuration(self, config: AircraftConfiguration):
        """Update an existing configuration"""
        if config.id in self.configurations:
            config.last_modified = datetime.now()
            self.configurations[config.id] = config
            self.save_data()
            self.configuration_updated.emit(config.id)
    
    def delete_configuration(self, config_id: str) -> bool:
        """Delete a configuration"""
        if config_id in self.configurations:
            # Remove from parameter files that use this configuration
            for param_file in self.parameter_files.values():
                if config_id in param_file.configurations_using:
                    param_file.configurations_using.remove(config_id)
            
            del self.configurations[config_id]
            
            # If this was the active configuration, clear it
            if self.active_configuration_id == config_id:
                self.active_configuration_id = None
            
            self.save_data()
            self.configuration_deleted.emit(config_id)
            return True
        return False
    
    def get_parameter_files(self) -> List[ParameterFile]:
        """Get all parameter files"""
        return list(self.parameter_files.values())
    
    def get_parameter_file(self, filename: str) -> Optional[ParameterFile]:
        """Get a specific parameter file by filename"""
        return self.parameter_files.get(filename)
    
    def add_parameter_file(self, param_file: ParameterFile):
        """Add a new parameter file"""
        self.parameter_files[param_file.filename] = param_file
        self.save_data()
        self.parameter_file_imported.emit(param_file.filename)
    
    def delete_parameter_file(self, filename: str) -> bool:
        """Delete a parameter file"""
        if filename in self.parameter_files:
            param_file = self.parameter_files[filename]
            
            # Check if any configurations are using this file
            if param_file.configurations_using:
                return False  # Cannot delete if in use
            
            # Remove physical file
            file_path = os.path.join(self.parameter_files_dir, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            del self.parameter_files[filename]
            self.save_data()
            return True
        return False
    
    def get_configurations_for_firmware(self, firmware_type: str) -> List[AircraftConfiguration]:
        """Get configurations for a specific firmware type"""
        return [config for config in self.configurations.values() 
                if config.firmware_type == firmware_type]
    
    def get_parameter_value(self, param_name: str, default_value: Any = None) -> Any:
        """Get a parameter value from the active configuration"""
        active_config = self.get_active_configuration()
        if active_config and param_name in active_config.parameters:
            return active_config.parameters[param_name]
        return default_value
    
    def get_flight_characteristic(self, characteristic_name: str, default_value: Any = None) -> Any:
        """Get a flight characteristic from the active configuration"""
        active_config = self.get_active_configuration()
        if active_config and characteristic_name in active_config.flight_characteristics:
            return active_config.flight_characteristics[characteristic_name]
        return default_value


# Global instance
configuration_manager = AircraftConfigurationManager()
