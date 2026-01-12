#!/usr/bin/env python3
"""
Parameter File Manager
Handles importing, parsing, and managing parameter files from ArduPilot and PX4
"""

import os
import re
from typing import Dict, List, Optional, Tuple, Any
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class ParameterFileManager(QObject):
    """Manages parameter file import, export, and parsing"""
    
    # Signals
    file_imported = pyqtSignal(str, str)  # filename, firmware_type
    import_error = pyqtSignal(str)  # error_message
    
    def __init__(self, parameter_files_dir: str = "aircraft_parameters/data/parameter_files"):
        super().__init__()
        self.parameter_files_dir = parameter_files_dir
        os.makedirs(parameter_files_dir, exist_ok=True)
    
    def import_parameter_file(self, parent_widget=None) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        Import a parameter file and return (filename, firmware_type, parameters)
        Returns None if import was cancelled or failed
        """
        try:
            # Open file dialog
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "Import Parameter File",
                "",
                "Parameter Files (*.param *.params *.txt *.parm);;All Files (*)"
            )
            
            if not file_path:
                return None
            
            # Parse the file
            filename = os.path.basename(file_path)
            firmware_type, parameters = self.parse_parameter_file(file_path)
            
            if not firmware_type:
                QMessageBox.warning(
                    parent_widget,
                    "Import Error",
                    "Could not determine firmware type from parameter file."
                )
                return None
            
            # Copy file to parameter files directory
            dest_path = os.path.join(self.parameter_files_dir, filename)
            with open(file_path, 'r') as src, open(dest_path, 'w') as dst:
                dst.write(src.read())
            
            self.file_imported.emit(filename, firmware_type)
            return filename, firmware_type, parameters
            
        except Exception as e:
            error_msg = f"Error importing parameter file: {str(e)}"
            self.import_error.emit(error_msg)
            if parent_widget:
                QMessageBox.critical(parent_widget, "Import Error", error_msg)
            return None
    
    def parse_parameter_file(self, file_path: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Parse a parameter file and return (firmware_type, parameters)
        Returns (None, {}) if parsing fails
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Detect firmware type
            firmware_type = self.detect_firmware_type(content)
            if not firmware_type:
                return None, {}
            
            # Parse parameters based on firmware type
            if firmware_type in ["arducopter", "arduplane"]:
                parameters = self.parse_ardupilot_parameters(content)
            elif firmware_type == "px4":
                parameters = self.parse_px4_parameters(content)
            else:
                return None, {}
            
            return firmware_type, parameters
            
        except Exception as e:
            print(f"Error parsing parameter file {file_path}: {e}")
            return None, {}
    
    def detect_firmware_type(self, content: str) -> Optional[str]:
        """Detect firmware type from parameter file content"""
        content_lower = content.lower()
        
        # Check for ArduPilot indicators
        if any(indicator in content_lower for indicator in [
            "arducopter", "arduplane", "ardupilot", "copter", "plane"
        ]):
            # Determine if it's copter or plane
            if any(indicator in content_lower for indicator in [
                "arducopter", "copter", "quad", "hex", "octa"
            ]):
                return "arducopter"
            elif any(indicator in content_lower for indicator in [
                "arduplane", "plane", "fixedwing", "fixed-wing"
            ]):
                return "arduplane"
            else:
                return "arducopter"  # Default to copter
        
        # Check for PX4 indicators
        elif any(indicator in content_lower for indicator in [
            "px4", "px4_", "mpc_", "fw_", "ekf2_", "nav_"
        ]):
            return "px4"
        
        return None
    
    def parse_ardupilot_parameters(self, content: str) -> Dict[str, Any]:
        """Parse ArduPilot parameter file format"""
        parameters = {}
        
        # ArduPilot format: PARAM_NAME,value
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split on comma
            parts = line.split(',', 1)
            if len(parts) == 2:
                param_name = parts[0].strip()
                param_value = parts[1].strip()
                
                # Try to convert to appropriate type
                try:
                    # Try integer first
                    if '.' not in param_value:
                        parameters[param_name] = int(param_value)
                    else:
                        parameters[param_name] = float(param_value)
                except ValueError:
                    # Keep as string if conversion fails
                    parameters[param_name] = param_value
        
        return parameters
    
    def parse_px4_parameters(self, content: str) -> Dict[str, Any]:
        """Parse PX4 parameter file format: instance_id\tcomponent_id\tparam_name\tvalue\ttype"""
        parameters = {}
        
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split on tabs - PX4 format: instance_id\tcomponent_id\tparam_name\tvalue\ttype
            parts = line.split('\t')
            if len(parts) >= 4:
                param_name = parts[2].strip()  # Parameter name is in column 3
                param_value = parts[3].strip()  # Value is in column 4
                param_type = parts[4].strip() if len(parts) > 4 else "9"  # Type is in column 5
                
                # Convert to appropriate type based on PX4 type codes
                try:
                    if param_type == "6":  # Integer type
                        parameters[param_name] = int(float(param_value))  # Handle scientific notation
                    elif param_type == "9":  # Float type
                        parameters[param_name] = float(param_value)
                    else:
                        # Default to float for unknown types
                        if '.' in param_value or 'e' in param_value.lower():
                            parameters[param_name] = float(param_value)
                        else:
                            parameters[param_name] = int(param_value)
                except ValueError:
                    # Keep as string if conversion fails
                    parameters[param_name] = param_value
        
        return parameters
    
    def export_parameter_file(self, parameters: Dict[str, Any], firmware_type: str, 
                            filename: str, parent_widget=None) -> bool:
        """Export parameters to a file"""
        try:
            # Open save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                parent_widget,
                "Export Parameter File",
                filename,
                "Parameter Files (*.param *.params);;Text Files (*.txt);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # Format parameters based on firmware type
            if firmware_type in ["arducopter", "arduplane"]:
                content = self.format_ardupilot_parameters(parameters)
            elif firmware_type == "px4":
                content = self.format_px4_parameters(parameters)
            else:
                return False
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            if parent_widget:
                QMessageBox.critical(
                    parent_widget,
                    "Export Error",
                    f"Error exporting parameter file: {str(e)}"
                )
            return False
    
    def format_ardupilot_parameters(self, parameters: Dict[str, Any]) -> str:
        """Format parameters in ArduPilot format"""
        lines = []
        for param_name, param_value in sorted(parameters.items()):
            lines.append(f"{param_name},{param_value}")
        return '\n'.join(lines)
    
    def format_px4_parameters(self, parameters: Dict[str, Any]) -> str:
        """Format parameters in PX4 format"""
        lines = []
        for param_name, param_value in sorted(parameters.items()):
            lines.append(f"{param_name} {param_value}")
        return '\n'.join(lines)
    
    def get_parameter_file_path(self, filename: str) -> str:
        """Get the full path to a parameter file"""
        return os.path.join(self.parameter_files_dir, filename)
    
    def parameter_file_exists(self, filename: str) -> bool:
        """Check if a parameter file exists"""
        return os.path.exists(self.get_parameter_file_path(filename))
    
    def delete_parameter_file(self, filename: str) -> bool:
        """Delete a parameter file from disk"""
        try:
            file_path = self.get_parameter_file_path(filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting parameter file {filename}: {e}")
            return False
    
    def detect_aircraft_type_from_parameters(self, parameters: Dict[str, Any]) -> str:
        """Enhanced aircraft type detection based on parameter analysis"""
        
        # Check for VTOL indicators first (highest priority)
        if 'VT_TYPE' in parameters and parameters['VT_TYPE'] > 0:
            return 'VTOL'
        
        # Check for Multicopter indicators (check before Fixed Wing)
        multicopter_indicators = ['MC_ROLLRATE_P', 'MPC_XY_CRUISE', 'MPC_THR_HOVER', 'MPC_XY_VEL_MAX']
        if any(param in parameters for param in multicopter_indicators):
            # Count MPC vs FW parameters to determine primary type
            mpc_count = sum(1 for key in parameters.keys() if key.startswith('MPC_'))
            fw_count = sum(1 for key in parameters.keys() if key.startswith('FW_'))
            
            # If significantly more MPC parameters, it's likely multicopter
            if mpc_count > fw_count * 2:  # At least 2x more MPC parameters
                return 'Multicopter'
        
        # Check for Fixed Wing indicators
        fixed_wing_indicators = ['FW_AIRSPD_MAX', 'FW_T_CLMB_MAX', 'FW_T_SINK_MAX', 'FW_AIRSPD_TRIM']
        if any(param in parameters for param in fixed_wing_indicators):
            return 'FixedWing'
        
        # Fallback detection based on parameter patterns
        param_keys = str(parameters.keys())
        mpc_count = param_keys.count('MPC_')
        fw_count = param_keys.count('FW_')
        
        if mpc_count > fw_count and mpc_count > 5:  # More MPC parameters than FW
            return 'Multicopter'
        elif fw_count > mpc_count and fw_count > 5:  # More FW parameters than MPC
            return 'FixedWing'
        
        return 'Unknown'
    
    def extract_flight_characteristics(self, parameters: Dict[str, Any], 
                                     firmware_type: str) -> Dict[str, Any]:
        """Extract flight characteristics from parameters"""
        characteristics = {}
        
        # Detect aircraft type from parameters
        aircraft_type = self.detect_aircraft_type_from_parameters(parameters)
        characteristics['aircraft_type'] = aircraft_type
        
        if firmware_type == "arducopter":
            characteristics.update({
                "max_speed": parameters.get("WPNAV_SPEED", 1000) / 100.0,  # cm/s to m/s
                "cruise_speed": parameters.get("WPNAV_SPEED", 1000) / 100.0 * 0.8,  # 80% of max
                "max_climb_rate": parameters.get("PILOT_SPEED_UP", 300) / 100.0,  # cm/s to m/s
                "max_descent_rate": parameters.get("PILOT_SPEED_DN", 200) / 100.0,  # cm/s to m/s
                "waypoint_radius": parameters.get("WP_RADIUS", 200) / 100.0,  # cm to m
                "turn_radius": parameters.get("WP_RADIUS", 200) / 100.0 * 2.5,  # Estimate
            })
        
        elif firmware_type == "arduplane":
            characteristics.update({
                "max_speed": parameters.get("AIRSPEED_MAX", 25.0),  # m/s
                "cruise_speed": parameters.get("AIRSPEED_CRUISE", 20.0),  # m/s
                "max_climb_rate": 5.0,  # Estimate for fixed-wing
                "max_descent_rate": 3.0,  # Estimate for fixed-wing
                "waypoint_radius": parameters.get("WP_RADIUS", 1000) / 100.0,  # cm to m
                "turn_radius": parameters.get("WP_RADIUS", 1000) / 100.0 * 5.0,  # Estimate
            })
        
        elif firmware_type == "px4":
            if aircraft_type == 'VTOL':
                characteristics.update({
                    "max_speed": parameters.get("FW_AIRSPD_MAX", 30.0),  # Forward flight speed
                    "cruise_speed": parameters.get("FW_AIRSPD_TRIM", 15.0),  # Cruise speed
                    "hover_speed": parameters.get("MPC_XY_CRUISE", 5.0),  # Hover speed
                    "max_climb_rate": parameters.get("FW_T_CLMB_MAX", 5.0),  # Forward flight climb
                    "max_descent_rate": parameters.get("FW_T_SINK_MAX", 8.0),  # Forward flight descent
                    "waypoint_radius": parameters.get("NAV_FW_ALT_RAD", 10.0),  # Fixed wing radius
                    "turn_radius": self._calculate_turn_radius(parameters.get("FW_AIRSPD_TRIM", 15.0), 
                                                             parameters.get("FW_R_LIM", 35.0)),
                    "transition_airspeed": parameters.get("VT_ARSP_TRANS", 16.0),
                    "energy_management": "TECS"
                })
            elif aircraft_type == 'FixedWing':
                characteristics.update({
                    "max_speed": parameters.get("FW_AIRSPD_MAX", 30.0),  # m/s
                    "cruise_speed": parameters.get("FW_AIRSPD_TRIM", 20.0),  # m/s
                    "max_climb_rate": parameters.get("FW_T_CLMB_MAX", 5.0),  # m/s
                    "max_descent_rate": parameters.get("FW_T_SINK_MAX", 8.0),  # m/s
                    "waypoint_radius": parameters.get("NAV_FW_ALT_RAD", 10.0),  # m
                    "turn_radius": self._calculate_turn_radius(parameters.get("FW_AIRSPD_TRIM", 20.0), 
                                                             parameters.get("FW_R_LIM", 35.0)),
                    "energy_management": "TECS"
                })
            elif aircraft_type == 'Multicopter':
                characteristics.update({
                    "max_speed": parameters.get("MPC_XY_VEL_MAX", 12.0),  # m/s
                    "cruise_speed": parameters.get("MPC_XY_CRUISE", 5.0),  # m/s
                    "max_climb_rate": parameters.get("MPC_Z_VEL_MAX_UP", 3.0),  # m/s
                    "max_descent_rate": parameters.get("MPC_Z_VEL_MAX_DN", 2.0),  # m/s
                    "waypoint_radius": parameters.get("NAV_MC_ALT_RAD", 0.8),  # m
                    "turn_radius": self._calculate_turn_radius(parameters.get("MPC_XY_CRUISE", 5.0), 
                                                             parameters.get("MPC_MAN_TILT_MAX", 35.0)),
                    "hover_throttle": parameters.get("MPC_THR_HOVER", 0.5),
                    "energy_management": "Direct"
                })
            else:
                # Default PX4 characteristics
                characteristics.update({
                    "max_speed": parameters.get("MPC_XY_VEL_MAX", 5.0),  # m/s
                    "cruise_speed": parameters.get("MPC_XY_CRUISE", 5.0),  # m/s
                    "max_climb_rate": parameters.get("MPC_Z_VEL_MAX_UP", 3.0),  # m/s
                    "max_descent_rate": parameters.get("MPC_Z_VEL_MAX_DN", 1.0),  # m/s
                    "waypoint_radius": parameters.get("NAV_ACC_RAD", 2.0),  # m
                    "turn_radius": parameters.get("NAV_ACC_RAD", 2.0) * 2.5,  # Estimate
                })
        
        return characteristics
    
    def _calculate_turn_radius(self, speed: float, max_bank_angle: float) -> float:
        """Calculate turn radius based on speed and bank angle"""
        import math
        if max_bank_angle <= 0:
            return 50.0  # Default turn radius
        return (speed ** 2) / (9.81 * math.tan(math.radians(max_bank_angle)))


# Global instance
parameter_file_manager = ParameterFileManager()
