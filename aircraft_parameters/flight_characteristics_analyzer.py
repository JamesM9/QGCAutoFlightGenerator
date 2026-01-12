#!/usr/bin/env python3
"""
Flight Characteristics Analyzer
Analyzes aircraft parameters to extract flight characteristics for mission generation
"""

import math
from typing import Dict, List, Any, Optional


class FlightCharacteristicsAnalyzer:
    """Extracts flight characteristics from aircraft parameters"""
    
    def __init__(self):
        self.default_characteristics = {
            'max_speed': 15.0,
            'cruise_speed': 10.0,
            'max_climb_rate': 3.0,
            'max_descent_rate': 2.0,
            'waypoint_radius': 5.0,
            'turn_radius': 50.0,
            'altitude_limits': {'min_altitude': 10.0, 'max_altitude': 1000.0},
            'energy_characteristics': {'energy_management': 'Direct'}
        }
    
    def analyze_aircraft_performance(self, parameters: Dict[str, Any], aircraft_type: str) -> Dict[str, Any]:
        """Extract performance characteristics based on aircraft type"""
        
        characteristics = {
            'aircraft_type': aircraft_type,
            'max_speed': self._get_max_speed(parameters, aircraft_type),
            'cruise_speed': self._get_cruise_speed(parameters, aircraft_type),
            'max_climb_rate': self._get_max_climb_rate(parameters, aircraft_type),
            'max_descent_rate': self._get_max_descent_rate(parameters, aircraft_type),
            'waypoint_radius': self._get_waypoint_radius(parameters, aircraft_type),
            'turn_radius': self._get_turn_radius(parameters, aircraft_type),
            'altitude_limits': self._get_altitude_limits(parameters, aircraft_type),
            'energy_characteristics': self._get_energy_characteristics(parameters, aircraft_type)
        }
        
        return characteristics
    
    def _get_max_speed(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Extract maximum speed based on aircraft type"""
        if aircraft_type == 'VTOL':
            # VTOL: Use FW airspeed for forward flight, MPC for hover
            return params.get('FW_AIRSPD_MAX', 30.0)
        elif aircraft_type == 'FixedWing':
            return params.get('FW_AIRSPD_MAX', 30.0)
        elif aircraft_type == 'Multicopter':
            # Convert MPC velocity to equivalent airspeed
            return params.get('MPC_XY_VEL_MAX', 12.0) * 1.5  # Rough conversion
        return 15.0  # Default
    
    def _get_cruise_speed(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Extract optimal cruise speed"""
        if aircraft_type == 'VTOL':
            return params.get('FW_AIRSPD_TRIM', 15.0)
        elif aircraft_type == 'FixedWing':
            return params.get('FW_AIRSPD_TRIM', 20.0)
        elif aircraft_type == 'Multicopter':
            return params.get('MPC_XY_CRUISE', 5.0)
        return 10.0
    
    def _get_max_climb_rate(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Extract maximum climb rate"""
        if aircraft_type in ['VTOL', 'FixedWing']:
            return params.get('FW_T_CLMB_MAX', 5.0)
        elif aircraft_type == 'Multicopter':
            return params.get('MPC_Z_VEL_MAX_UP', 3.0)
        return 3.0
    
    def _get_max_descent_rate(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Extract maximum descent rate"""
        if aircraft_type in ['VTOL', 'FixedWing']:
            return params.get('FW_T_SINK_MAX', 8.0)
        elif aircraft_type == 'Multicopter':
            return params.get('MPC_Z_VEL_MAX_DN', 2.0)
        return 2.0
    
    def _get_waypoint_radius(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Extract waypoint acceptance radius"""
        if aircraft_type == 'Multicopter':
            return params.get('NAV_MC_ALT_RAD', 0.8)
        elif aircraft_type in ['VTOL', 'FixedWing']:
            return params.get('NAV_FW_ALT_RAD', 10.0)
        return 5.0
    
    def _get_turn_radius(self, params: Dict[str, Any], aircraft_type: str) -> float:
        """Calculate turn radius based on speed and control parameters"""
        cruise_speed = self._get_cruise_speed(params, aircraft_type)
        
        if aircraft_type == 'Multicopter':
            # Multicopter: Based on velocity and position control
            max_roll = params.get('MPC_MAN_TILT_MAX', 35.0)
            return (cruise_speed ** 2) / (9.81 * math.tan(math.radians(max_roll)))
        elif aircraft_type in ['VTOL', 'FixedWing']:
            # Fixed wing: Based on L1 navigation or roll limits
            max_roll = params.get('FW_R_LIM', 35.0)
            return (cruise_speed ** 2) / (9.81 * math.tan(math.radians(max_roll)))
        
        return 50.0  # Default turn radius
    
    def _get_altitude_limits(self, params: Dict[str, Any], aircraft_type: str) -> Dict[str, float]:
        """Extract altitude operation limits"""
        return {
            'min_altitude': params.get('MIS_TAKEOFF_ALT', 10.0),
            'max_altitude': params.get('GND_ALT_MAX', 1000.0),
            'landing_altitude': params.get('MPC_LAND_ALT1', 10.0)
        }
    
    def _get_energy_characteristics(self, params: Dict[str, Any], aircraft_type: str) -> Dict[str, Any]:
        """Extract energy management characteristics"""
        if aircraft_type in ['VTOL', 'FixedWing']:
            return {
                'energy_management': 'TECS',
                'climb_efficiency': params.get('FW_T_CLMB_MAX', 5.0) / params.get('FW_AIRSPD_TRIM', 15.0),
                'descent_efficiency': params.get('FW_T_SINK_MAX', 8.0) / params.get('FW_AIRSPD_TRIM', 15.0),
                'transition_energy': params.get('VT_F_TRANS_THR', 0.68) if aircraft_type == 'VTOL' else None
            }
        else:
            return {
                'energy_management': 'Direct',
                'hover_throttle': params.get('MPC_THR_HOVER', 0.5),
                'max_throttle': params.get('MPC_THR_MAX', 0.7)
            }
    
    def get_mission_optimization_settings(self, characteristics: Dict[str, Any]) -> Dict[str, Any]:
        """Get mission optimization settings based on aircraft characteristics"""
        aircraft_type = characteristics.get('aircraft_type', 'Unknown')
        
        settings = {
            'waypoint_spacing': self._calculate_optimal_waypoint_spacing(characteristics),
            'altitude_strategy': self._get_altitude_strategy(aircraft_type),
            'speed_profile': self._get_speed_profile(characteristics),
            'turn_strategy': self._get_turn_strategy(aircraft_type, characteristics),
            'energy_management': characteristics.get('energy_characteristics', {}).get('energy_management', 'Direct')
        }
        
        return settings
    
    def _calculate_optimal_waypoint_spacing(self, characteristics: Dict[str, Any]) -> float:
        """Calculate optimal waypoint spacing based on aircraft performance"""
        turn_radius = characteristics.get('turn_radius', 50.0)
        cruise_speed = characteristics.get('cruise_speed', 10.0)
        
        # Minimum spacing should be at least 2x turn radius or 2 seconds at cruise speed
        min_spacing = max(turn_radius * 2, cruise_speed * 2)
        
        # For precision missions, use tighter spacing
        if characteristics.get('aircraft_type') == 'Multicopter':
            return min(min_spacing, 20.0)  # Cap at 20m for multicopters
        else:
            return min_spacing
    
    def _get_altitude_strategy(self, aircraft_type: str) -> str:
        """Get altitude strategy based on aircraft type"""
        if aircraft_type == 'Multicopter':
            return 'precise'  # Precise altitude control
        elif aircraft_type in ['VTOL', 'FixedWing']:
            return 'energy_efficient'  # Consider energy management
        else:
            return 'standard'
    
    def _get_speed_profile(self, characteristics: Dict[str, Any]) -> Dict[str, float]:
        """Get speed profile for mission generation"""
        aircraft_type = characteristics.get('aircraft_type', 'Unknown')
        
        if aircraft_type == 'VTOL':
            return {
                'hover_speed': characteristics.get('hover_speed', 5.0),
                'transition_speed': characteristics.get('transition_airspeed', 16.0),
                'cruise_speed': characteristics.get('cruise_speed', 15.0)
            }
        else:
            return {
                'cruise_speed': characteristics.get('cruise_speed', 10.0),
                'max_speed': characteristics.get('max_speed', 15.0)
            }
    
    def _get_turn_strategy(self, aircraft_type: str, characteristics: Dict[str, Any]) -> str:
        """Get turn strategy based on aircraft type and characteristics"""
        if aircraft_type == 'Multicopter':
            return 'tight_turns'  # Can make tight turns
        elif aircraft_type in ['VTOL', 'FixedWing']:
            turn_radius = characteristics.get('turn_radius', 50.0)
            if turn_radius > 100:
                return 'wide_turns'  # Large turn radius
            else:
                return 'moderate_turns'
        else:
            return 'standard_turns'
    
    def validate_mission_parameters(self, mission_params: Dict[str, Any], 
                                  characteristics: Dict[str, Any]) -> List[str]:
        """Validate mission parameters against aircraft characteristics"""
        warnings = []
        
        # Check speed limits
        if mission_params.get('cruise_speed', 0) > characteristics.get('max_speed', 0):
            warnings.append(f"Cruise speed exceeds aircraft maximum speed")
        
        # Check climb/descent rates
        if mission_params.get('climb_rate', 0) > characteristics.get('max_climb_rate', 0):
            warnings.append(f"Climb rate exceeds aircraft maximum climb rate")
        
        if mission_params.get('descent_rate', 0) > characteristics.get('max_descent_rate', 0):
            warnings.append(f"Descent rate exceeds aircraft maximum descent rate")
        
        # Check altitude limits
        altitude_limits = characteristics.get('altitude_limits', {})
        if mission_params.get('altitude', 0) < altitude_limits.get('min_altitude', 0):
            warnings.append(f"Mission altitude below aircraft minimum altitude")
        
        if mission_params.get('altitude', 0) > altitude_limits.get('max_altitude', 1000):
            warnings.append(f"Mission altitude above aircraft maximum altitude")
        
        return warnings
