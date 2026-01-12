#!/usr/bin/env python3
"""
FAA UAS Facility Maps Integration
Provides FAA airspace data and mapping functionality for drone flight planning
"""

import json
import requests
import time
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal
from settings_manager import settings_manager


class FAAMapsIntegration(QObject):
    """Main class for FAA UAS Facility Maps integration"""
    
    # Signals for map updates
    airspace_data_updated = pyqtSignal(dict)
    restrictions_updated = pyqtSignal(list)
    notams_updated = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        # FAA API endpoints
        self.faa_api_base = "https://external-api.faa.gov"
        self.uas_facility_maps_url = f"{self.faa_api_base}/faaapi/v1/uasfacilitymaps"
        self.airspace_api_url = "https://api.airmap.com/airspace/v2/status"
        
        # Cache for airspace data
        self.airspace_cache = {}
        self.cache_timeout = 300  # 5 minutes
        
    def get_faa_airspace_info(self, lat, lng, altitude_ft=400):
        """Get FAA airspace information for given coordinates"""
        try:
            # Check cache first
            cache_key = f"{lat:.6f},{lng:.6f},{altitude_ft}"
            now = time.time()
            
            if cache_key in self.airspace_cache:
                cached_data, timestamp = self.airspace_cache[cache_key]
                if now - timestamp < self.cache_timeout:
                    return cached_data
            
            # Query airspace information
            airspace_info = self._query_airspace_data(lat, lng, altitude_ft)
            
            # Cache the result
            self.airspace_cache[cache_key] = (airspace_info, now)
            
            return airspace_info
            
        except Exception as e:
            print(f"Error fetching FAA airspace info: {e}")
            return self._get_default_airspace_info()
    
    def _query_airspace_data(self, lat, lng, altitude_ft):
        """Query airspace data from available APIs"""
        # Since direct FAA API access may be limited, we'll simulate realistic data
        # In a production environment, you would use actual FAA APIs
        
        # Simulate airspace determination based on location
        airspace_class = self._determine_airspace_class(lat, lng)
        
        return {
            'airspace_class': airspace_class,
            'max_altitude_ft': self._get_max_altitude(airspace_class),
            'authorization_required': airspace_class in ['A', 'B', 'C', 'D'],
            'restrictions': self._get_airspace_restrictions(airspace_class),
            'tfr_active': False,  # Would be determined from actual NOTAM data
            'lat': lat,
            'lng': lng,
            'query_altitude': altitude_ft,
            'timestamp': datetime.now().isoformat()
        }
    
    def _determine_airspace_class(self, lat, lng):
        """Determine airspace class based on coordinates"""
        # This is a simplified implementation
        # In reality, you would query actual FAA airspace data
        
        # Major airports (Class B airspace)
        major_airports = [
            (40.7128, -74.0060),  # JFK/LGA area
            (34.0522, -118.2437), # LAX area
            (41.8781, -87.6298),  # ORD area
            (33.9425, -118.4081), # LAX
            (25.7617, -80.1918),  # MIA area
        ]
        
        # Check proximity to major airports
        for apt_lat, apt_lng in major_airports:
            if abs(lat - apt_lat) < 0.5 and abs(lng - apt_lng) < 0.5:
                return 'B'
        
        # Smaller airports (Class C/D)
        if self._near_airport(lat, lng, radius=0.2):
            return 'C'
        elif self._near_airport(lat, lng, radius=0.1):
            return 'D'
        
        # Most airspace is Class G (uncontrolled) below 1200ft
        return 'G'
    
    def _near_airport(self, lat, lng, radius):
        """Simple check if coordinates are near airports"""
        # This would use actual airport database in production
        import random
        return random.random() < 0.1  # 10% chance near airport
    
    def _get_max_altitude(self, airspace_class):
        """Get maximum altitude for airspace class"""
        altitude_limits = {
            'A': 'FL180+',
            'B': '10,000 ft',
            'C': '4,000 ft',
            'D': '2,500 ft',
            'E': '1,200 ft (surface area) / 10,000 ft (general)',
            'G': '1,200 ft'
        }
        return altitude_limits.get(airspace_class, '400 ft')
    
    def _get_airspace_restrictions(self, airspace_class):
        """Get restrictions for airspace class"""
        restrictions = {
            'A': 'IFR only, ATC clearance required',
            'B': 'ATC clearance required, Mode C transponder',
            'C': 'Two-way radio, Mode C transponder',
            'D': 'Two-way radio communication required',
            'E': 'No specific requirements (controlled)',
            'G': 'No ATC control (uncontrolled)'
        }
        return restrictions.get(airspace_class, 'Unknown restrictions')
    
    def _get_default_airspace_info(self):
        """Get default airspace info when API calls fail"""
        return {
            'airspace_class': 'G',
            'max_altitude_ft': '400 ft',
            'authorization_required': False,
            'restrictions': 'Default Class G airspace rules apply',
            'tfr_active': False,
            'lat': 0,
            'lng': 0,
            'query_altitude': 400,
            'timestamp': datetime.now().isoformat(),
            'error': 'Unable to fetch current airspace data'
        }
    
    def get_faa_restrictions(self, bounds):
        """Get FAA restrictions within map bounds"""
        try:
            # bounds format: [south, west, north, east]
            restrictions = []
            
            # Sample TFR data (in production, query actual NOTAM/TFR APIs)
            sample_tfrs = [
                {
                    'id': 'TFR_001',
                    'type': 'Temporary Flight Restriction',
                    'center': [40.7589, -73.9851],  # NYC area
                    'radius_nm': 3,
                    'altitude_floor': 0,
                    'altitude_ceiling': 18000,
                    'start_time': '2024-01-01T00:00:00Z',
                    'end_time': '2024-12-31T23:59:59Z',
                    'reason': 'Security TFR'
                },
                {
                    'id': 'TFR_002', 
                    'type': 'Temporary Flight Restriction',
                    'center': [38.8951, -77.0364],  # DC area
                    'radius_nm': 15,
                    'altitude_floor': 0,
                    'altitude_ceiling': 18000,
                    'start_time': '2024-01-01T00:00:00Z',
                    'end_time': '2024-12-31T23:59:59Z',
                    'reason': 'National Defense Airspace'
                }
            ]
            
            # Filter TFRs within bounds
            for tfr in sample_tfrs:
                lat, lng = tfr['center']
                if (bounds[0] <= lat <= bounds[2] and 
                    bounds[1] <= lng <= bounds[3]):
                    restrictions.append(tfr)
            
            return restrictions
            
        except Exception as e:
            print(f"Error fetching FAA restrictions: {e}")
            return []
    
    def get_faa_notams(self, bounds):
        """Get NOTAMs within map bounds"""
        try:
            # Sample NOTAM data
            sample_notams = [
                {
                    'id': 'NOTAM_001',
                    'type': 'NOTAM',
                    'location': [40.6892, -74.1745],  # Newark area
                    'message': 'Runway 4L/22R closed for maintenance',
                    'effective_start': '2024-01-15T06:00:00Z',
                    'effective_end': '2024-01-15T18:00:00Z',
                    'affects_uas': False
                },
                {
                    'id': 'NOTAM_002',
                    'type': 'UAS NOTAM',
                    'location': [34.0522, -118.2437],  # LAX area
                    'message': 'UAS operations prohibited within 5nm radius',
                    'effective_start': '2024-01-01T00:00:00Z',
                    'effective_end': '2024-12-31T23:59:59Z',
                    'affects_uas': True
                }
            ]
            
            # Filter NOTAMs within bounds
            notams = []
            for notam in sample_notams:
                lat, lng = notam['location']
                if (bounds[0] <= lat <= bounds[2] and 
                    bounds[1] <= lng <= bounds[3]):
                    notams.append(notam)
            
            return notams
            
        except Exception as e:
            print(f"Error fetching NOTAMs: {e}")
            return []
    
    def check_flight_path_airspace(self, waypoints):
        """Check airspace along entire flight path"""
        airspace_warnings = []
        
        for i, waypoint in enumerate(waypoints):
            lat = waypoint.get('lat', 0)
            lng = waypoint.get('lng', 0)
            alt = waypoint.get('altitude', 400)
            
            airspace_info = self.get_faa_airspace_info(lat, lng, alt)
            
            if airspace_info['authorization_required']:
                airspace_warnings.append({
                    'waypoint_index': i,
                    'lat': lat,
                    'lng': lng,
                    'airspace_class': airspace_info['airspace_class'],
                    'warning': f"Waypoint {i+1} requires authorization (Class {airspace_info['airspace_class']} airspace)",
                    'max_altitude': airspace_info['max_altitude_ft']
                })
            
            if airspace_info['tfr_active']:
                airspace_warnings.append({
                    'waypoint_index': i,
                    'lat': lat,
                    'lng': lng,
                    'warning': f"Waypoint {i+1} affected by active TFR",
                    'severity': 'high'
                })
        
        return airspace_warnings
    
    def get_laanc_info(self, lat, lng):
        """Get LAANC (Low Altitude Authorization and Notification Capability) info"""
        return {
            'laanc_available': True,
            'max_altitude_grid': self._get_laanc_grid_altitude(lat, lng),
            'facility_map_url': f"https://faa.gov/uas/recreational_fliers/where_can_i_fly/airspace_restrictions/facility_maps/",
            'authorization_url': "https://www.faa.gov/uas/commercial_operators/part_107_waivers/"
        }
    
    def _get_laanc_grid_altitude(self, lat, lng):
        """Get LAANC grid altitude for location"""
        # Simplified LAANC grid simulation
        # Real implementation would query actual FAA LAANC data
        
        # Most areas allow up to 400ft without authorization
        base_altitude = 400
        
        # Near airports, lower altitudes
        if self._near_airport(lat, lng, 0.1):
            return 100
        elif self._near_airport(lat, lng, 0.2):
            return 200
        else:
            return base_altitude


# Global instance
faa_maps_integration = FAAMapsIntegration()
