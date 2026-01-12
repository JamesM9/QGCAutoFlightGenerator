#!/usr/bin/env python3
"""
Aircraft Profile Manager for AutoFlightGenerator
Manages saved aircraft profiles with their associated parameters
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal
from aircraft_parameter_manager import AircraftParameterManager


class AircraftProfile:
    """Represents an aircraft profile with parameters and metadata"""
    
    def __init__(self, name: str, firmware_type: str, parameters: Dict[str, float], 
                 aircraft_type: str = "Unknown", description: str = ""):
        self.name = name
        self.firmware_type = firmware_type
        self.parameters = parameters
        self.aircraft_type = aircraft_type
        self.description = description
        self.created_date = datetime.now().isoformat()
        self.last_used = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.parameter_file_path = None
        self.is_default = False
        
    def to_dict(self) -> Dict:
        """Convert profile to dictionary for storage"""
        return {
            "name": self.name,
            "firmware_type": self.firmware_type,
            "parameters": self.parameters,
            "aircraft_type": self.aircraft_type,
            "description": self.description,
            "created_date": self.created_date,
            "last_used": self.last_used,
            "last_modified": self.last_modified,
            "parameter_file_path": self.parameter_file_path,
            "is_default": self.is_default
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AircraftProfile':
        """Create profile from dictionary"""
        profile = cls(
            name=data.get("name", "Unknown"),
            firmware_type=data.get("firmware_type", "Unknown"),
            parameters=data.get("parameters", {}),
            aircraft_type=data.get("aircraft_type", "Unknown"),
            description=data.get("description", "")
        )
        profile.created_date = data.get("created_date", datetime.now().isoformat())
        profile.last_used = data.get("last_used", datetime.now().isoformat())
        profile.last_modified = data.get("last_modified", datetime.now().isoformat())
        profile.parameter_file_path = data.get("parameter_file_path")
        profile.is_default = data.get("is_default", False)
        return profile
    
    def update_parameters(self, new_parameters: Dict[str, float]):
        """Update profile parameters"""
        self.parameters = new_parameters.copy()
        self.last_modified = datetime.now().isoformat()
    
    def mark_used(self):
        """Mark profile as recently used"""
        self.last_used = datetime.now().isoformat()
    
    def get_aircraft_category(self) -> str:
        """Get aircraft category based on parameters"""
        if self.firmware_type == "ardupilot":
            if "Q_ENABLE" in self.parameters and self.parameters["Q_ENABLE"] > 0:
                return "VTOL"
            elif "ARSPD_FBW_MIN" in self.parameters:
                return "Fixed Wing"
            else:
                return "Multicopter"
        elif self.firmware_type == "px4":
            if "VT_TRANS_MIN_TM" in self.parameters:
                return "VTOL"
            elif "FW_AIRSPD_MIN" in self.parameters:
                return "Fixed Wing"
            else:
                return "Multicopter"
        return "Unknown"
    
    def get_key_parameters_summary(self) -> str:
        """Get summary of key parameters"""
        if not self.parameters:
            return "No parameters"
        
        summary = []
        
        # Add firmware-specific key parameters
        if self.firmware_type == "ardupilot":
            key_params = ["WPNAV_SPEED", "WPNAV_RADIUS", "PILOT_ALT_MAX", "RTL_ALT"]
        elif self.firmware_type == "px4":
            key_params = ["MC_XY_CRUISE", "NAV_MC_ALT_RAD", "RTL_RETURN_ALT", "FW_AIRSPD_MAX"]
        else:
            key_params = []
        
        for param in key_params:
            if param in self.parameters:
                summary.append(f"{param}: {self.parameters[param]}")
        
        return ", ".join(summary) if summary else "Standard parameters"


class AircraftProfileManager(QObject):
    """Manages saved aircraft profiles"""
    
    # Signals for profile changes
    profile_created = pyqtSignal(str)      # Emits profile name
    profile_updated = pyqtSignal(str)      # Emits profile name
    profile_deleted = pyqtSignal(str)      # Emits profile name
    profile_loaded = pyqtSignal(str)       # Emits profile name
    profiles_changed = pyqtSignal()        # General profiles change
    
    def __init__(self, profiles_file: str = "aircraft_profiles.json"):
        super().__init__()
        self.profiles_file = profiles_file
        self.profiles: Dict[str, AircraftProfile] = {}
        self.current_profile: Optional[AircraftProfile] = None
        self.load_profiles()
        self.create_default_profiles()
    
    def load_profiles(self):
        """Load aircraft profiles from file"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    
                    for profile_data in data.get("profiles", []):
                        profile = AircraftProfile.from_dict(profile_data)
                        self.profiles[profile.name] = profile
                        
                    # Set current profile if specified
                    current_profile_name = data.get("current_profile")
                    if current_profile_name and current_profile_name in self.profiles:
                        self.current_profile = self.profiles[current_profile_name]
                        
        except Exception as e:
            print(f"Error loading aircraft profiles: {e}")
            # Create empty profiles if loading fails
            self.profiles = {}
    
    def save_profiles(self):
        """Save aircraft profiles to file"""
        try:
            data = {
                "profiles": [profile.to_dict() for profile in self.profiles.values()],
                "current_profile": self.current_profile.name if self.current_profile else None,
                "last_saved": datetime.now().isoformat()
            }
            
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving aircraft profiles: {e}")
    
    def create_default_profiles(self):
        """Create default aircraft profiles if none exist"""
        if not self.profiles:
            # Create some common default profiles
            default_profiles = [
                {
                    "name": "Generic Multicopter (ArduPilot)",
                    "firmware_type": "ardupilot",
                    "aircraft_type": "Multicopter",
                    "description": "Standard multicopter configuration for ArduPilot",
                    "parameters": {
                        "WPNAV_SPEED": 5.0,
                        "WPNAV_ACCEL": 50.0,
                        "WPNAV_RADIUS": 2.0,
                        "PILOT_ALT_MAX": 100.0,
                        "RTL_ALT": 50.0,
                        "WPNAV_LOITER_RAD": 2.0
                    }
                },
                {
                    "name": "Generic Fixed Wing (ArduPilot)",
                    "firmware_type": "ardupilot",
                    "aircraft_type": "Fixed Wing",
                    "description": "Standard fixed wing configuration for ArduPilot",
                    "parameters": {
                        "WPNAV_SPEED": 15.0,
                        "WPNAV_ACCEL": 10.0,
                        "WPNAV_RADIUS": 50.0,
                        "PILOT_ALT_MAX": 200.0,
                        "RTL_ALT": 100.0,
                        "WPNAV_LOITER_RAD": 100.0,
                        "ARSPD_FBW_MIN": 8.0,
                        "ARSPD_FBW_MAX": 25.0
                    }
                },
                {
                    "name": "Generic Multicopter (PX4)",
                    "firmware_type": "px4",
                    "aircraft_type": "Multicopter",
                    "description": "Standard multicopter configuration for PX4",
                    "parameters": {
                        "MC_XY_CRUISE": 5.0,
                        "MC_XY_VEL_MAX": 8.0,
                        "NAV_MC_ALT_RAD": 2.0,
                        "RTL_RETURN_ALT": 50.0,
                        "RTL_DESCEND_ALT": 30.0
                    }
                },
                {
                    "name": "Generic Fixed Wing (PX4)",
                    "firmware_type": "px4",
                    "aircraft_type": "Fixed Wing",
                    "description": "Standard fixed wing configuration for PX4",
                    "parameters": {
                        "FW_AIRSPD_MAX": 25.0,
                        "FW_AIRSPD_MIN": 8.0,
                        "FW_AIRSPD_TRIM": 15.0,
                        "NAV_FW_ALT_RAD": 50.0,
                        "RTL_RETURN_ALT": 100.0,
                        "RTL_DESCEND_ALT": 50.0
                    }
                }
            ]
            
            for profile_data in default_profiles:
                profile = AircraftProfile(
                    name=profile_data["name"],
                    firmware_type=profile_data["firmware_type"],
                    parameters=profile_data["parameters"],
                    aircraft_type=profile_data["aircraft_type"],
                    description=profile_data["description"]
                )
                profile.is_default = True
                self.profiles[profile.name] = profile
            
            # Set first profile as current
            if self.profiles:
                first_profile_name = list(self.profiles.keys())[0]
                self.current_profile = self.profiles[first_profile_name]
            
            self.save_profiles()
    
    def create_profile(self, name: str, firmware_type: str, parameters: Dict[str, float],
                      aircraft_type: str = "Unknown", description: str = "") -> bool:
        """Create new aircraft profile"""
        try:
            if name in self.profiles:
                return False  # Profile already exists
            
            profile = AircraftProfile(
                name=name,
                firmware_type=firmware_type,
                parameters=parameters,
                aircraft_type=aircraft_type,
                description=description
            )
            
            self.profiles[name] = profile
            self.save_profiles()
            self.profile_created.emit(name)
            self.profiles_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error creating profile: {e}")
            return False
    
    def update_profile(self, name: str, **kwargs) -> bool:
        """Update existing aircraft profile"""
        try:
            if name not in self.profiles:
                return False
            
            profile = self.profiles[name]
            
            # Update specified fields
            for key, value in kwargs.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
            
            profile.last_modified = datetime.now().isoformat()
            self.save_profiles()
            self.profile_updated.emit(name)
            self.profiles_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """Delete aircraft profile"""
        try:
            if name not in self.profiles:
                return False
            
            # Don't allow deletion of default profiles
            if self.profiles[name].is_default:
                return False
            
            # Remove profile
            del self.profiles[name]
            
            # Update current profile if it was deleted
            if self.current_profile and self.current_profile.name == name:
                if self.profiles:
                    first_profile_name = list(self.profiles.keys())[0]
                    self.current_profile = self.profiles[first_profile_name]
                else:
                    self.current_profile = None
            
            self.save_profiles()
            self.profile_deleted.emit(name)
            self.profiles_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error deleting profile: {e}")
            return False
    
    def get_profile(self, name: str) -> Optional[AircraftProfile]:
        """Get aircraft profile by name"""
        return self.profiles.get(name)
    
    def get_current_profile(self) -> Optional[AircraftProfile]:
        """Get current aircraft profile"""
        return self.current_profile
    
    def set_current_profile(self, name: str) -> bool:
        """Set current aircraft profile"""
        if name in self.profiles:
            self.current_profile = self.profiles[name]
            self.current_profile.mark_used()
            self.save_profiles()
            self.profile_loaded.emit(name)
            return True
        return False
    
    def get_profile_names(self) -> List[str]:
        """Get list of all profile names"""
        return list(self.profiles.keys())
    
    def get_profiles_by_firmware(self, firmware_type: str) -> List[AircraftProfile]:
        """Get profiles filtered by firmware type"""
        return [profile for profile in self.profiles.values() 
                if profile.firmware_type == firmware_type]
    
    def get_profiles_by_aircraft_type(self, aircraft_type: str) -> List[AircraftProfile]:
        """Get profiles filtered by aircraft type"""
        return [profile for profile in self.profiles.values() 
                if profile.aircraft_type == aircraft_type]
    
    def import_profile_from_parameter_manager(self, param_manager: AircraftParameterManager,
                                            name: str, aircraft_type: str = "Unknown",
                                            description: str = "") -> bool:
        """Import profile from AircraftParameterManager"""
        try:
            if not param_manager.has_parameters():
                return False
            
            # Create profile from parameter manager
            profile = AircraftProfile(
                name=name,
                firmware_type=param_manager.current_firmware,
                parameters=param_manager.get_current_parameters(),
                aircraft_type=aircraft_type,
                description=description
            )
            profile.parameter_file_path = param_manager.param_file_path
            
            # Add to profiles
            self.profiles[name] = profile
            self.save_profiles()
            self.profile_created.emit(name)
            self.profiles_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error importing profile: {e}")
            return False
    
    def export_profile_to_parameter_manager(self, profile_name: str, 
                                          param_manager: AircraftParameterManager) -> bool:
        """Export profile to AircraftParameterManager"""
        try:
            if profile_name not in self.profiles:
                return False
            
            profile = self.profiles[profile_name]
            
            # Load parameters into parameter manager
            if profile.firmware_type == "ardupilot":
                param_manager.ardupilot_params = profile.parameters.copy()
                param_manager.current_firmware = "ardupilot"
            elif profile.firmware_type == "px4":
                param_manager.px4_params = profile.parameters.copy()
                param_manager.current_firmware = "px4"
            
            param_manager.param_file_path = profile.parameter_file_path
            param_manager.parameters_updated.emit()
            
            # Mark profile as used
            profile.mark_used()
            self.save_profiles()
            
            return True
            
        except Exception as e:
            print(f"Error exporting profile: {e}")
            return False
    
    def duplicate_profile(self, original_name: str, new_name: str) -> bool:
        """Duplicate existing profile with new name"""
        try:
            if original_name not in self.profiles or new_name in self.profiles:
                return False
            
            original_profile = self.profiles[original_name]
            
            # Create duplicate with new name
            duplicate_profile = AircraftProfile(
                name=new_name,
                firmware_type=original_profile.firmware_type,
                parameters=original_profile.parameters.copy(),
                aircraft_type=original_profile.aircraft_type,
                description=f"Copy of {original_profile.description}"
            )
            
            self.profiles[new_name] = duplicate_profile
            self.save_profiles()
            self.profile_created.emit(new_name)
            self.profiles_changed.emit()
            return True
            
        except Exception as e:
            print(f"Error duplicating profile: {e}")
            return False
    
    def get_profile_statistics(self) -> Dict:
        """Get statistics about profiles"""
        total_profiles = len(self.profiles)
        ardupilot_profiles = len(self.get_profiles_by_firmware("ardupilot"))
        px4_profiles = len(self.get_profiles_by_firmware("px4"))
        default_profiles = len([p for p in self.profiles.values() if p.is_default])
        custom_profiles = total_profiles - default_profiles
        
        return {
            "total_profiles": total_profiles,
            "ardupilot_profiles": ardupilot_profiles,
            "px4_profiles": px4_profiles,
            "default_profiles": default_profiles,
            "custom_profiles": custom_profiles,
            "current_profile": self.current_profile.name if self.current_profile else None
        }
