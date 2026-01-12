#!/usr/bin/env python3
"""
Plan Visualizer Module for AutoFlightGenerator
Implements the visualization methods from MapsolutionLocal for .plan file display
"""

import json
import os
import math
from typing import Dict, List, Optional, Any


class PlanVisualizer:
    """Unified plan file visualization for flight planning tools using MapsolutionLocal methods"""
    
    def __init__(self, map_view):
        """
        Initialize the plan visualizer
        
        Args:
            map_view: QWebEngineView instance for the map
        """
        self.map_view = map_view
        self.current_plan_data = None
        self.current_waypoints = []
        self.current_geofence_polygons = []
        self.current_rally_points = []
    
    def parse_plan_file(self, plan_data: Dict) -> Dict:
        """
        Parse .plan file and extract visualization data using MapsolutionLocal methods
        
        Args:
            plan_data: Raw plan file data as dictionary
            
        Returns:
            Dict containing parsed waypoints, geofence, and rally points
        """
        waypoints = []
        geofence_polygons = []
        rally_points = []
        
        # Parse mission items - using MapsolutionLocal extraction method
        if 'mission' in plan_data and 'items' in plan_data['mission']:
            for i, item in enumerate(plan_data['mission']['items']):
                waypoint = self.extract_waypoint_from_item(item, i)
                if waypoint:
                    waypoints.append(waypoint)
        
        # Parse geofence - using MapsolutionLocal method
        if 'geoFence' in plan_data:
            geofence_polygons = self.parse_geofence(plan_data['geoFence'])
        
        # Parse rally points - using MapsolutionLocal method
        if 'rallyPoints' in plan_data and 'points' in plan_data['rallyPoints']:
            for point in plan_data['rallyPoints']['points']:
                if 'coordinate' in point and len(point['coordinate']) >= 2:
                    rally_points.append({
                        'lat': point['coordinate'][0],
                        'lng': point['coordinate'][1],
                        'alt': point['coordinate'][2] if len(point['coordinate']) > 2 else 0,
                        'id': point.get('id', 'Unknown')
                    })
        
        # Store current data
        self.current_waypoints = waypoints
        self.current_geofence_polygons = geofence_polygons
        self.current_rally_points = rally_points
        
        return {
            'waypoints': waypoints,
            'geofence': geofence_polygons,
            'rally_points': rally_points,
            'mission_info': self.extract_mission_info(plan_data)
        }
    
    def extract_waypoint_from_item(self, item: Dict, index: int) -> Optional[Dict]:
        """
        Extract waypoint data from a mission item using MapsolutionLocal method
        
        Args:
            item: Mission item dictionary
            index: Waypoint index
            
        Returns:
            Waypoint dictionary or None if invalid
        """
        # Check for coordinates in params array (QGC format: [0, 0, 0, null, lat, lon, alt])
        if 'params' in item and len(item['params']) >= 6:
            lat = item['params'][4]
            lng = item['params'][5]
            alt = item['params'][6] if len(item['params']) > 6 else 0
            
            if (isinstance(lat, (int, float)) and isinstance(lng, (int, float)) and 
                not math.isnan(lat) and not math.isnan(lng) and lat is not None and lng is not None):
                
                return {
                    'index': index,
                    'lat': lat,
                    'lng': lng,
                    'alt': alt,
                    'command': item.get('command', 'Unknown'),
                    'command_name': self.get_command_name(item.get('command', 0)),
                    'frame': item.get('frame', 'Unknown'),
                    'altitude_mode': item.get('AltitudeMode', 'Unknown'),
                    'amsl_alt': item.get('AMSLAltAboveTerrain', 'N/A'),
                    'auto_continue': item.get('autoContinue', False)
                }
        
        # Alternative format: coordinate array
        elif 'coordinate' in item and len(item['coordinate']) >= 2:
            lat = item['coordinate'][0]
            lng = item['coordinate'][1]
            alt = item['coordinate'][2] if len(item['coordinate']) > 2 else 0
            
            if (isinstance(lat, (int, float)) and isinstance(lng, (int, float)) and 
                not math.isnan(lat) and not math.isnan(lng)):
                
                return {
                    'index': index,
                    'lat': lat,
                    'lng': lng,
                    'alt': alt,
                    'command': item.get('command', 'Unknown'),
                    'command_name': self.get_command_name(item.get('command', 0)),
                    'frame': item.get('frame', 'Unknown'),
                    'altitude_mode': item.get('AltitudeMode', 'Unknown'),
                    'amsl_alt': item.get('AMSLAltAboveTerrain', 'N/A'),
                    'auto_continue': item.get('autoContinue', False)
                }
        
        return None
    
    def parse_geofence(self, geo_fence_data: Dict) -> List:
        """
        Parse geofence data from the plan file using MapsolutionLocal method
        
        Args:
            geo_fence_data: Geofence data dictionary
            
        Returns:
            List of geofence polygons
        """
        geofence_polygons = []
        
        # Handle different geofence formats
        if 'polygon' in geo_fence_data and isinstance(geo_fence_data['polygon'], list):
            # Old format: direct polygon array
            geofence_polygons.append(geo_fence_data['polygon'])
        elif 'polygons' in geo_fence_data and isinstance(geo_fence_data['polygons'], list):
            # New format: array of polygon objects
            for polygon_obj in geo_fence_data['polygons']:
                if 'polygon' in polygon_obj:
                    geofence_polygons.append(polygon_obj['polygon'])
        
        return geofence_polygons
    
    def get_command_name(self, command: int) -> str:
        """
        Get human-readable name for MAVLink command using MapsolutionLocal method
        
        Args:
            command: MAVLink command number
            
        Returns:
            Human-readable command name
        """
        commands = {
            16: 'MAV_CMD_NAV_WAYPOINT',
            17: 'MAV_CMD_NAV_LOITER_UNLIM',
            18: 'MAV_CMD_NAV_LOITER_TURNS',
            19: 'MAV_CMD_NAV_LOITER_TIME',
            20: 'MAV_CMD_NAV_RETURN_TO_LAUNCH',
            21: 'MAV_CMD_NAV_LAND',
            22: 'MAV_CMD_NAV_TAKEOFF',
            82: 'MAV_CMD_NAV_SPLINE_WAYPOINT',
            84: 'MAV_CMD_NAV_VTOL_TAKEOFF',
            85: 'MAV_CMD_NAV_VTOL_LAND',
            86: 'MAV_CMD_NAV_GUIDED_ENABLE',
            89: 'MAV_CMD_NAV_DELAY',
            90: 'MAV_CMD_NAV_CHANGE_ALT',
            91: 'MAV_CMD_NAV_LOITER_TO_ALT',
            92: 'MAV_CMD_NAV_DO_FOLLOW',
            93: 'MAV_CMD_NAV_DO_FOLLOW_REPOSITION',
            94: 'MAV_CMD_NAV_ROI',
            95: 'MAV_CMD_NAV_PATHPLANNING',
            96: 'MAV_CMD_NAV_SPLINE_WAYPOINT',
            101: 'MAV_CMD_NAV_FENCE_RETURN_POINT',
            102: 'MAV_CMD_NAV_FENCE_POLYGON_VERTEX_INCLUSION',
            103: 'MAV_CMD_NAV_FENCE_POLYGON_VERTEX_EXCLUSION',
            104: 'MAV_CMD_NAV_FENCE_CIRCLE_INCLUSION',
            105: 'MAV_CMD_NAV_FENCE_CIRCLE_EXCLUSION',
            106: 'MAV_CMD_NAV_RALLY_POINT',
            211: 'MAV_CMD_DO_GRIPPER'
        }
        return commands.get(command, f'Unknown Command ({command})')
    
    def extract_mission_info(self, plan_data: Dict) -> Dict:
        """
        Extract mission information from plan data
        
        Args:
            plan_data: Raw plan file data
            
        Returns:
            Mission information dictionary
        """
        info = {}
        
        if 'mission' in plan_data:
            mission = plan_data['mission']
            if 'cruiseSpeed' in mission:
                info['cruise_speed'] = mission['cruiseSpeed']
            if 'hoverSpeed' in mission:
                info['hover_speed'] = mission['hoverSpeed']
            if 'vehicleType' in mission:
                vehicle_types = {1: 'Fixed Wing', 2: 'Multicopter', 3: 'Rover', 4: 'Submarine'}
                info['vehicle_type'] = vehicle_types.get(mission['vehicleType'], 'Unknown')
        
        info['ground_station'] = plan_data.get('groundStation', 'Unknown')
        info['version'] = plan_data.get('version', 'Unknown')
        info['waypoint_count'] = len(self.current_waypoints)
        info['geofence_count'] = len(self.current_geofence_polygons)
        info['rally_point_count'] = len(self.current_rally_points)
        
        return info
    
    def visualize_plan_on_map(self, plan_data: Dict):
        """
        Visualize parsed plan data on the map using MapsolutionLocal JavaScript method
        
        Args:
            plan_data: Parsed plan data dictionary
        """
        self.current_plan_data = plan_data
        
        # Prepare JavaScript data in MapsolutionLocal format
        js_data = {
            'waypoints': plan_data['waypoints'],
            'geofence': plan_data['geofence'],
            'rally_points': plan_data['rally_points']
        }
        
        # Convert to JSON and inject into map using MapsolutionLocal method
        mission_json = json.dumps(js_data)
        js_code = f"updateMissionData({mission_json});"
        
        # Execute JavaScript in the web view
        self.map_view.page().runJavaScript(js_code)
    
    def auto_visualize_after_generation(self, plan_file_path: str) -> bool:
        """
        Automatically visualize plan file after generation
        
        Args:
            plan_file_path: Path to the generated plan file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(plan_file_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            # Parse and visualize
            parsed_data = self.parse_plan_file(plan_data)
            self.visualize_plan_on_map(parsed_data)
            
            return True
        except Exception as e:
            print(f"Error auto-visualizing plan: {e}")
            return False
    
    def clear_visualization(self):
        """Clear current plan visualization from the map"""
        js_code = """
        // Clear existing markers
        if (window.qgcMarkers) {
            window.qgcMarkers.forEach(marker => map.removeLayer(marker));
            window.qgcMarkers = [];
        }
        
        // Clear path
        if (window.qgcPath) {
            map.removeLayer(window.qgcPath);
            window.qgcPath = null;
        }
        
        // Clear geofence
        if (window.qgcGeofence) {
            map.removeLayer(window.qgcGeofence);
            window.qgcGeofence = null;
        }
        """
        self.map_view.page().runJavaScript(js_code)
    
    def get_visualization_stats(self) -> Dict:
        """
        Get statistics about current visualization
        
        Returns:
            Dictionary with visualization statistics
        """
        return {
            'waypoints': len(self.current_waypoints),
            'geofence_polygons': len(self.current_geofence_polygons),
            'rally_points': len(self.current_rally_points),
            'has_plan_data': self.current_plan_data is not None
        }
