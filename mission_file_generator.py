#!/usr/bin/env python3
"""
Mission File Generator for AutoFlightGenerator
Handles generation of mission files for different ground control stations.
"""

import json
from settings_manager import GroundControlStation


class MissionFileGenerator:
    """Generates mission files for different ground control stations"""
    
    def __init__(self, gcs_type):
        """
        Initialize the file generator
        
        Args:
            gcs_type (str): Ground control station type ('qgroundcontrol' or 'mission_planner')
        """
        self.gcs_type = gcs_type
    
    def generate_file(self, mission_data, filename):
        """
        Generate mission file based on the selected ground control station
        
        Args:
            mission_data (dict): Mission data structure
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.gcs_type == GroundControlStation.QGROUNDCONTROL.value:
                return self.generate_plan_file(mission_data, filename)
            elif self.gcs_type == GroundControlStation.MISSION_PLANNER.value:
                return self.generate_waypoint_file(mission_data, filename)
            else:
                raise ValueError(f"Unsupported ground control station: {self.gcs_type}")
        except Exception as e:
            print(f"Error generating mission file: {e}")
            return False
    
    def generate_plan_file(self, mission_data, filename):
        """
        Generate QGroundControl .plan file (JSON format)
        
        Args:
            mission_data (dict): Mission data structure
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                json.dump(mission_data, f, indent=4)
            return True
        except Exception as e:
            print(f"Error writing .plan file: {e}")
            return False
    
    def generate_waypoint_file(self, mission_data, filename):
        """
        Generate Mission Planner .waypoint file (MAVLink format)
        
        Args:
            mission_data (dict): Mission data structure
            filename (str): Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filename, 'w') as f:
                # Write MAVLink waypoint header
                f.write("QGC WPL 110\n")
                
                # Extract mission items
                mission_items = mission_data.get('mission', {}).get('items', [])
                
                for item in mission_items:
                    # Extract waypoint data
                    seq = item.get('doJumpId', 0)
                    frame = item.get('frame', 3)  # MAV_FRAME_GLOBAL_RELATIVE_ALT
                    command = item.get('command', 16)  # MAV_CMD_NAV_WAYPOINT
                    params = item.get('params', [0, 0, 0, 0, 0, 0, 0])
                    
                    # Ensure we have enough parameters
                    while len(params) < 7:
                        params.append(0)
                    
                    # Write waypoint line
                    f.write(f"{seq}\t{frame}\t{command}\t"
                           f"{params[0]}\t{params[1]}\t{params[2]}\t{params[3]}\t"
                           f"{params[4]}\t{params[5]}\t{params[6]}\t1\n")
            
            return True
        except Exception as e:
            print(f"Error writing .waypoint file: {e}")
            return False
    
    def get_file_extension(self):
        """Get the appropriate file extension for the current GCS"""
        if self.gcs_type == GroundControlStation.QGROUNDCONTROL.value:
            return ".plan"
        elif self.gcs_type == GroundControlStation.MISSION_PLANNER.value:
            return ".waypoint"
        else:
            return ".plan"  # Default fallback
    
    def get_file_filter(self):
        """Get the appropriate file filter for the current GCS"""
        if self.gcs_type == GroundControlStation.QGROUNDCONTROL.value:
            return "Plan Files (*.plan)"
        elif self.gcs_type == GroundControlStation.MISSION_PLANNER.value:
            return "Waypoint Files (*.waypoint)"
        else:
            return "Plan Files (*.plan)"  # Default fallback


def create_file_generator(gcs_type):
    """
    Factory function to create a file generator for the specified GCS
    
    Args:
        gcs_type (str): Ground control station type
        
    Returns:
        MissionFileGenerator: Configured file generator
    """
    return MissionFileGenerator(gcs_type)
