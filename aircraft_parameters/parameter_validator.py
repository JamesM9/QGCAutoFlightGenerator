#!/usr/bin/env python3
"""
Parameter Validator
Validates parameter files and configurations for correctness
"""

from typing import Dict, List, Optional, Tuple, Any
import re


class ParameterValidator:
    """Validates parameter files and configurations"""
    
    # Known parameter ranges and types for different firmware types
    ARDUCOPTER_PARAMETERS = {
        "RTL_ALT": {"type": int, "min": 30, "max": 300000, "unit": "cm"},
        "RTL_SPEED": {"type": int, "min": 0, "max": 2000, "unit": "cm/s"},
        "WPNAV_SPEED": {"type": int, "min": 0, "max": 2000, "unit": "cm/s"},
        "LAND_SPEED": {"type": int, "min": 30, "max": 200, "unit": "cm/s"},
        "PILOT_SPEED_UP": {"type": int, "min": 50, "max": 500, "unit": "cm/s"},
        "PILOT_SPEED_DN": {"type": int, "min": 0, "max": 500, "unit": "cm/s"},
        "ANGLE_MAX": {"type": int, "min": 1000, "max": 8000, "unit": "centidegrees"},
        "WP_RADIUS": {"type": int, "min": 1, "max": 32767, "unit": "cm"},
        "THR_DZ": {"type": int, "min": 0, "max": 300, "unit": "PWM"},
        "RC_SPEED": {"type": int, "min": 50, "max": 490, "unit": "Hz"},
    }
    
    ARDUPLANE_PARAMETERS = {
        "RTL_ALT": {"type": int, "min": 30, "max": 3000, "unit": "cm"},
        "RTL_SPEED": {"type": int, "min": 0, "max": 2000, "unit": "cm/s"},
        "AIRSPEED_CRUISE": {"type": float, "min": 5.0, "max": 50.0, "unit": "m/s"},
        "AIRSPEED_MIN": {"type": float, "min": 5.0, "max": 30.0, "unit": "m/s"},
        "AIRSPEED_MAX": {"type": float, "min": 10.0, "max": 50.0, "unit": "m/s"},
        "WP_RADIUS": {"type": int, "min": 1, "max": 32767, "unit": "cm"},
        "THR_MIN": {"type": int, "min": -100, "max": 100, "unit": "%"},
        "THR_MAX": {"type": int, "min": 0, "max": 100, "unit": "%"},
        "FW_R_LIM": {"type": float, "min": 10.0, "max": 90.0, "unit": "deg"},
    }
    
    PX4_PARAMETERS = {
        "MPC_XY_VEL_MAX": {"type": float, "min": 2.0, "max": 20.0, "unit": "m/s"},
        "MPC_Z_VEL_MAX_UP": {"type": float, "min": 1.0, "max": 8.0, "unit": "m/s"},
        "MPC_Z_VEL_MAX_DN": {"type": float, "min": 1.0, "max": 4.0, "unit": "m/s"},
        "NAV_ACC_RAD": {"type": float, "min": 0.1, "max": 100.0, "unit": "m"},
        "RTL_RETURN_ALT": {"type": float, "min": 0.0, "max": 100.0, "unit": "m"},
        "FW_AIRSPD_MIN": {"type": float, "min": 5.0, "max": 30.0, "unit": "m/s"},
        "FW_AIRSPD_MAX": {"type": float, "min": 10.0, "max": 50.0, "unit": "m/s"},
        "EKF2_REQ_EPH": {"type": float, "min": 0.01, "max": 100.0, "unit": "m"},
    }
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_parameter_file(self, parameters: Dict[str, Any], 
                              firmware_type: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a parameter file
        Returns (is_valid, errors, warnings)
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Get parameter definitions for firmware type
        param_definitions = self.get_parameter_definitions(firmware_type)
        
        # Validate each parameter
        for param_name, param_value in parameters.items():
            self.validate_parameter(param_name, param_value, param_definitions)
        
        # Check for critical parameters
        self.check_critical_parameters(parameters, firmware_type)
        
        return len(self.validation_errors) == 0, self.validation_errors, self.validation_warnings
    
    def get_parameter_definitions(self, firmware_type: str) -> Dict[str, Dict]:
        """Get parameter definitions for a firmware type"""
        if firmware_type == "arducopter":
            return self.ARDUCOPTER_PARAMETERS
        elif firmware_type == "arduplane":
            return self.ARDUPLANE_PARAMETERS
        elif firmware_type == "px4":
            return self.PX4_PARAMETERS
        else:
            return {}
    
    def validate_parameter(self, param_name: str, param_value: Any, 
                          param_definitions: Dict[str, Dict]):
        """Validate a single parameter"""
        if param_name not in param_definitions:
            # Unknown parameter - just a warning
            self.validation_warnings.append(f"Unknown parameter: {param_name}")
            return
        
        definition = param_definitions[param_name]
        expected_type = definition["type"]
        
        # Check type
        if not isinstance(param_value, expected_type):
            self.validation_errors.append(
                f"Parameter {param_name}: Expected {expected_type.__name__}, got {type(param_value).__name__}"
            )
            return
        
        # Check range
        if "min" in definition and param_value < definition["min"]:
            self.validation_errors.append(
                f"Parameter {param_name}: Value {param_value} is below minimum {definition['min']} {definition['unit']}"
            )
        
        if "max" in definition and param_value > definition["max"]:
            self.validation_errors.append(
                f"Parameter {param_name}: Value {param_value} is above maximum {definition['max']} {definition['unit']}"
            )
    
    def check_critical_parameters(self, parameters: Dict[str, Any], firmware_type: str):
        """Check for critical parameters that should be present"""
        critical_params = self.get_critical_parameters(firmware_type)
        
        for param_name in critical_params:
            if param_name not in parameters:
                self.validation_warnings.append(
                    f"Critical parameter missing: {param_name}"
                )
    
    def get_critical_parameters(self, firmware_type: str) -> List[str]:
        """Get list of critical parameters for a firmware type"""
        if firmware_type == "arducopter":
            return ["RTL_ALT", "RTL_SPEED", "WPNAV_SPEED", "LAND_SPEED"]
        elif firmware_type == "arduplane":
            return ["RTL_ALT", "RTL_SPEED", "AIRSPEED_CRUISE", "AIRSPEED_MIN", "AIRSPEED_MAX"]
        elif firmware_type == "px4":
            return ["MPC_XY_VEL_MAX", "MPC_Z_VEL_MAX_UP", "MPC_Z_VEL_MAX_DN", "NAV_ACC_RAD"]
        else:
            return []
    
    def validate_configuration(self, config_name: str, firmware_type: str, 
                             vehicle_type: str, parameters: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """Validate an aircraft configuration"""
        self.validation_errors = []
        self.validation_warnings = []
        
        # Validate configuration name
        if not config_name or len(config_name.strip()) == 0:
            self.validation_errors.append("Configuration name cannot be empty")
        
        # Validate firmware type
        if firmware_type not in ["arducopter", "arduplane", "px4"]:
            self.validation_errors.append(f"Invalid firmware type: {firmware_type}")
        
        # Validate vehicle type
        if vehicle_type not in ["multicopter", "fixedwing", "vtol"]:
            self.validation_errors.append(f"Invalid vehicle type: {vehicle_type}")
        
        # Validate firmware/vehicle type compatibility
        if firmware_type == "arduplane" and vehicle_type != "fixedwing":
            self.validation_warnings.append("ArduPlane firmware typically used with fixed-wing aircraft")
        
        if firmware_type == "arducopter" and vehicle_type not in ["multicopter", "vtol"]:
            self.validation_warnings.append("ArduCopter firmware typically used with multicopter or VTOL aircraft")
        
        # Validate parameters
        is_valid, param_errors, param_warnings = self.validate_parameter_file(parameters, firmware_type)
        self.validation_errors.extend(param_errors)
        self.validation_warnings.extend(param_warnings)
        
        return len(self.validation_errors) == 0, self.validation_errors, self.validation_warnings
    
    def suggest_parameter_values(self, firmware_type: str, vehicle_type: str) -> Dict[str, Any]:
        """Suggest default parameter values for a firmware/vehicle type combination"""
        suggestions = {}
        
        if firmware_type == "arducopter":
            suggestions = {
                "RTL_ALT": 10000,  # 100m
                "RTL_SPEED": 500,  # 5 m/s
                "WPNAV_SPEED": 1000,  # 10 m/s
                "LAND_SPEED": 50,  # 0.5 m/s
                "PILOT_SPEED_UP": 300,  # 3 m/s
                "PILOT_SPEED_DN": 200,  # 2 m/s
                "ANGLE_MAX": 4500,  # 45 degrees
                "WP_RADIUS": 200,  # 2m
            }
        
        elif firmware_type == "arduplane":
            suggestions = {
                "RTL_ALT": 10000,  # 100m
                "RTL_SPEED": 1000,  # 10 m/s
                "AIRSPEED_CRUISE": 15.0,  # m/s
                "AIRSPEED_MIN": 10.0,  # m/s
                "AIRSPEED_MAX": 25.0,  # m/s
                "WP_RADIUS": 1000,  # 10m
                "THR_MIN": 0,  # %
                "THR_MAX": 100,  # %
                "FW_R_LIM": 45.0,  # degrees
            }
        
        elif firmware_type == "px4":
            suggestions = {
                "MPC_XY_VEL_MAX": 5.0,  # m/s
                "MPC_Z_VEL_MAX_UP": 3.0,  # m/s
                "MPC_Z_VEL_MAX_DN": 1.0,  # m/s
                "NAV_ACC_RAD": 2.0,  # m
                "RTL_RETURN_ALT": 60.0,  # m
                "MIS_TAKEOFF_ALT": 2.5,  # m
                "EKF2_REQ_EPH": 5.0,  # m
                "EKF2_REQ_EPV": 8.0,  # m
            }
        
        return suggestions


# Global instance
parameter_validator = ParameterValidator()
