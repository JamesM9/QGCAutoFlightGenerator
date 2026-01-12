#!/usr/bin/env python3
"""
CPU Optimization Module for Flight Planning Tools
Provides thread pooling, caching, and performance optimization features
"""

import time
import threading
import queue
import concurrent.futures
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Callable
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QMutex, QWaitCondition, Qt
from PyQt5.QtWidgets import QProgressDialog, QApplication


class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.operation_times = {}
        self.api_call_count = 0
        self.cache_hit_count = 0
        self.cache_miss_count = 0
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        if self.start_time is None:
            self.start_time = time.time()
        self.operation_times[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> float:
        """End timing an operation and return duration"""
        if operation_name in self.operation_times:
            duration = time.time() - self.operation_times[operation_name]
            print(f"[TIME] {operation_name}: {duration:.3f}s")
            return duration
        return 0.0
    
    def get_total_time(self) -> float:
        """Get total execution time"""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0
    
    def log_api_call(self, cached: bool = False):
        """Log API call statistics"""
        self.api_call_count += 1
        if cached:
            self.cache_hit_count += 1
        else:
            self.cache_miss_count += 1
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'total_time': self.get_total_time(),
            'api_calls': self.api_call_count,
            'cache_hits': self.cache_hit_count,
            'cache_misses': self.cache_miss_count,
            'cache_hit_rate': self.cache_hit_count / max(self.api_call_count, 1) * 100
        }


class OptimizedTerrainQuery(QObject):
    """Optimized terrain elevation query using hybrid tile-based caching system"""
    
    elevation_ready = pyqtSignal(float, float, float)  # lat, lon, elevation
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        # Use integrated terrain system with tile-based caching
        self.terrain_query = self._create_terrain_query(max_workers)
        self.monitor = PerformanceMonitor()
    
    def get_elevation(self, lat: float, lon: float) -> float:
        """Get elevation with caching"""
        return self.terrain_query.get_elevation(lat, lon)
    
    def get_elevation_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """Get elevations for multiple coordinates efficiently"""
        return self.terrain_query.get_elevation_batch(coordinates)
    
    def get_elevation_with_timeout(self, lat: float, lon: float, timeout: float = 2.0) -> float:
        """Get elevation with timeout to prevent hanging"""
        return self.terrain_query.get_elevation_with_timeout(lat, lon, timeout)
    
    
    def _create_terrain_query(self, max_workers: int):
        """Create terrain query with tile-based caching"""
        import os
        import json
        import requests
        from typing import Dict, Tuple, Optional, List
        
        class TerrainTileCache:
            """Manages terrain tile caching similar to QGroundControl's system"""
            
            def __init__(self, cache_dir: str = "terrain_cache"):
                self.cache_dir = cache_dir
                self.cache_mutex = QMutex()
                self.tile_cache = {}  # In-memory cache for loaded tiles
                
                # Create cache directory if it doesn't exist
                os.makedirs(cache_dir, exist_ok=True)
                
                # Tile size (0.1 degree x 0.1 degree for better granularity)
                self.tile_size = 0.1
                
                # API endpoint
                self.api_url = "https://api.opentopodata.org/v1/srtm90m"
            
            def get_tile_filename(self, lat: float, lon: float) -> str:
                """Generate tile filename based on coordinates"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                
                # Create filename
                lat_str = f"{tile_lat:+.1f}".replace('+', 'N').replace('-', 'S')
                lon_str = f"{tile_lon:+.1f}".replace('+', 'E').replace('-', 'W')
                return f"{lat_str}{lon_str}.json"
            
            def get_tile_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
                """Get tile coordinates for given lat/lon"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                return tile_lat, tile_lon
            
            def is_tile_cached(self, tile_lat: float, tile_lon: float) -> bool:
                """Check if tile is cached locally"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                return os.path.exists(filepath)
            
            def download_tile(self, tile_lat: float, tile_lon: float) -> bool:
                """Download terrain tile data from OpenTopography API"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    # Generate grid of points within the tile
                    points = []
                    for lat_offset in [0, self.tile_size/2, self.tile_size]:
                        for lon_offset in [0, self.tile_size/2, self.tile_size]:
                            point_lat = tile_lat + lat_offset
                            point_lon = tile_lon + lon_offset
                            points.append(f"{point_lat},{point_lon}")
                    
                    # Make API request
                    locations = "|".join(points)
                    url = f"{self.api_url}?locations={locations}"
                    
                    print(f"Downloading terrain tile: {filename}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Save tile data
                    with open(filepath, 'w') as f:
                        json.dump(data, f)
                    
                    print(f"Successfully downloaded: {filename}")
                    return True
                    
                except Exception as e:
                    print(f"Failed to download tile {filename}: {e}")
                    return False
            
            def load_tile(self, tile_lat: float, tile_lon: float) -> Optional[Dict]:
                """Load terrain tile data from cache or download if needed"""
                try:
                    self.cache_mutex.lock()
                    
                    # Check in-memory cache first
                    cache_key = (tile_lat, tile_lon)
                    if cache_key in self.tile_cache:
                        tile_data = self.tile_cache[cache_key]
                        self.cache_mutex.unlock()
                        return tile_data
                    
                    self.cache_mutex.unlock()
                    
                    # Check if tile exists on disk
                    if not self.is_tile_cached(tile_lat, tile_lon):
                        # Download tile if not cached
                        if not self.download_tile(tile_lat, tile_lon):
                            return None
                    
                    # Load tile from disk
                    filename = self.get_tile_filename(tile_lat, tile_lon)
                    filepath = os.path.join(self.cache_dir, filename)
                    
                    with open(filepath, 'r') as f:
                        tile_data = json.load(f)
                    
                    # Cache in memory
                    self.cache_mutex.lock()
                    self.tile_cache[cache_key] = tile_data
                    self.cache_mutex.unlock()
                    
                    return tile_data
                    
                except Exception as e:
                    print(f"Error loading tile {filename}: {e}")
                    return None
            
            def get_elevation_from_tile(self, tile_data: Dict, lat: float, lon: float) -> float:
                """Extract elevation from tile data using interpolation"""
                if not tile_data or "results" not in tile_data:
                    return 0.0
                
                results = tile_data["results"]
                if not results:
                    return 0.0
                
                # Find the closest point in the tile
                min_distance = float('inf')
                closest_elevation = 0.0
                
                for result in results:
                    if "elevation" in result and "location" in result:
                        result_lat = result["location"]["lat"]
                        result_lon = result["location"]["lng"]
                        elevation = result["elevation"]
                        
                        # Calculate distance
                        distance = ((lat - result_lat) ** 2 + (lon - result_lon) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_elevation = elevation
                
                return closest_elevation if closest_elevation is not None else 0.0
            
            def get_elevation_direct(self, lat: float, lon: float) -> float:
                """Get elevation directly from API for individual waypoints with confirmation loop"""
                import time
                
                # Rate limiting - wait between requests
                current_time = time.time()
                if hasattr(self, 'last_request_time'):
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < 1.0:  # Wait 1 second between requests
                        time.sleep(1.0 - time_since_last)
                
                self.last_request_time = time.time()
                
                # Confirmation loop - retry until successful or max attempts reached
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        import requests
                        import json
                        
                        url = "https://api.opentopodata.org/v1/srtm90m"
                        params = {'locations': f"{lat},{lon}"}
                        
                        response = requests.get(url, params=params, timeout=10)  # Increased timeout
                        
                        # Handle rate limiting
                        if response.status_code == 429:
                            wait_time = 2 + (attempt * 2)  # Exponential backoff
                            print(f"Rate limited (attempt {attempt + 1}), waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        data = response.json()
                        
                        if "results" in data and data["results"]:
                            elevation = data["results"][0]["elevation"]
                            if elevation is not None:
                                print(f"[OK] Terrain elevation confirmed: {lat:.6f}, {lon:.6f} -> {elevation}m")
                                return elevation
                        
                        # If no elevation data, wait and retry
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] No elevation data (attempt {attempt + 1}), retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        
                        return 0.0
                    
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] Terrain query failed (attempt {attempt + 1}): {e}")
                            print(f"   Retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        else:
                            print(f"[ERROR] Terrain query failed after {max_attempts} attempts: {e}")
                            return 0.0
                
                return 0.0
        
        class IntegratedTerrainQuery:
            """Integrated terrain elevation query system with tile-based caching"""
            
            def __init__(self, max_workers: int = 4):
                self.tile_cache = TerrainTileCache()
                self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
                self.cache_mutex = QMutex()
                self.elevation_cache = {}  # Cache for individual elevation queries
                
            def get_elevation(self, lat: float, lon: float) -> float:
                """Get elevation for a single coordinate using direct API queries"""
                # Check individual elevation cache first
                cache_key = (round(lat, 4), round(lon, 4))
                
                self.cache_mutex.lock()
                if cache_key in self.elevation_cache:
                    elevation = self.elevation_cache[cache_key]
                    self.cache_mutex.unlock()
                    return elevation
                self.cache_mutex.unlock()
                
                # Get elevation directly from API for individual waypoints
                elevation = self.tile_cache.get_elevation_direct(lat, lon)
                
                # Cache the result
                self.cache_mutex.lock()
                self.elevation_cache[cache_key] = elevation
                self.cache_mutex.unlock()
                
                return elevation
            
            def get_elevation_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
                """Get elevations for multiple coordinates efficiently"""
                elevations = []
                
                for lat, lon in coordinates:
                    elevation = self.get_elevation(lat, lon)
                    elevations.append(elevation)
                
                return elevations
            
            def get_elevation_with_timeout(self, lat: float, lon: float, timeout: float = 2.0) -> float:
                """Get elevation with timeout to prevent hanging"""
                import threading
                
                result = [None]
                exception = [None]
                
                def fetch_elevation():
                    try:
                        elevation = self.get_elevation(lat, lon)
                        result[0] = elevation
                    except Exception as e:
                        exception[0] = e
                
                # Start the fetch in a separate thread
                thread = threading.Thread(target=fetch_elevation)
                thread.daemon = True
                thread.start()
                
                # Wait for the result with timeout
                thread.join(timeout=timeout)
                
                if thread.is_alive():
                    # Timeout occurred, return default elevation
                    print(f"Terrain query timeout for {lat}, {lon}, using default elevation")
                    return 0.0
                
                if exception[0]:
                    # Exception occurred, return default elevation
                    print(f"Terrain query error for {lat}, {lon}: {exception[0]}")
                    return 0.0
                
                if result[0] is not None:
                    return result[0]
                
                # Fallback to default elevation
                return 0.0
            
            def cleanup(self):
                """Clean up resources"""
                self.thread_pool.shutdown(wait=True)
        
        return IntegratedTerrainQuery(max_workers)

    def cleanup(self):
        """Clean up resources"""
        self.terrain_query.cleanup()
    
    def get_default_terrain_elevation(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """Get default terrain elevations when API fails"""
        return [0.0] * len(coordinates)  # Default to sea level
class MissionGeneratorOptimizer:
    """Optimize mission generation process"""
    
    def __init__(self, max_workers: int = 4):
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.monitor = PerformanceMonitor()
        self.terrain_query = OptimizedTerrainQuery(max_workers=max_workers)
        self.waypoint_optimizer = WaypointOptimizer()
    
    def generate_mission_sequential(self, waypoints: List[Tuple[float, float]], 
                                altitude: float, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Generate mission items sequentially with terrain elevation queries and progress updates"""
        self.monitor.start_operation("mission_generation")
        
        mission_items = []
        total_waypoints = len(waypoints)
        
        if progress_callback:
            progress_callback(5)  # Start progress
        
        for i, (lat, lon) in enumerate(waypoints):
            try:
                # Query terrain elevation for this specific waypoint
                if progress_callback:
                    progress = 5 + int((i / total_waypoints) * 90)
                    progress_callback(progress)
                
                # Get terrain elevation with timeout
                terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lon, timeout=2.0)
                
                # Calculate AMSL altitude (terrain elevation + AGL altitude)
                absolute_altitude = terrain_elevation + altitude
                
                # Create mission item with correct AMSL altitude
                mission_item = {
                    "AMSLAltAboveTerrain": absolute_altitude,  # AMSL altitude (terrain + AGL)
                    "Altitude": altitude,  # AGL altitude (constant)
                    "AltitudeMode": 3,  # Terrain following mode
                    "autoContinue": True,
                    "command": 16,  # NAV_WAYPOINT
                    "frame": 0,
                    "params": [0, 0, 0, None, lat, lon, absolute_altitude],  # AMSL altitude
                    "type": "SimpleItem"  # Required field for QGC
                }
                mission_items.append(mission_item)
                
                # Update progress after each waypoint
                if progress_callback:
                    progress = 5 + int(((i + 1) / total_waypoints) * 90)
                    progress_callback(progress)
                    
            except Exception as e:
                print(f"Error processing waypoint {i+1}: {e}")
                # Use default elevation if terrain query fails
                absolute_altitude = altitude  # Fallback to AGL altitude
                
                mission_item = {
                    "AMSLAltAboveTerrain": absolute_altitude,  # Fallback to AGL altitude
                    "Altitude": altitude,  # AGL altitude
                    "AltitudeMode": 3,  # Terrain following mode
                    "autoContinue": True,
                    "command": 16,  # NAV_WAYPOINT
                    "frame": 0,
                    "params": [0, 0, 0, None, lat, lon, absolute_altitude],  # Fallback altitude
                    "type": "SimpleItem"  # Required field for QGC
                }
                mission_items.append(mission_item)
                
                # Continue with next waypoint
                if progress_callback:
                    progress = 5 + int(((i + 1) / total_waypoints) * 90)
                    progress_callback(progress)
        
        if progress_callback:
            progress_callback(100)  # Complete
        
        self.monitor.end_operation("mission_generation")
        return mission_items
    
    def generate_mission_parallel(self, waypoints: List[Tuple[float, float]], 
                                altitude: float, progress_callback: Optional[Callable] = None) -> List[Dict]:
        """Generate mission items - now uses sequential processing to prevent hanging"""
        return self.generate_mission_sequential(waypoints, altitude, progress_callback)
    
    def _generate_waypoint_item(self, data: Tuple[int, float, float, float]) -> Dict:
        """Generate a single waypoint item in proper QGC format"""
        index, lat, lon, altitude = data
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
        absolute_altitude = terrain_elevation + altitude
        
        return {
            "AMSLAltAboveTerrain": absolute_altitude,  # AMSL altitude (terrain + AGL)
            "Altitude": altitude,
            "AltitudeMode": 3,  # Terrain following mode
            "autoContinue": True,
            "command": 16,  # NAV_WAYPOINT
            "frame": 0,
            "params": [0, 0, 0, None, lat, lon, absolute_altitude],
            "type": "SimpleItem"  # Required field for QGC
        }
    
    def _create_fallback_waypoint(self, index: int, coords: Tuple[float, float]) -> Dict:
        """Create a fallback waypoint if generation fails"""
        lat, lon = coords
        default_altitude = 100  # Default altitude in meters
        
        # Get terrain elevation for fallback waypoint
        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
        absolute_altitude = terrain_elevation + default_altitude
        return {
            "AMSLAltAboveTerrain": absolute_altitude,  # AMSL altitude (terrain + AGL)
            "Altitude": default_altitude,
            "AltitudeMode": 3,  # Terrain following mode
            "autoContinue": True,
            "command": 16,  # NAV_WAYPOINT
            "frame": 0,
            "params": [0, 0, 0, None, lat, lon, absolute_altitude],
            "type": "SimpleItem"  # Required field for QGC
        }
    
    
    def get_default_terrain_elevation(self, coordinates: List[Tuple[float, float]]) -> List[float]:
        """Get default terrain elevations when API fails"""
        return [0.0] * len(coordinates)  # Default to sea level

    
    def _create_terrain_query(self, max_workers: int):
        """Create terrain query with tile-based caching"""
        import os
        import json
        import requests
        from typing import Dict, Tuple, Optional, List
        
        class TerrainTileCache:
            """Manages terrain tile caching similar to QGroundControl's system"""
            
            def __init__(self, cache_dir: str = "terrain_cache"):
                self.cache_dir = cache_dir
                self.cache_mutex = QMutex()
                self.tile_cache = {}  # In-memory cache for loaded tiles
                
                # Create cache directory if it doesn't exist
                os.makedirs(cache_dir, exist_ok=True)
                
                # Tile size (0.1 degree x 0.1 degree for better granularity)
                self.tile_size = 0.1
                
                # API endpoint
                self.api_url = "https://api.opentopodata.org/v1/srtm90m"
            
            def get_tile_filename(self, lat: float, lon: float) -> str:
                """Generate tile filename based on coordinates"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                
                # Create filename
                lat_str = f"{tile_lat:+.1f}".replace('+', 'N').replace('-', 'S')
                lon_str = f"{tile_lon:+.1f}".replace('+', 'E').replace('-', 'W')
                return f"{lat_str}{lon_str}.json"
            
            def get_tile_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
                """Get tile coordinates for given lat/lon"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                return tile_lat, tile_lon
            
            def is_tile_cached(self, tile_lat: float, tile_lon: float) -> bool:
                """Check if tile is cached locally"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                return os.path.exists(filepath)
            
            def download_tile(self, tile_lat: float, tile_lon: float) -> bool:
                """Download terrain tile data from OpenTopography API"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    # Generate grid of points within the tile
                    points = []
                    for lat_offset in [0, self.tile_size/2, self.tile_size]:
                        for lon_offset in [0, self.tile_size/2, self.tile_size]:
                            point_lat = tile_lat + lat_offset
                            point_lon = tile_lon + lon_offset
                            points.append(f"{point_lat},{point_lon}")
                    
                    # Make API request
                    locations = "|".join(points)
                    url = f"{self.api_url}?locations={locations}"
                    
                    print(f"Downloading terrain tile: {filename}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Save tile data
                    with open(filepath, 'w') as f:
                        json.dump(data, f)
                    
                    print(f"Successfully downloaded: {filename}")
                    return True
                    
                except Exception as e:
                    print(f"Failed to download tile {filename}: {e}")
                    return False
            
            def load_tile(self, tile_lat: float, tile_lon: float) -> Optional[Dict]:
                """Load terrain tile data from cache or download if needed"""
                self.cache_mutex.lock()
                
                # Check in-memory cache first
                cache_key = (tile_lat, tile_lon)
                if cache_key in self.tile_cache:
                    tile_data = self.tile_cache[cache_key]
                    self.cache_mutex.unlock()
                    return tile_data
                
                self.cache_mutex.unlock()
                
                # Check if tile exists on disk
                if not self.is_tile_cached(tile_lat, tile_lon):
                    # Download tile if not cached
                    if not self.download_tile(tile_lat, tile_lon):
                        return None
                
                # Load tile from disk
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        tile_data = json.load(f)
                    
                    # Cache in memory
                    self.cache_mutex.lock()
                    self.tile_cache[cache_key] = tile_data
                    self.cache_mutex.unlock()
                    
                    return tile_data
                    
                except Exception as e:
                    print(f"Error loading tile {filename}: {e}")
                    return None
            
            def get_elevation_from_tile(self, tile_data: Dict, lat: float, lon: float) -> float:
                """Extract elevation from tile data using interpolation"""
                if not tile_data or "results" not in tile_data:
                    return 0.0
                
                results = tile_data["results"]
                if not results:
                    return 0.0
                
                # Find the closest point in the tile
                min_distance = float('inf')
                closest_elevation = 0.0
                
                for result in results:
                    if "elevation" in result and "location" in result:
                        result_lat = result["location"]["lat"]
                        result_lon = result["location"]["lng"]
                        elevation = result["elevation"]
                        
                        # Calculate distance
                        distance = ((lat - result_lat) ** 2 + (lon - result_lon) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_elevation = elevation
                
                return closest_elevation if closest_elevation is not None else 0.0
            
            def get_elevation_direct(self, lat: float, lon: float) -> float:
                """Get elevation directly from API for individual waypoints with confirmation loop"""
                import time
                
                # Rate limiting - wait between requests
                current_time = time.time()
                if hasattr(self, 'last_request_time'):
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < 1.0:  # Wait 1 second between requests
                        time.sleep(1.0 - time_since_last)
                
                self.last_request_time = time.time()
                
                # Confirmation loop - retry until successful or max attempts reached
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        import requests
                        import json
                        
                        url = "https://api.opentopodata.org/v1/srtm90m"
                        params = {'locations': f"{lat},{lon}"}
                        
                        response = requests.get(url, params=params, timeout=10)  # Increased timeout
                        
                        # Handle rate limiting
                        if response.status_code == 429:
                            wait_time = 2 + (attempt * 2)  # Exponential backoff
                            print(f"Rate limited (attempt {attempt + 1}), waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        data = response.json()
                        
                        if "results" in data and data["results"]:
                            elevation = data["results"][0]["elevation"]
                            if elevation is not None:
                                print(f"[OK] Terrain elevation confirmed: {lat:.6f}, {lon:.6f} -> {elevation}m")
                                return elevation
                        
                        # If no elevation data, wait and retry
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] No elevation data (attempt {attempt + 1}), retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        
                        return 0.0
                        
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] Terrain query failed (attempt {attempt + 1}): {e}")
                            print(f"   Retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        else:
                            print(f"[ERROR] Terrain query failed after {max_attempts} attempts: {e}")
                            return 0.0
                
                return 0.0
        
        class IntegratedTerrainQuery:
            """Integrated terrain elevation query system with tile-based caching"""
            
            def __init__(self, max_workers: int = 4):
                self.tile_cache = TerrainTileCache()
                self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
                self.cache_mutex = QMutex()
                self.elevation_cache = {}  # Cache for individual elevation queries
                
            def get_elevation(self, lat: float, lon: float) -> float:
                """Get elevation for a single coordinate using direct API queries"""
                # Check individual elevation cache first
                cache_key = (round(lat, 4), round(lon, 4))
                
                self.cache_mutex.lock()
                if cache_key in self.elevation_cache:
                    elevation = self.elevation_cache[cache_key]
                    self.cache_mutex.unlock()
                    return elevation
                self.cache_mutex.unlock()
                
                # Get elevation directly from API for individual waypoints
                elevation = self.tile_cache.get_elevation_direct(lat, lon)
                
                # Cache the result
                self.cache_mutex.lock()
                self.elevation_cache[cache_key] = elevation
                self.cache_mutex.unlock()
                
                return elevation
            
            def get_elevation_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
                """Get elevations for multiple coordinates efficiently"""
                elevations = []
                
                for lat, lon in coordinates:
                    elevation = self.get_elevation(lat, lon)
                    elevations.append(elevation)
                
                return elevations
            
            def get_elevation_with_timeout(self, lat: float, lon: float, timeout: float = 2.0) -> float:
                """Get elevation with timeout to prevent hanging"""
                import threading
                
                result = [None]
                exception = [None]
                
                def fetch_elevation():
                    try:
                        elevation = self.get_elevation(lat, lon)
                        result[0] = elevation
                    except Exception as e:
                        exception[0] = e
                
                # Start the fetch in a separate thread
                thread = threading.Thread(target=fetch_elevation)
                thread.daemon = True
                thread.start()
                
                # Wait for the result with timeout
                thread.join(timeout=timeout)
                
                if thread.is_alive():
                    # Timeout occurred, return default elevation
                    print(f"Terrain query timeout for {lat}, {lon}, using default elevation")
                    return 0.0
                
                if exception[0]:
                    # Exception occurred, return default elevation
                    print(f"Terrain query error for {lat}, {lon}: {exception[0]}")
                    return 0.0
                
                if result[0] is not None:
                    return result[0]
                
                # Fallback to default elevation
                return 0.0
            
            def cleanup(self):
                """Clean up resources"""
                self.thread_pool.shutdown(wait=True)
        
        return IntegratedTerrainQuery(max_workers)
    
    def cleanup(self):
        """Clean up resources"""
        self.thread_pool.shutdown(wait=True)
        self.terrain_query.cleanup()


class CPUOptimizedProgressDialog(QProgressDialog):
    """CPU-optimized progress dialog with performance monitoring"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(title, "Cancel", 0, 100, parent)
        self.setWindowModality(Qt.WindowModal)
        self.setAutoClose(True)
        self.setMinimumDuration(0)  # Show immediately
        self.monitor = PerformanceMonitor()
        
    def update_with_stats(self, value: int, operation: str):
        """Update progress with performance statistics"""
        self.setValue(value)
        self.setLabelText(f"{operation} ({value}%)")
        
        # Process events to keep UI responsive
        if value % 10 == 0:  # Update every 10%
            QApplication.processEvents()
    
    def show_completion_stats(self):
        """Show completion statistics"""
        stats = self.monitor.get_stats()
        self.setLabelText(
            f"Complete! Total time: {stats['total_time']:.2f}s\n"
            f"API calls: {stats['api_calls']}, Cache hit rate: {stats['cache_hit_rate']:.1f}%"
        )



class WaypointOptimizer:
    """Optimize waypoint generation and processing"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
    
    def optimize_waypoints(self, waypoints: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Optimize waypoint list for better performance"""
        self.monitor.start_operation("waypoint_optimization")
        
        # Simple optimization: remove duplicate consecutive waypoints
        optimized = []
        prev_waypoint = None
        
        for waypoint in waypoints:
            if prev_waypoint is None or waypoint != prev_waypoint:
                optimized.append(waypoint)
            prev_waypoint = waypoint
        
        self.monitor.end_operation("waypoint_optimization")
        return optimized
    
    def interpolate_waypoints_optimized(self, start: Tuple[float, float], end: Tuple[float, float], interval: float) -> List[Tuple[float, float]]:
        """Interpolate waypoints between start and end points"""
        import math
        
        start_lat, start_lon = start
        end_lat, end_lon = end
        
        # Calculate distance between points
        lat_diff = end_lat - start_lat
        lon_diff = end_lon - start_lon
        
        # Calculate total distance in meters (approximate)
        lat_dist = lat_diff * 111000  # 1 degree latitude ≈ 111km
        lon_dist = lon_diff * 111000 * math.cos(math.radians(start_lat))  # Adjust for longitude
        total_dist = math.sqrt(lat_dist**2 + lon_dist**2)
        
        # Calculate number of waypoints needed
        num_waypoints = int(total_dist / interval) + 1
        
        waypoints = []
        for i in range(num_waypoints):
            ratio = i / max(num_waypoints - 1, 1)
            lat = start_lat + lat_diff * ratio
            lon = start_lon + lon_diff * ratio
            waypoints.append((lat, lon))
        
        return waypoints
    
    
    def _create_terrain_query(self, max_workers: int):
        """Create terrain query with tile-based caching"""
        import os
        import json
        import requests
        from typing import Dict, Tuple, Optional, List
        
        class TerrainTileCache:
            """Manages terrain tile caching similar to QGroundControl's system"""
            
            def __init__(self, cache_dir: str = "terrain_cache"):
                self.cache_dir = cache_dir
                self.cache_mutex = QMutex()
                self.tile_cache = {}  # In-memory cache for loaded tiles
                
                # Create cache directory if it doesn't exist
                os.makedirs(cache_dir, exist_ok=True)
                
                # Tile size (0.1 degree x 0.1 degree for better granularity)
                self.tile_size = 0.1
                
                # API endpoint
                self.api_url = "https://api.opentopodata.org/v1/srtm90m"
            
            def get_tile_filename(self, lat: float, lon: float) -> str:
                """Generate tile filename based on coordinates"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                
                # Create filename
                lat_str = f"{tile_lat:+.1f}".replace('+', 'N').replace('-', 'S')
                lon_str = f"{tile_lon:+.1f}".replace('+', 'E').replace('-', 'W')
                return f"{lat_str}{lon_str}.json"
            
            def get_tile_coordinates(self, lat: float, lon: float) -> Tuple[float, float]:
                """Get tile coordinates for given lat/lon"""
                # Round to tile boundaries
                tile_lat = round(lat / self.tile_size) * self.tile_size
                tile_lon = round(lon / self.tile_size) * self.tile_size
                return tile_lat, tile_lon
            
            def is_tile_cached(self, tile_lat: float, tile_lon: float) -> bool:
                """Check if tile is cached locally"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                return os.path.exists(filepath)
            
            def download_tile(self, tile_lat: float, tile_lon: float) -> bool:
                """Download terrain tile data from OpenTopography API"""
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    # Generate grid of points within the tile
                    points = []
                    for lat_offset in [0, self.tile_size/2, self.tile_size]:
                        for lon_offset in [0, self.tile_size/2, self.tile_size]:
                            point_lat = tile_lat + lat_offset
                            point_lon = tile_lon + lon_offset
                            points.append(f"{point_lat},{point_lon}")
                    
                    # Make API request
                    locations = "|".join(points)
                    url = f"{self.api_url}?locations={locations}"
                    
                    print(f"Downloading terrain tile: {filename}")
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    # Save tile data
                    with open(filepath, 'w') as f:
                        json.dump(data, f)
                    
                    print(f"Successfully downloaded: {filename}")
                    return True
                    
                except Exception as e:
                    print(f"Failed to download tile {filename}: {e}")
                    return False
            
            def load_tile(self, tile_lat: float, tile_lon: float) -> Optional[Dict]:
                """Load terrain tile data from cache or download if needed"""
                self.cache_mutex.lock()
                
                # Check in-memory cache first
                cache_key = (tile_lat, tile_lon)
                if cache_key in self.tile_cache:
                    tile_data = self.tile_cache[cache_key]
                    self.cache_mutex.unlock()
                    return tile_data
                
                self.cache_mutex.unlock()
                
                # Check if tile exists on disk
                if not self.is_tile_cached(tile_lat, tile_lon):
                    # Download tile if not cached
                    if not self.download_tile(tile_lat, tile_lon):
                        return None
                
                # Load tile from disk
                filename = self.get_tile_filename(tile_lat, tile_lon)
                filepath = os.path.join(self.cache_dir, filename)
                
                try:
                    with open(filepath, 'r') as f:
                        tile_data = json.load(f)
                    
                    # Cache in memory
                    self.cache_mutex.lock()
                    self.tile_cache[cache_key] = tile_data
                    self.cache_mutex.unlock()
                    
                    return tile_data
                    
                except Exception as e:
                    print(f"Error loading tile {filename}: {e}")
                    return None
            
            def get_elevation_from_tile(self, tile_data: Dict, lat: float, lon: float) -> float:
                """Extract elevation from tile data using interpolation"""
                if not tile_data or "results" not in tile_data:
                    return 0.0
                
                results = tile_data["results"]
                if not results:
                    return 0.0
                
                # Find the closest point in the tile
                min_distance = float('inf')
                closest_elevation = 0.0
                
                for result in results:
                    if "elevation" in result and "location" in result:
                        result_lat = result["location"]["lat"]
                        result_lon = result["location"]["lng"]
                        elevation = result["elevation"]
                        
                        # Calculate distance
                        distance = ((lat - result_lat) ** 2 + (lon - result_lon) ** 2) ** 0.5
                        
                        if distance < min_distance:
                            min_distance = distance
                            closest_elevation = elevation
                
                return closest_elevation if closest_elevation is not None else 0.0
            
            def get_elevation_direct(self, lat: float, lon: float) -> float:
                """Get elevation directly from API for individual waypoints with confirmation loop"""
                import time
                
                # Rate limiting - wait between requests
                current_time = time.time()
                if hasattr(self, 'last_request_time'):
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < 1.0:  # Wait 1 second between requests
                        time.sleep(1.0 - time_since_last)
                
                self.last_request_time = time.time()
                
                # Confirmation loop - retry until successful or max attempts reached
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        import requests
                        import json
                        
                        url = "https://api.opentopodata.org/v1/srtm90m"
                        params = {'locations': f"{lat},{lon}"}
                        
                        response = requests.get(url, params=params, timeout=10)  # Increased timeout
                        
                        # Handle rate limiting
                        if response.status_code == 429:
                            wait_time = 2 + (attempt * 2)  # Exponential backoff
                            print(f"Rate limited (attempt {attempt + 1}), waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        
                        response.raise_for_status()
                        data = response.json()
                        
                        if "results" in data and data["results"]:
                            elevation = data["results"][0]["elevation"]
                            if elevation is not None:
                                print(f"[OK] Terrain elevation confirmed: {lat:.6f}, {lon:.6f} -> {elevation}m")
                                return elevation
                        
                        # If no elevation data, wait and retry
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] No elevation data (attempt {attempt + 1}), retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        
                        return 0.0
                        
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            print(f"[WARNING] Terrain query failed (attempt {attempt + 1}): {e}")
                            print(f"   Retrying in 2 seconds...")
                            time.sleep(2)
                            continue
                        else:
                            print(f"[ERROR] Terrain query failed after {max_attempts} attempts: {e}")
                            return 0.0
                
                return 0.0
        
        class IntegratedTerrainQuery:
            """Integrated terrain elevation query system with tile-based caching"""
            
            def __init__(self, max_workers: int = 4):
                self.tile_cache = TerrainTileCache()
                self.thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
                self.cache_mutex = QMutex()
                self.elevation_cache = {}  # Cache for individual elevation queries
                
            def get_elevation(self, lat: float, lon: float) -> float:
                """Get elevation for a single coordinate using direct API queries"""
                # Check individual elevation cache first
                cache_key = (round(lat, 4), round(lon, 4))
                
                self.cache_mutex.lock()
                if cache_key in self.elevation_cache:
                    elevation = self.elevation_cache[cache_key]
                    self.cache_mutex.unlock()
                    return elevation
                self.cache_mutex.unlock()
                
                # Get elevation directly from API for individual waypoints
                elevation = self.tile_cache.get_elevation_direct(lat, lon)
                
                # Cache the result
                self.cache_mutex.lock()
                self.elevation_cache[cache_key] = elevation
                self.cache_mutex.unlock()
                
                return elevation
            
            def get_elevation_batch(self, coordinates: List[Tuple[float, float]]) -> List[float]:
                """Get elevations for multiple coordinates efficiently"""
                elevations = []
                
                for lat, lon in coordinates:
                    elevation = self.get_elevation(lat, lon)
                    elevations.append(elevation)
                
                return elevations
            
            def get_elevation_with_timeout(self, lat: float, lon: float, timeout: float = 2.0) -> float:
                """Get elevation with timeout to prevent hanging"""
                import threading
                
                result = [None]
                exception = [None]
                
                def fetch_elevation():
                    try:
                        elevation = self.get_elevation(lat, lon)
                        result[0] = elevation
                    except Exception as e:
                        exception[0] = e
                
                # Start the fetch in a separate thread
                thread = threading.Thread(target=fetch_elevation)
                thread.daemon = True
                thread.start()
                
                # Wait for the result with timeout
                thread.join(timeout=timeout)
                
                if thread.is_alive():
                    # Timeout occurred, return default elevation
                    print(f"Terrain query timeout for {lat}, {lon}, using default elevation")
                    return 0.0
                
                if exception[0]:
                    # Exception occurred, return default elevation
                    print(f"Terrain query error for {lat}, {lon}: {exception[0]}")
                    return 0.0
                
                if result[0] is not None:
                    return result[0]
                
                # Fallback to default elevation
                return 0.0
            
            def cleanup(self):
                """Clean up resources"""
                self.thread_pool.shutdown(wait=True)
        
        return IntegratedTerrainQuery(max_workers)

    def cleanup(self):
        """Clean up resources"""
        pass


# Global optimization manager
class GlobalOptimizationManager:
    """Global manager for CPU optimization across all tools"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.mission_generators = {}
            self.terrain_queries = {}
            self.waypoint_optimizers = {}
            self.monitor = PerformanceMonitor()
    
    def get_mission_generator(self, tool_name: str) -> MissionGeneratorOptimizer:
        """Get or create mission generator for a tool"""
        if tool_name not in self.mission_generators:
            self.mission_generators[tool_name] = MissionGeneratorOptimizer()
        return self.mission_generators[tool_name]
    
    def get_terrain_query(self, tool_name: str) -> OptimizedTerrainQuery:
        """Get or create terrain query for a tool"""
        if tool_name not in self.terrain_queries:
            self.terrain_queries[tool_name] = OptimizedTerrainQuery()
        return self.terrain_queries[tool_name]
    
    def get_waypoint_optimizer(self, tool_name: str) -> WaypointOptimizer:
        """Get or create waypoint optimizer for a tool"""
        if tool_name not in self.waypoint_optimizers:
            self.waypoint_optimizers[tool_name] = WaypointOptimizer()
        return self.waypoint_optimizers[tool_name]
    
    def cleanup_all(self):
        """Clean up all resources"""
        for generator in self.mission_generators.values():
            generator.cleanup()
        for terrain_query in self.terrain_queries.values():
            terrain_query.cleanup()
        self.mission_generators.clear()
        self.terrain_queries.clear()
        self.waypoint_optimizers.clear()
    
    def get_global_stats(self) -> Dict:
        """Get global performance statistics"""
        return self.monitor.get_stats()


# Convenience functions
def get_optimized_terrain_query(tool_name: str) -> OptimizedTerrainQuery:
    """Get optimized terrain query for a tool"""
    return GlobalOptimizationManager().get_terrain_query(tool_name)

def get_optimized_mission_generator(tool_name: str) -> MissionGeneratorOptimizer:
    """Get optimized mission generator for a tool"""
    return GlobalOptimizationManager().get_mission_generator(tool_name)

def get_optimized_waypoint_optimizer(tool_name: str) -> WaypointOptimizer:
    """Get optimized waypoint optimizer for a tool"""
    return GlobalOptimizationManager().get_waypoint_optimizer(tool_name)

def create_optimized_progress_dialog(title: str, parent=None) -> CPUOptimizedProgressDialog:
    """Create an optimized progress dialog"""
    return CPUOptimizedProgressDialog(title, parent)
