#!/usr/bin/env python3
"""
Aircraft Parameter Manager for AutoFlightGenerator
Handles loading, parsing, and managing aircraft parameters for ArduPilot and PX4 firmware
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox


class AircraftParameterManager(QObject):
    """Manages aircraft-specific parameters for ArduPilot and PX4"""
    
    # Signals for parameter changes
    parameters_loaded = pyqtSignal(str)  # Emits firmware type
    parameters_updated = pyqtSignal()    # General parameter update
    validation_warnings = pyqtSignal(list)  # Emits list of warnings
    validation_errors = pyqtSignal(list)    # Emits list of errors
    
    def __init__(self):
        super().__init__()
        self.ardupilot_params = {}
        self.px4_params = {}
        self.current_firmware = None
        self.aircraft_profile = None
        self.param_file_path = None
        
        # Default parameter values for common aircraft types
        self.default_params = {
            "ardupilot": {
                "multicopter": {
                    "WPNAV_SPEED": 5.0,
                    "WPNAV_ACCEL": 50.0,
                    "WPNAV_RADIUS": 2.0,
                    "PILOT_ALT_MAX": 100.0,
                    "RTL_ALT": 50.0,
                    "WPNAV_LOITER_RAD": 2.0,
                    "MOT_SPIN_ARMED": 0.1,
                    "MOT_SPIN_MAX": 0.95
                },
                "fixed_wing": {
                    "WPNAV_SPEED": 15.0,
                    "WPNAV_ACCEL": 10.0,
                    "WPNAV_RADIUS": 50.0,
                    "PILOT_ALT_MAX": 200.0,
                    "RTL_ALT": 100.0,
                    "WPNAV_LOITER_RAD": 100.0,
                    "ARSPD_FBW_MIN": 8.0,
                    "ARSPD_FBW_MAX": 25.0
                },
                "vtol": {
                    "WPNAV_SPEED": 10.0,
                    "WPNAV_ACCEL": 25.0,
                    "WPNAV_RADIUS": 10.0,
                    "PILOT_ALT_MAX": 150.0,
                    "RTL_ALT": 75.0,
                    "WPNAV_LOITER_RAD": 20.0,
                    "Q_ENABLE": 1.0,
                    "Q_TRANS_DECEL": 2.0
                }
            },
            "px4": {
                "multicopter": {
                    "MC_XY_CRUISE": 5.0,
                    "MC_XY_VEL_MAX": 8.0,
                    "NAV_MC_ALT_RAD": 2.0,
                    "RTL_RETURN_ALT": 50.0,
                    "RTL_DESCEND_ALT": 30.0,
                    "MIS_DIST_1WP": 0.0,
                    "MIS_YAW_TAW": 0.0
                },
                "fixed_wing": {
                    "FW_AIRSPD_MAX": 25.0,
                    "FW_AIRSPD_MIN": 8.0,
                    "FW_AIRSPD_TRIM": 15.0,
                    "NAV_FW_ALT_RAD": 50.0,
                    "RTL_RETURN_ALT": 100.0,
                    "RTL_DESCEND_ALT": 50.0,
                    "MIS_DIST_1WP": 0.0
                },
                "vtol": {
                    "MC_XY_CRUISE": 8.0,
                    "FW_AIRSPD_MAX": 20.0,
                    "FW_AIRSPD_MIN": 8.0,
                    "NAV_MC_ALT_RAD": 5.0,
                    "NAV_FW_ALT_RAD": 30.0,
                    "RTL_RETURN_ALT": 75.0,
                    "VT_TRANS_MIN_TM": 5.0
                }
            }
        }
    
    def load_ardupilot_params(self, param_file_path: str) -> bool:
        """Load ArduPilot parameter file (.par)"""
        try:
            if not os.path.exists(param_file_path):
                self.validation_errors.emit([f"Parameter file not found: {param_file_path}"])
                return False
            
            self.ardupilot_params = self.parse_ardupilot_params(param_file_path)
            self.current_firmware = "ardupilot"
            self.param_file_path = param_file_path
            
            # Validate parameters
            warnings, errors = self.validate_ardupilot_parameters()
            if warnings:
                self.validation_warnings.emit(warnings)
            if errors:
                self.validation_errors.emit(errors)
                return False
            
            self.parameters_loaded.emit("ardupilot")
            self.parameters_updated.emit()
            return True
            
        except Exception as e:
            self.validation_errors.emit([f"Error loading ArduPilot parameters: {str(e)}"])
            return False
    
    def load_px4_params(self, param_file_path: str) -> bool:
        """Load PX4 parameter file (.params)"""
        try:
            if not os.path.exists(param_file_path):
                self.validation_errors.emit([f"Parameter file not found: {param_file_path}"])
                return False
            
            self.px4_params = self.parse_px4_params(param_file_path)
            self.current_firmware = "px4"
            self.param_file_path = param_file_path
            
            # Validate parameters
            warnings, errors = self.validate_px4_parameters()
            if warnings:
                self.validation_warnings.emit(warnings)
            if errors:
                self.validation_errors.emit(errors)
                return False
            
            self.parameters_loaded.emit("px4")
            self.parameters_updated.emit()
            return True
            
        except Exception as e:
            self.validation_errors.emit([f"Error loading PX4 parameters: {str(e)}"])
            return False
    
    def parse_ardupilot_params(self, param_file_path: str) -> Dict[str, float]:
        """Parse ArduPilot .par file format"""
        params = {}
        try:
            with open(param_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Handle different .par file formats
                        if '\t' in line:
                            parts = line.split('\t')
                        else:
                            parts = line.split()
                        
                        if len(parts) >= 2:
                            param_name = parts[0].strip()
                            try:
                                param_value = float(parts[1].strip())
                                params[param_name] = param_value
                            except ValueError:
                                # Skip non-numeric values
                                continue
        except Exception as e:
            raise Exception(f"Error parsing ArduPilot parameter file: {str(e)}")
        
        return params
    
    def parse_px4_params(self, param_file_path: str) -> Dict[str, float]:
        """Parse PX4 .params file format"""
        params = {}
        try:
            with open(param_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            param_name, param_value = line.split('=', 1)
                            param_name = param_name.strip()
                            param_value = param_value.strip()
                            
                            try:
                                # Handle different value formats
                                if param_value.lower() == 'true':
                                    params[param_name] = 1.0
                                elif param_value.lower() == 'false':
                                    params[param_name] = 0.0
                                else:
                                    params[param_name] = float(param_value)
                            except ValueError:
                                # Skip non-numeric values
                                continue
        except Exception as e:
            raise Exception(f"Error parsing PX4 parameter file: {str(e)}")
        
        return params
    
    def validate_ardupilot_parameters(self) -> Tuple[List[str], List[str]]:
        """Validate ArduPilot parameters for safety"""
        warnings = []
        errors = []
        
        # Check critical safety parameters
        if "PILOT_ALT_MAX" in self.ardupilot_params:
            max_alt = self.ardupilot_params["PILOT_ALT_MAX"]
            if max_alt > 400:
                warnings.append(f"Maximum altitude ({max_alt}m) exceeds recommended safety limit (400m)")
            elif max_alt < 10:
                errors.append(f"Maximum altitude ({max_alt}m) is too low for safe operation")
        
        if "WPNAV_SPEED" in self.ardupilot_params:
            max_speed = self.ardupilot_params["WPNAV_SPEED"]
            if max_speed > 50:
                warnings.append(f"Maximum waypoint speed ({max_speed}m/s) exceeds recommended limit (50m/s)")
            elif max_speed < 1:
                errors.append(f"Maximum waypoint speed ({max_speed}m/s) is too low for safe operation")
        
        if "WPNAV_RADIUS" in self.ardupilot_params:
            wp_radius = self.ardupilot_params["WPNAV_RADIUS"]
            if wp_radius < 0.5:
                errors.append(f"Waypoint radius ({wp_radius}m) is too small for safe navigation")
            elif wp_radius > 200:
                warnings.append(f"Waypoint radius ({wp_radius}m) is very large, may cause inefficient routing")
        
        return warnings, errors
    
    def validate_px4_parameters(self) -> Tuple[List[str], List[str]]:
        """Validate PX4 parameters for safety"""
        warnings = []
        errors = []
        
        # Check critical safety parameters
        if "RTL_RETURN_ALT" in self.px4_params:
            rtl_alt = self.px4_params["RTL_RETURN_ALT"]
            if rtl_alt > 300:
                warnings.append(f"RTL return altitude ({rtl_alt}m) exceeds recommended safety limit (300m)")
            elif rtl_alt < 10:
                errors.append(f"RTL return altitude ({rtl_alt}m) is too low for safe operation")
        
        if "FW_AIRSPD_MAX" in self.px4_params:
            max_airspeed = self.px4_params["FW_AIRSPD_MAX"]
            if max_airspeed > 40:
                warnings.append(f"Maximum airspeed ({max_airspeed}m/s) exceeds recommended limit (40m/s)")
            elif max_airspeed < 5:
                errors.append(f"Maximum airspeed ({max_airspeed}m/s) is too low for safe operation")
        
        if "NAV_ACC_RAD" in self.px4_params:
            nav_rad = self.px4_params["NAV_ACC_RAD"]
            if nav_rad < 0.5:
                errors.append(f"Navigation acceptance radius ({nav_rad}m) is too small for safe navigation")
            elif nav_rad > 100:
                warnings.append(f"Navigation acceptance radius ({nav_rad}m) is very large, may cause inefficient routing")
        
        return warnings, errors
    
    def get_waypoint_radius(self) -> float:
        """Get optimal waypoint radius based on aircraft performance"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.get("WPNAV_RADIUS", 2.0)
        elif self.current_firmware == "px4":
            return self.px4_params.get("NAV_ACC_RAD", 2.0)
        return 2.0  # Default
    
    def get_cruise_speed(self) -> float:
        """Get cruise speed based on aircraft performance"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.get("WPNAV_SPEED", 5.0)
        elif self.current_firmware == "px4":
            return self.px4_params.get("MC_XY_CRUISE", 5.0)
        return 5.0  # Default
    
    def get_hover_speed(self) -> float:
        """Get hover speed for multicopters"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.get("WPNAV_SPEED", 2.0) * 0.4
        elif self.current_firmware == "px4":
            return self.px4_params.get("MC_XY_CRUISE", 2.0) * 0.4
        return 2.0  # Default
    
    def get_max_climb_rate(self) -> float:
        """Get maximum climb rate"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.get("PILOT_ALT_MAX", 100.0) / 60.0  # m/s
        elif self.current_firmware == "px4":
            return self.px4_params.get("RTL_RETURN_ALT", 100.0) / 60.0  # m/s
        return 2.0  # Default 2 m/s
    
    def get_max_descent_rate(self) -> float:
        """Get maximum descent rate"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.get("PILOT_ALT_MAX", 100.0) / 60.0  # m/s
        elif self.current_firmware == "px4":
            return self.px4_params.get("RTL_DESCEND_ALT", 100.0) / 60.0  # m/s
        return 2.0  # Default 2 m/s
    
    def get_vehicle_type(self) -> int:
        """Get vehicle type for mission export"""
        if self.current_firmware == "ardupilot":
            # ArduPilot vehicle types: 1=Fixed Wing, 2=Multicopter, 3=VTOL
            if "Q_ENABLE" in self.ardupilot_params and self.ardupilot_params["Q_ENABLE"] > 0:
                return 3  # VTOL
            elif "ARSPD_FBW_MIN" in self.ardupilot_params:
                return 1  # Fixed Wing
            else:
                return 2  # Multicopter
        elif self.current_firmware == "px4":
            # PX4 vehicle types: 1=Fixed Wing, 2=Multicopter, 3=VTOL
            if "VT_TRANS_MIN_TM" in self.px4_params:
                return 3  # VTOL
            elif "FW_AIRSPD_MIN" in self.px4_params:
                return 1  # Fixed Wing
            else:
                return 2  # Multicopter
        return 2  # Default to multicopter
    
    def get_firmware_type(self) -> int:
        """Get firmware type for mission export"""
        if self.current_firmware == "ardupilot":
            return 12  # ArduPilot
        elif self.current_firmware == "px4":
            return 12  # PX4 (same as ArduPilot for compatibility)
        return 12  # Default
    
    def get_current_parameters(self) -> Dict[str, float]:
        """Get current parameters based on firmware type"""
        if self.current_firmware == "ardupilot":
            return self.ardupilot_params.copy()
        elif self.current_firmware == "px4":
            return self.px4_params.copy()
        return {}
    
    def get_export_parameters(self) -> Dict[str, Union[str, Dict[str, float]]]:
        """Get parameters formatted for export"""
        return {
            "firmware_type": self.current_firmware,
            "parameter_file": self.param_file_path,
            "parameters": self.get_current_parameters(),
            "export_timestamp": datetime.now().isoformat()
        }
    
    def clear_parameters(self):
        """Clear all loaded parameters"""
        self.ardupilot_params = {}
        self.px4_params = {}
        self.current_firmware = None
        self.param_file_path = None
        self.parameters_updated.emit()
    
    def has_parameters(self) -> bool:
        """Check if parameters are loaded"""
        return self.current_firmware is not None and bool(self.get_current_parameters())
    
    def get_parameter_summary(self) -> str:
        """Get a summary of current parameters"""
        if not self.has_parameters():
            return "No parameters loaded"
        
        params = self.get_current_parameters()
        summary = f"Firmware: {self.current_firmware.upper()}\n"
        summary += f"File: {os.path.basename(self.param_file_path) if self.param_file_path else 'Unknown'}\n"
        summary += f"Parameters loaded: {len(params)}\n\n"
        
        # Show key parameters
        key_params = ["WPNAV_SPEED", "WPNAV_RADIUS", "PILOT_ALT_MAX", "RTL_ALT"]
        for param in key_params:
            if param in params:
                summary += f"{param}: {params[param]}\n"
        
        return summary
