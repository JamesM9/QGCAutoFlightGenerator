#!/usr/bin/env python3
"""
Settings Manager for AutoFlightGenerator
Handles global settings like unit preferences, theme settings, and user preferences.
"""

import json
import os
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal


class UnitSystem(Enum):
    """Enumeration for unit systems"""
    METRIC = "metric"
    IMPERIAL = "imperial"


class GroundControlStation(Enum):
    """Enumeration for ground control stations"""
    QGROUNDCONTROL = "qgroundcontrol"
    MISSION_PLANNER = "mission_planner"


class SettingsManager(QObject):
    """Manages global application settings"""
    
    # Signals for when settings change
    units_changed = pyqtSignal(str)  # Emits new unit system
    theme_changed = pyqtSignal(str)  # Emits new theme
    gcs_changed = pyqtSignal(str)  # Emits new ground control station
    settings_updated = pyqtSignal()  # General settings update
    
    def __init__(self, settings_file="app_settings.json"):
        super().__init__()
        self.settings_file = settings_file
        self.settings = self.load_default_settings()
        self.load_settings()
    
    def load_default_settings(self):
        """Load default settings"""
        return {
            "units": UnitSystem.METRIC.value,
            "theme": "dark",
            "ground_control_station": GroundControlStation.QGROUNDCONTROL.value,
            "auto_save": True,
            "show_faa_maps": False,
            "show_faa_restrictions": False,
            "show_faa_notams": False,
            "show_laanc_grid": False,
            "show_startup_progress": False,  # Control startup progress dialog
            "recent_files": [],
            "default_altitude": 100,
            "default_interval": 50,
            "default_geofence_buffer": 100,
            "map_default_center": [40.615, -75.387],
            "map_default_zoom": 15
        }
    
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    file_settings = json.load(f)
                    # Update with file settings, keeping defaults for missing keys
                    for key, value in file_settings.items():
                        if key in self.settings:
                            self.settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_unit_system(self):
        """Get current unit system"""
        return self.settings.get("units", UnitSystem.METRIC.value)
    
    def set_unit_system(self, unit_system):
        """Set unit system and emit signal"""
        if unit_system in [UnitSystem.METRIC.value, UnitSystem.IMPERIAL.value]:
            self.settings["units"] = unit_system
            self.save_settings()
            self.units_changed.emit(unit_system)
            self.settings_updated.emit()
    
    def is_metric(self):
        """Check if using metric units"""
        return self.get_unit_system() == UnitSystem.METRIC.value
    
    def is_imperial(self):
        """Check if using imperial units"""
        return self.get_unit_system() == UnitSystem.IMPERIAL.value
    
    def get_altitude_units(self):
        """Get altitude units based on current system"""
        return "Meters" if self.is_metric() else "Feet"
    
    def get_distance_units(self):
        """Get distance units based on current system"""
        return "Meters" if self.is_metric() else "Feet"
    
    def get_default_altitude(self):
        """Get default altitude in current units"""
        default_meters = self.settings.get("default_altitude", 100)
        if self.is_imperial():
            return int(default_meters * 3.28084)  # Convert to feet
        return default_meters
    
    def get_default_interval(self):
        """Get default interval in current units"""
        default_meters = self.settings.get("default_interval", 50)
        if self.is_imperial():
            return int(default_meters * 3.28084)  # Convert to feet
        return default_meters
    
    def get_default_geofence_buffer(self):
        """Get default geofence buffer in current units"""
        default_meters = self.settings.get("default_geofence_buffer", 100)
        if self.is_imperial():
            return int(default_meters * 3.28084)  # Convert to feet
        return default_meters
    
    def convert_to_meters(self, value, from_units):
        """Convert value to meters"""
        if from_units.lower() in ["feet", "ft"]:
            return value * 0.3048
        return value
    
    def convert_from_meters(self, meters, to_units):
        """Convert meters to specified units"""
        if to_units.lower() in ["feet", "ft"]:
            return meters * 3.28084
        return meters
    
    def get_theme(self):
        """Get current theme"""
        return self.settings.get("theme", "dark")
    
    def set_theme(self, theme):
        """Set theme and emit signal"""
        self.settings["theme"] = theme
        self.save_settings()
        self.theme_changed.emit(theme)
        self.settings_updated.emit()
    
    def get_setting(self, key, default=None):
        """Get a specific setting"""
        return self.settings.get(key, default)
    
    def set_setting(self, key, value):
        """Set a specific setting"""
        self.settings[key] = value
        self.save_settings()
        self.settings_updated.emit()
    
    def get_show_startup_progress(self):
        """Get startup progress setting"""
        return self.settings.get("show_startup_progress", False)
    
    def set_show_startup_progress(self, show):
        """Set startup progress setting"""
        self.settings["show_startup_progress"] = show
        self.save_settings()
        self.settings_updated.emit()
    
    def get_ground_control_station(self):
        """Get current ground control station"""
        return self.settings.get("ground_control_station", GroundControlStation.QGROUNDCONTROL.value)
    
    def set_ground_control_station(self, gcs):
        """Set ground control station and emit signal"""
        if gcs in [GroundControlStation.QGROUNDCONTROL.value, GroundControlStation.MISSION_PLANNER.value]:
            self.settings["ground_control_station"] = gcs
            self.save_settings()
            self.gcs_changed.emit(gcs)
            self.settings_updated.emit()
    
    def is_qgroundcontrol(self):
        """Check if using QGroundControl"""
        return self.get_ground_control_station() == GroundControlStation.QGROUNDCONTROL.value
    
    def is_mission_planner(self):
        """Check if using Mission Planner"""
        return self.get_ground_control_station() == GroundControlStation.MISSION_PLANNER.value
    
    def get_file_extension(self):
        """Get file extension based on current GCS"""
        if self.is_qgroundcontrol():
            return ".plan"
        else:
            return ".waypoint"
    
    def get_file_filter(self):
        """Get file filter based on current GCS"""
        if self.is_qgroundcontrol():
            return "Plan Files (*.plan)"
        else:
            return "Waypoint Files (*.waypoint)"


# Global settings manager instance
settings_manager = SettingsManager() 