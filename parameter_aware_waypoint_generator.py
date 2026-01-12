#!/usr/bin/env python3
"""
Parameter-Aware Waypoint Generator for AutoFlightGenerator
Generates waypoints based on aircraft parameters for optimal mission planning
"""

import math
from typing import Dict, List, Tuple, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from aircraft_parameter_manager import AircraftParameterManager


class ParameterAwareWaypointGenerator(QObject):
    """Generates waypoints based on aircraft parameters"""
    
    # Signals for generation progress
    waypoint_generated = pyqtSignal(int, float, float, float)  # index, lat, lon, alt
    generation_complete = pyqtSignal(list)  # Emits list of waypoints
    generation_error = pyqtSignal(str)      # Emits error message
    
    def __init__(self, param_manager: AircraftParameterManager):
        super().__init__()
        self.param_manager = param_manager
        
        # Default values for when parameters are not available
        self.default_values = {
            "waypoint_radius": 2.0,
            "cruise_speed": 5.0,
            "hover_speed": 2.0,
            "max_climb_rate": 2.0,
            "max_descent_rate": 2.0,
            "min_altitude": 10.0,
            "max_altitude": 100.0,
            "waypoint_spacing": 50.0
        }
    
    def calculate_waypoint_spacing(self, mission_type: str, terrain_complexity: str = "medium") -> float:
        """Calculate optimal waypoint spacing based on aircraft performance"""
        try:
            # Get aircraft parameters
            waypoint_radius = self.param_manager.get_waypoint_radius()
            cruise_speed = self.param_manager.get_cruise_speed()
            
            # Base spacing on waypoint radius and cruise speed
            base_spacing = max(waypoint_radius * 3, cruise_speed * 2)
            
            # Adjust for mission type
            mission_multipliers = {
                "delivery": 1.0,
                "mapping": 0.7,      # Closer spacing for mapping
                "inspection": 0.8,    # Closer spacing for inspection
                "security": 1.2,      # Wider spacing for security patrols
                "linear": 0.9,        # Slightly closer for linear routes
                "tower": 0.6          # Very close spacing for tower inspection
            }
            
            multiplier = mission_multipliers.get(mission_type.lower(), 1.0)
            base_spacing *= multiplier
            
            # Adjust for terrain complexity
            terrain_multipliers = {
                "low": 1.2,      # Wider spacing for simple terrain
                "medium": 1.0,   # Standard spacing
                "high": 0.8      # Closer spacing for complex terrain
            }
            
            terrain_mult = terrain_multipliers.get(terrain_complexity.lower(), 1.0)
            base_spacing *= terrain_mult
            
            # Ensure minimum and maximum spacing
            min_spacing = max(waypoint_radius * 2, 10.0)
            max_spacing = min(cruise_speed * 10, 200.0)
            
            return max(min_spacing, min(base_spacing, max_spacing))
            
        except Exception as e:
            print(f"Error calculating waypoint spacing: {e}")
            return self.default_values["waypoint_spacing"]
    
    def adjust_altitude_profile(self, waypoints: List[Tuple[float, float]], 
                               terrain_data: Optional[List[float]] = None,
                               mission_type: str = "delivery") -> List[Tuple[float, float, float]]:
        """Adjust altitude based on aircraft climb/descent rates and terrain"""
        try:
            if not waypoints:
                return []
            
            # Get aircraft parameters
            max_climb_rate = self.param_manager.get_max_climb_rate()
            max_descent_rate = self.param_manager.get_max_descent_rate()
            min_altitude = self.default_values["min_altitude"]
            max_altitude = self.default_values["max_altitude"]
            
            # Override with actual parameters if available
            if self.param_manager.current_firmware == "ardupilot":
                if "PILOT_ALT_MAX" in self.param_manager.ardupilot_params:
                    max_altitude = self.param_manager.ardupilot_params["PILOT_ALT_MAX"]
                if "PILOT_ALT_MIN" in self.param_manager.ardupilot_params:
                    min_altitude = self.param_manager.ardup_point_params["PILOT_ALT_MIN"]
            elif self.param_manager.current_firmware == "px4":
                if "RTL_RETURN_ALT" in self.param_manager.px4_params:
                    max_altitude = self.param_manager.px4_params["RTL_RETURN_ALT"]
            
            # Mission-specific altitude adjustments
            mission_altitudes = {
                "delivery": {"base": 50.0, "min": 30.0},
                "mapping": {"base": 80.0, "min": 50.0},
                "inspection": {"base": 40.0, "min": 20.0},
                "security": {"base": 60.0, "min": 40.0},
                "linear": {"base": 70.0, "min": 40.0},
                "tower": {"base": 30.0, "min": 15.0}
            }
            
            mission_alt = mission_altitudes.get(mission_type.lower(), {"base": 50.0, "min": 30.0})
            base_altitude = mission_alt["base"]
            min_mission_alt = mission_alt["min"]
            
            # Calculate altitudes with terrain following
            altitudes = []
            current_altitude = base_altitude
            
            for i, (lat, lon) in enumerate(waypoints):
                # Get terrain elevation if available
                terrain_elevation = 0.0
                if terrain_data and i < len(terrain_data):
                    terrain_elevation = terrain_data[i]
                
                # Calculate target altitude above terrain
                target_altitude = max(base_altitude, terrain_elevation + min_mission_alt)
                
                # Limit to aircraft capabilities
                target_altitude = max(min_altitude, min(target_altitude, max_altitude))
                
                # Calculate achievable altitude based on climb/descent rates
                if i > 0:
                    prev_alt = altitudes[-1][2]
                    distance = self._calculate_distance(
                        (lat, lon), 
                        (waypoints[i-1][0], waypoints[i-1][1])
                    )
                    
                    # Calculate maximum altitude change possible
                    max_alt_change = (distance / cruise_speed) * max_climb_rate
                    
                    if target_altitude > prev_alt:
                        # Climbing
                        achievable_alt = min(target_altitude, prev_alt + max_alt_change)
                    else:
                        # Descending
                        achievable_alt = max(target_altitude, prev_alt - max_alt_change)
                    
                    current_altitude = achievable_alt
                else:
                    current_altitude = target_altitude
                
                # Add waypoint with calculated altitude
                altitudes.append((lat, lon, current_altitude))
                
                # Emit progress
                self.waypoint_generated.emit(i, lat, lon, current_altitude)
            
            return altitudes
            
        except Exception as e:
            print(f"Error adjusting altitude profile: {e}")
            # Fallback to simple altitude assignment
            return [(lat, lon, self.default_values["min_altitude"]) for lat, lon in waypoints]
    
    def optimize_waypoint_sequence(self, waypoints: List[Tuple[float, float, float]], 
                                 mission_type: str = "delivery") -> List[Tuple[float, float, float]]:
        """Optimize waypoint sequence based on aircraft performance"""
        try:
            if len(waypoints) <= 2:
                return waypoints
            
            # Get aircraft parameters
            waypoint_radius = self.param_manager.get_waypoint_radius()
            cruise_speed = self.param_manager.get_cruise_speed()
            
            # Mission-specific optimization strategies
            if mission_type.lower() == "mapping":
                # For mapping, maintain grid pattern
                return waypoints
            elif mission_type.lower() == "tower":
                # For tower inspection, maintain orbital pattern
                return waypoints
            elif mission_type.lower() == "linear":
                # For linear routes, maintain sequence
                return waypoints
            else:
                # For other missions, apply TSP-like optimization
                return self._apply_tsp_optimization(waypoints, waypoint_radius, cruise_speed)
                
        except Exception as e:
            print(f"Error optimizing waypoint sequence: {e}")
            return waypoints
    
    def generate_mission_commands(self, waypoints: List[Tuple[float, float, float]], 
                                mission_type: str = "delivery") -> List[Dict]:
        """Generate mission commands based on aircraft parameters"""
        try:
            if not waypoints:
                return []
            
            # Get aircraft parameters
            waypoint_radius = self.param_manager.get_waypoint_radius()
            cruise_speed = self.param_manager.get_cruise_speed()
            vehicle_type = self.param_manager.get_vehicle_type()
            firmware_type = self.param_manager.get_firmware_type()
            
            mission_items = []
            
            # Add takeoff command
            start_lat, start_lon, start_alt = waypoints[0]
            takeoff_command = self._create_takeoff_command(
                start_lat, start_lon, start_alt, vehicle_type, firmware_type
            )
            mission_items.append(takeoff_command)
            
            # Add waypoint commands
            for i, (lat, lon, alt) in enumerate(waypoints[1:], 1):
                waypoint_command = self._create_waypoint_command(
                    i, lat, lon, alt, waypoint_radius, cruise_speed, firmware_type
                )
                mission_items.append(waypoint_command)
            
            # Add landing command
            end_lat, end_lon, end_alt = waypoints[-1]
            landing_command = self._create_landing_command(
                end_lat, end_lon, end_alt, vehicle_type, firmware_type
            )
            mission_items.append(landing_command)
            
            return mission_items
            
        except Exception as e:
            print(f"Error generating mission commands: {e}")
            self.generation_error.emit(str(e))
            return []
    
    def _create_takeoff_command(self, lat: float, lon: float, alt: float, 
                               vehicle_type: int, firmware_type: int) -> Dict:
        """Create takeoff command based on vehicle type"""
        if vehicle_type == 1:  # Fixed Wing
            return {
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, lat, lon, alt],  # 15 m/s pitch
                "type": "SimpleItem",
                "autoContinue": True
            }
        elif vehicle_type == 3:  # VTOL
            return {
                "command": 84,  # VTOL_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, alt],
                "type": "SimpleItem",
                "autoContinue": True
            }
        else:  # Multicopter
            return {
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, alt],
                "type": "SimpleItem",
                "autoContinue": True
            }
    
    def _create_waypoint_command(self, index: int, lat: float, lon: float, alt: float,
                                waypoint_radius: float, cruise_speed: float, 
                                firmware_type: int) -> Dict:
        """Create waypoint command with aircraft-specific parameters"""
        return {
            "command": 16,  # WAYPOINT
            "doJumpId": index + 1,
            "frame": 0,  # Absolute altitude frame
            "params": [0, 0, 0, None, lat, lon, alt],
            "type": "SimpleItem",
            "autoContinue": True,
            "AMSLAltAboveTerrain": alt,
            "Altitude": alt,
            "AltitudeMode": 3,
            "waypoint_radius": waypoint_radius,
            "cruise_speed": cruise_speed
        }
    
    def _create_landing_command(self, lat: float, lon: float, alt: float,
                               vehicle_type: int, firmware_type: int) -> Dict:
        """Create landing command based on vehicle type"""
        if vehicle_type == 1:  # Fixed Wing
            return {
                "command": 21,  # LAND
                "doJumpId": 999,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, alt],
                "type": "SimpleItem",
                "autoContinue": True
            }
        elif vehicle_type == 3:  # VTOL
            return {
                "command": 85,  # VTOL_LAND
                "doJumpId": 999,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, alt],
                "type": "SimpleItem",
                "autoContinue": True
            }
        else:  # Multicopter
            return {
                "command": 21,  # LAND
                "doJumpId": 999,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, alt],
                "type": "SimpleItem",
                "autoContinue": True
            }
    
    def _apply_tsp_optimization(self, waypoints: List[Tuple[float, float, float]], 
                               waypoint_radius: float, cruise_speed: float) -> List[Tuple[float, float, float]]:
        """Apply Traveling Salesman Problem optimization to waypoints"""
        try:
            if len(waypoints) <= 3:
                return waypoints
            
            # Simple nearest neighbor optimization
            optimized = [waypoints[0]]  # Start with first waypoint
            remaining = waypoints[1:]
            
            while remaining:
                current = optimized[-1]
                nearest_idx = 0
                min_distance = float('inf')
                
                # Find nearest remaining waypoint
                for i, waypoint in enumerate(remaining):
                    distance = self._calculate_distance(
                        (current[0], current[1]), 
                        (waypoint[0], waypoint[1])
                    )
                    if distance < min_distance:
                        min_distance = distance
                        nearest_idx = i
                
                # Add nearest waypoint to optimized sequence
                optimized.append(remaining[nearest_idx])
                remaining.pop(nearest_idx)
            
            return optimized
            
        except Exception as e:
            print(f"Error applying TSP optimization: {e}")
            return waypoints
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """Calculate distance between two points using Haversine formula"""
        try:
            lat1, lon1 = math.radians(point1[0]), math.radians(point1[1])
            lat2, lon2 = math.radians(point2[0]), math.radians(point2[1])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = (math.sin(dlat/2)**2 + 
                 math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
            c = 2 * math.asin(math.sqrt(a))
            
            # Earth's radius in meters
            R = 6371000
            return R * c
            
        except Exception as e:
            print(f"Error calculating distance: {e}")
            return 0.0
    
    def get_mission_characteristics(self, waypoints: List[Tuple[float, float, float]], 
                                  mission_type: str = "delivery") -> Dict:
        """Get mission characteristics based on aircraft parameters"""
        try:
            if not waypoints:
                return {}
            
            # Get aircraft parameters
            cruise_speed = self.param_manager.get_cruise_speed()
            waypoint_radius = self.param_manager.get_waypoint_radius()
            
            # Calculate total distance
            total_distance = 0.0
            for i in range(1, len(waypoints)):
                distance = self._calculate_distance(
                    (waypoints[i-1][0], waypoints[i-1][1]),
                    (waypoints[i][0], waypoints[i][1])
                )
                total_distance += distance
            
            # Calculate estimated duration
            estimated_duration = total_distance / cruise_speed if cruise_speed > 0 else 0
            
            # Calculate altitude statistics
            altitudes = [wp[2] for wp in waypoints if len(wp) > 2]
            min_alt = min(altitudes) if altitudes else 0
            max_alt = max(altitudes) if altitudes else 0
            avg_alt = sum(altitudes) / len(altitudes) if altitudes else 0
            
            # Calculate waypoint density
            waypoint_density = len(waypoints) / (total_distance / 1000) if total_distance > 0 else 0
            
            return {
                "total_waypoints": len(waypoints),
                "total_distance_m": total_distance,
                "total_distance_km": total_distance / 1000,
                "estimated_duration_s": estimated_duration,
                "estimated_duration_min": estimated_duration / 60,
                "min_altitude": min_alt,
                "max_altitude": max_alt,
                "average_altitude": avg_alt,
                "waypoint_density": waypoint_density,
                "cruise_speed": cruise_speed,
                "waypoint_radius": waypoint_radius,
                "mission_type": mission_type
            }
            
        except Exception as e:
            print(f"Error calculating mission characteristics: {e}")
            return {}
    
    def validate_mission_parameters(self, waypoints: List[Tuple[float, float, float]], 
                                  mission_type: str = "delivery") -> Tuple[List[str], List[str]]:
        """Validate mission parameters against aircraft capabilities"""
        warnings = []
        errors = []
        
        try:
            if not waypoints:
                errors.append("No waypoints provided")
                return warnings, errors
            
            # Get aircraft parameters
            max_altitude = self.param_manager.get_current_parameters().get("PILOT_ALT_MAX", 100.0)
            max_speed = self.param_manager.get_current_parameters().get("WPNAV_SPEED", 5.0)
            
            # Check altitude limits
            altitudes = [wp[2] for wp in waypoints if len(wp) > 2]
            if altitudes:
                max_mission_alt = max(altitudes)
                if max_mission_alt > max_altitude:
                    errors.append(f"Mission altitude ({max_mission_alt}m) exceeds aircraft limit ({max_altitude}m)")
                elif max_mission_alt > max_altitude * 0.8:
                    warnings.append(f"Mission altitude ({max_mission_alt}m) is close to aircraft limit ({max_altitude}m)")
            
            # Check waypoint density
            if len(waypoints) > 100:
                warnings.append("Large number of waypoints may impact mission reliability")
            
            # Check distance limits (basic validation)
            total_distance = 0.0
            for i in range(1, len(waypoints)):
                distance = self._calculate_distance(
                    (waypoints[i-1][0], waypoints[i-1][1]),
                    (waypoints[i][0], waypoints[i][1])
                )
                total_distance += distance
            
            if total_distance > 50000:  # 50km
                warnings.append("Long mission distance may require additional planning considerations")
            
            return warnings, errors
            
        except Exception as e:
            errors.append(f"Error validating mission parameters: {str(e)}")
            return warnings, errors
