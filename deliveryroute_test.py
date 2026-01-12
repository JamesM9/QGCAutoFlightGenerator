import json
import sys
import time
import requests
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for PyQt compatibility
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout, QMainWindow,
    QHBoxLayout, QWidget, QGroupBox, QLineEdit, QTextEdit, QScrollArea, QGridLayout, QSplitter, QDialog
)
from PyQt5.QtCore import QUrl, Qt, QObject, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from shapely.geometry import Point, MultiPoint
from geopy.distance import distance as geopy_distance
from settings_manager import settings_manager
from shared_toolbar import SharedToolBar
from cpu_optimizer import (get_optimized_terrain_query, get_optimized_mission_generator, 
                          get_optimized_waypoint_optimizer, create_optimized_progress_dialog)
# Import new aircraft parameter system
from aircraft_parameters import MissionToolBase
from aircraft_parameters.parameter_ui_component import ParameterAwareUIComponent


class TerrainQuery:
    """Class to fetch terrain elevation using OpenTopography API with rate limiting and caching."""
    def __init__(self):
        self.api_url = "https://api.opentopodata.org/v1/srtm90m"
        self.cache = {}  # Cache to store elevation data for coordinates
        self.rate_limit_delay = 2  # Increased delay in seconds for rate limiting
        self.max_retries = 3  # Reduced max retries
        self.last_request_time = 0  # Track last request time
        self.min_request_interval = 1.5  # Minimum seconds between requests

    def get_elevation(self, lat, lon):
        # Check if elevation is already cached
        cache_key = (round(lat, 4), round(lon, 4))  # Round to reduce cache misses
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Rate limiting - ensure minimum time between requests
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        retries = 0
        while retries < self.max_retries:
            try:
                self.last_request_time = time.time()
                response = requests.get(self.api_url, params={'locations': f"{lat},{lon}"}, timeout=10)
                
                if response.status_code == 429:  # Rate limit exceeded
                    retries += 1
                    if retries >= self.max_retries:
                        print(f"Rate limit exceeded for coordinates {lat}, {lon}. Using default elevation.")
                        self.cache[cache_key] = 0  # Cache default value
                        return 0
                    # Exponential backoff for rate limiting
                    wait_time = self.rate_limit_delay * (2 ** retries)
                    print(f"Rate limited. Waiting {wait_time} seconds before retry {retries + 1}")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                if "results" in data and data["results"]:
                    elevation = data["results"][0]["elevation"]
                    if elevation is not None:
                        self.cache[cache_key] = elevation
                        return elevation
                
                # If no elevation data, use default
                self.cache[cache_key] = 0
                return 0
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
                retries += 1
                if retries >= self.max_retries:
                    print(f"Failed to fetch elevation after {self.max_retries} attempts. Using default elevation.")
                    self.cache[cache_key] = 0
                    return 0
                time.sleep(self.rate_limit_delay)
        
        # Fallback to default elevation
        self.cache[cache_key] = 0
        return 0


class DeliveryRouteMapBridge(QObject):
    """Bridge class for QWebChannel communication."""
    
    @pyqtSlot(float, float)
    def setStartLocation(self, lat, lng):
        """Set start location from map click."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.set_start_location(lat, lng)
    
    @pyqtSlot(float, float)
    def setEndLocation(self, lat, lng):
        """Set end location from map click."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.set_end_location(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_takeoff_location(self, lat, lng):
        """Receive takeoff location from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_takeoff_location_selected(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_landing_location(self, lat, lng):
        """Receive landing location from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_landing_location_selected(lat, lng)
    
    @pyqtSlot()
    def onFlightPathCleared(self):
        """Handle flight path cleared event."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.on_flight_path_cleared()


class DeliveryRoute(MissionToolBase):
    """
    DeliveryRoute: UI and logic for the delivery route planning tool.
    """
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("delivery_route")
        self.mission_generator = get_optimized_mission_generator("delivery_route")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("delivery_route")
        
        # Initialize parameter UI component
        self.parameter_ui = ParameterAwareUIComponent()
        self.parameter_ui.parameter_usage_changed.connect(self.on_parameter_usage_changed)
        self.parameter_ui.parameter_file_loaded.connect(self.on_parameter_file_loaded)
        self.parameter_ui.parameter_file_error.connect(self.on_parameter_file_error)
        
        self.plan_file_path = None
        self.waypoints = []  # Placeholder for storing waypoints for visualization
        self.takeoff_point = None
        self.landing_point = None
        self.initUI()
        self.apply_qgc_theme()

    def initUI(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Delivery Route Planner")
        self.setGeometry(100, 100, 1200, 800)

        # Add shared toolbar
        self.toolbar = SharedToolBar(self)
        self.addToolBar(self.toolbar)

        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Left side: Map view and instructions
        left_layout = QtWidgets.QVBoxLayout()



        # Map View
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        from utils import get_map_html_path
        self.map_view.setUrl(QUrl.fromLocalFile(get_map_html_path()))
        
        # Set up communication channel for map interactions
        self.channel = QWebChannel()
        self.map_bridge = DeliveryRouteMapBridge()
        self.map_bridge.parent_widget = self
        self.channel.registerObject('pywebchannel', self.map_bridge)
        self.map_view.page().setWebChannel(self.channel)
        
        left_layout.addWidget(self.map_view)

        main_layout.addLayout(left_layout, 2)

        # Right side: Form input fields and buttons with scrollable area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Settings container
        settings_widget = QWidget()
        form_layout = QVBoxLayout(settings_widget)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Takeoff/Landing Configuration Group
        takeoff_landing_group = QGroupBox("Takeoff & Landing Configuration")
        takeoff_landing_layout = QVBoxLayout(takeoff_landing_group)
        
        # Takeoff location
        takeoff_landing_layout.addWidget(QLabel("Takeoff Location:"))
        self.takeoff_location_label = QLabel("Not set - Click 'Set Takeoff' and click on map")
        self.takeoff_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        takeoff_landing_layout.addWidget(self.takeoff_location_label)
        
        takeoff_btn_layout = QHBoxLayout()
        self.set_takeoff_btn = QPushButton("Set Takeoff")
        self.set_takeoff_btn.clicked.connect(self.start_takeoff_selection)
        takeoff_btn_layout.addWidget(self.set_takeoff_btn)
        
        self.clear_takeoff_btn = QPushButton("Clear")
        self.clear_takeoff_btn.clicked.connect(self.clear_takeoff_location)
        takeoff_btn_layout.addWidget(self.clear_takeoff_btn)
        takeoff_landing_layout.addLayout(takeoff_btn_layout)
        
        # Landing location
        takeoff_landing_layout.addWidget(QLabel("Landing Location:"))
        self.landing_location_label = QLabel("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        takeoff_landing_layout.addWidget(self.landing_location_label)
        
        landing_btn_layout = QHBoxLayout()
        self.set_landing_btn = QPushButton("Set Landing")
        self.set_landing_btn.clicked.connect(self.start_landing_selection)
        landing_btn_layout.addWidget(self.set_landing_btn)
        
        self.clear_landing_btn = QPushButton("Clear")
        self.clear_landing_btn.clicked.connect(self.clear_landing_location)
        landing_btn_layout.addWidget(self.clear_landing_btn)
        takeoff_landing_layout.addLayout(landing_btn_layout)
        
        form_layout.addWidget(takeoff_landing_group)

        
        # Aircraft Type Selection (fallback)
        form_layout.addWidget(QLabel("Select Aircraft Type:"))
        self.aircraft_type = QComboBox(self)
        self.aircraft_type.addItems(["Multicopter/Helicopter", "Fixed Wing", "Quadplane/VTOL Hybrid"])
        form_layout.addWidget(self.aircraft_type)
        
        # Add parameter UI component
        form_layout.addWidget(self.parameter_ui)

        # Altitude Above Terrain
        form_layout.addWidget(QLabel("Altitude Above Terrain:"))
        self.altitude = QtWidgets.QLineEdit(self)
        # Set default altitude from settings
        self.altitude.setText(str(settings_manager.get_default_altitude()))
        form_layout.addWidget(self.altitude)

        # Altitude Units
        self.altitude_units = QComboBox(self)
        self.altitude_units.addItems(["Feet", "Meters"])
        # Set default based on settings
        if settings_manager.is_metric():
            self.altitude_units.setCurrentText("Meters")
        else:
            self.altitude_units.setCurrentText("Feet")
        form_layout.addWidget(self.altitude_units)

        # Waypoint Interval
        form_layout.addWidget(QLabel("Waypoint Interval:"))
        self.interval = QtWidgets.QLineEdit(self)
        # Set default interval from settings
        self.interval.setText(str(settings_manager.get_default_interval()))
        form_layout.addWidget(self.interval)

        # Waypoint Interval Units
        self.interval_units = QComboBox(self)
        self.interval_units.addItems(["Meters", "Feet"])
        # Set default based on settings
        if settings_manager.is_metric():
            self.interval_units.setCurrentText("Meters")
        else:
            self.interval_units.setCurrentText("Feet")
        form_layout.addWidget(self.interval_units)

        # Geofence Buffer
        form_layout.addWidget(QLabel("Geofence Buffer:"))
        self.geofence_buffer = QtWidgets.QLineEdit(self)
        # Set default geofence buffer from settings
        self.geofence_buffer.setText(str(settings_manager.get_default_geofence_buffer()))
        form_layout.addWidget(self.geofence_buffer)

        # Geofence Units
        self.geofence_units = QComboBox(self)
        self.geofence_units.addItems(["Feet", "Meters"])
        # Set default based on settings
        if settings_manager.is_metric():
            self.geofence_units.setCurrentText("Meters")
        else:
            self.geofence_units.setCurrentText("Feet")
        form_layout.addWidget(self.geofence_units)

        # Landing Behavior at Point B
        form_layout.addWidget(QLabel("Landing Behavior at Point B:"))
        self.landing_behavior = QComboBox(self)
        self.landing_behavior.addItems(["Payload Mechanism", "Land and Takeoff When Commanded to Return"])
        form_layout.addWidget(self.landing_behavior)

        # Button to generate .plan file
        self.generate_btn = QtWidgets.QPushButton("Generate .plan File", self)
        self.generate_btn.clicked.connect(self.generate_plan)
        form_layout.addWidget(self.generate_btn)


        # Button to visualize flight path on map (initially disabled)
        self.visualize_path_btn = QtWidgets.QPushButton("Visualize Flight Path", self)
        self.visualize_path_btn.setEnabled(False)
        self.visualize_path_btn.clicked.connect(self.visualize_flight_path)
        form_layout.addWidget(self.visualize_path_btn)

        # Button to visualize altitude profile (initially disabled)
        self.visualize_btn = QtWidgets.QPushButton("Visualize Altitude Profile", self)
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self.visualize_altitude)
        form_layout.addWidget(self.visualize_btn)

        # Button to export flight path as KMZ/KML (initially disabled)
        self.export_btn = QtWidgets.QPushButton("Export Flight Path (KMZ/KML)", self)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_flight_path)
        form_layout.addWidget(self.export_btn)

        # Progress bar for generating .plan file
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)

        # Set up scroll area
        scroll.setWidget(settings_widget)
        right_layout.addWidget(scroll)
        
        main_layout.addWidget(right_panel, 1)
        # Remove setLayout call - QMainWindow already has central widget with layout

    def set_start_location(self, lat, lng):
        """Set the clicked location as the start coordinates."""
        self.start_coords.setText(f"{lat:.6f},{lng:.6f}")
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "Start Location Set", 
                              f"Start coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
                              f"Terrain Elevation:\n{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")
    
    def set_end_location(self, lat, lng):
        """Set the clicked location as the end coordinates."""
        self.end_coords.setText(f"{lat:.6f},{lng:.6f}")
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "End Location Set", 
                              f"End coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
                              f"Terrain Elevation:\n{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")

    def start_takeoff_selection(self):
        """Start takeoff location selection mode."""
        self.map_view.page().runJavaScript("startTakeoffSelection();")

    def start_landing_selection(self):
        """Start landing location selection mode."""
        self.map_view.page().runJavaScript("startLandingSelection();")

    def clear_takeoff_location(self):
        """Clear the takeoff location."""
        self.takeoff_point = None
        self.takeoff_location_label.setText("Not set - Click 'Set Takeoff' and click on map")
        self.takeoff_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.map_view.page().runJavaScript("clearTakeoffMarker();")

    def clear_landing_location(self):
        """Clear the landing location."""
        self.landing_point = None
        self.landing_location_label.setText("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.map_view.page().runJavaScript("clearLandingMarker();")

    def handle_takeoff_location_selected(self, lat, lng):
        """Handle takeoff location selection from map."""
        self.takeoff_point = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.takeoff_location_label.setText(f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.takeoff_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def handle_landing_location_selected(self, lat, lng):
        """Handle landing location selection from map."""
        self.landing_point = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.landing_location_label.setText(f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")


    
    def apply_qgc_theme(self):
        """Apply QGroundControl-inspired dark theme styling."""
        # Import the dark theme from Main
        from utils import get_dark_theme
        self.setStyleSheet(get_dark_theme())
        
        # Additional styling for this specific tool
        additional_style = """
        QLabel {
            color: white;
            font-size: 13px;
            font-weight: bold;
            margin-top: 8px;
        }
        QLineEdit, QComboBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
            margin-bottom: 8px;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #FFD700;
        }
        QPushButton {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: bold;
            margin: 4px 0px;
        }
        QPushButton:hover {
            background-color: #4C4C4C;
            border-color: #666666;
        }
        QPushButton:pressed {
            background-color: #2C2C2C;
        }
        QPushButton:disabled {
            background-color: #2C2C2C;
            color: #888888;
            border-color: #444444;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #2C2C2C;
            color: white;
            margin: 4px 0px;
        }
        QProgressBar::chunk {
            background-color: #FFD700;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(self.styleSheet() + additional_style)

    def parse_coordinates(self, coord_text):
        try:
            lat, lon = map(float, coord_text.split(','))
            return lat, lon
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in 'lat,lon' format.")
            return None, None

    def interpolate_waypoints(self, start, end, interval):
        """Use optimized waypoint interpolation"""
        return self.waypoint_optimizer.interpolate_waypoints_optimized(start, end, interval)

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def offset_waypoints(self, waypoints, offset_distance):
        offset_points = []
        bearings = [0, 90, 180, 270]

        for lat, lon in waypoints:
            for bearing in bearings:
                offset_point = geopy_distance(meters=offset_distance).destination((lat, lon), bearing)
                offset_points.append((offset_point.latitude, offset_point.longitude))
        return offset_points

    def generate_geofence(self, offset_points):
        points = MultiPoint([Point(lon, lat) for lat, lon in offset_points])
        hull = points.convex_hull
        return [[coord[1], coord[0]] for coord in hull.exterior.coords]

    def convert_to_meters(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def validate_numeric_input(self, text, field_name):
        try:
            value = float(text)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"Please enter a positive number for {field_name}.")
            return None

    def add_takeoff_command(self, mission_items, start_lat, start_lon, altitude_meters):
        aircraft_type = self.aircraft_type.currentText()
        terrain_elevation = self.terrain_query.get_elevation(start_lat, start_lon)
        amsl_altitude = terrain_elevation + altitude_meters
        
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "AMSLAltAboveTerrain": amsl_altitude,
                "Altitude": altitude_meters,
                "AltitudeMode": 3,
                "autoContinue": True,
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, start_lat, start_lon, amsl_altitude],
                "type": "SimpleItem"
            })
        elif aircraft_type == "Fixed Wing":
            mission_items.append({
                "AMSLAltAboveTerrain": amsl_altitude,
                "Altitude": altitude_meters,
                "AltitudeMode": 3,
                "autoContinue": True,
                "command": 22,  # TAKEOFF (Fixed Wing uses command 22 with frame 0)
                "doJumpId": 1,
                "frame": 0,
                "params": [15, 0, 0, None, start_lat, start_lon, amsl_altitude],
                "type": "SimpleItem"
            })
        elif aircraft_type == "Quadplane/VTOL Hybrid":
            mission_items.append({
                "AMSLAltAboveTerrain": amsl_altitude,
                "Altitude": altitude_meters,
                "AltitudeMode": 3,
                "autoContinue": True,
                "command": 84,  # VTOL TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, start_lat, start_lon, amsl_altitude],
                "type": "SimpleItem"
            })

    def add_waypoint_command(self, mission_items, index, lat, lon, altitude_meters):
        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = terrain_elevation + altitude_meters

        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,
            "Altitude": altitude_meters,
            "AltitudeMode": 3,
            "autoContinue": True,
            "command": 16,  # Waypoint command
            "doJumpId": index + 2,
            "frame": 0,
            "params": [0, 0, 0, None, lat, lon, amsl_altitude],
            "type": "SimpleItem"
        })

    def add_vtol_transition_command(self, mission_items, transition_mode):
        mission_items.append({
            "command": 3000,  # VTOL TRANSITION
            "doJumpId": len(mission_items) + 1,
            "frame": 2,
            "params": [transition_mode, 0, 0, 0, 0, 0, 0],
            "type": "SimpleItem",
            "autoContinue": True
        })

    def add_landing_or_loiter_command(self, mission_items, lat, lon, altitude_meters):
        aircraft_type = self.aircraft_type.currentText()
        landing_behavior = self.landing_behavior.currentText()

        if aircraft_type == "Multicopter/Helicopter":
            # For multicopters, handle based on landing behavior
            if landing_behavior == "Payload Mechanism":
                # Add a waypoint at delivery location for payload release
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude_meters
                mission_items.append({
                    "AMSLAltAboveTerrain": amsl_altitude,
                    "Altitude": altitude_meters,
                    "AltitudeMode": 3,
                    "autoContinue": True,
                    "command": 16,  # Waypoint
                    "doJumpId": len(mission_items) + 1,
                    "frame": 0,
                    "params": [0, 0, 0, None, lat, lon, amsl_altitude],
                    "type": "SimpleItem"
                })
                
                # Add gripper release command
                mission_items.append({
                    "autoContinue": True,
                    "command": 211,  # DO_GRIPPER (release payload)
                    "doJumpId": len(mission_items) + 1,
                    "frame": 0,
                    "params": [2, 0, 0, 0, 0, 0, 0],  # "2" assumes release action
                    "type": "SimpleItem"
                })
            else:
                # For "Land and Takeoff When Commanded to Return" - just add a waypoint
                # The actual landing command will be added separately in the main generation
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude_meters
                mission_items.append({
                    "AMSLAltAboveTerrain": amsl_altitude,
                    "Altitude": altitude_meters,
                    "AltitudeMode": 3,
                    "autoContinue": True,
                    "command": 16,  # Waypoint
                    "doJumpId": len(mission_items) + 1,
                    "frame": 0,
                    "params": [0, 0, 0, None, lat, lon, altitude_meters],
                    "type": "SimpleItem"
                })
        
        elif aircraft_type == "Fixed Wing":
            # For fixed wing, add a loiter pattern at delivery location
            loiter_altitude_meters = 6.096  # 20 feet in meters

            mission_items.append({
                "AMSLAltAboveTerrain": loiter_altitude_meters,
                "Altitude": loiter_altitude_meters,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 19,  # LOITER_UNLIMITED
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [10, 1, 50, 1, lat, lon, loiter_altitude_meters],
                "type": "SimpleItem"
            })

            # Add gripper release if using payload mechanism
            if landing_behavior == "Payload Mechanism":
                mission_items.append({
                    "autoContinue": True,
                    "command": 211,  # DO_GRIPPER (release payload)
                    "doJumpId": len(mission_items) + 1,
                    "frame": 0,
                    "params": [2, 0, 0, 0, 0, 0, 0],  # "2" assumes release action
                    "type": "SimpleItem"
                })
        
        elif aircraft_type == "Quadplane/VTOL Hybrid":
            # For VTOL, add a loiter at delivery location
            loiter_altitude_meters = 6.096  # 20 feet in meters
            
            mission_items.append({
                "AMSLAltAboveTerrain": loiter_altitude_meters,
                "Altitude": loiter_altitude_meters,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 19,  # LOITER_UNLIMITED
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [10, 1, 50, 1, lat, lon, loiter_altitude_meters],
                "type": "SimpleItem"
            })

            # Add gripper release if using payload mechanism
            if landing_behavior == "Payload Mechanism":
                mission_items.append({
                "autoContinue": True,
                "command": 211,  # DO_GRIPPER (release payload)
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [2, 0, 0, 0, 0, 0, 0],  # "2" assumes release action
                "type": "SimpleItem"
            })

    def add_fixed_wing_landing_pattern(self, mission_items, start_lat, start_lon, home_elevation, altitude_meters):
        """Add a fixed-wing landing pattern to the mission."""
        landing_approach_coord = [
            start_lat + 0.001,  # Adjust these values as needed
            start_lon + 0.001,
            home_elevation + altitude_meters  # Use user-defined altitude above terrain
        ]

        mission_items.append({
            "altitudesAreRelative": True,
            "complexItemType": "fwLandingPattern",
            "landCoordinate": [start_lat, start_lon, 0],
            "landingApproachCoordinate": landing_approach_coord,
            "loiterClockwise": True,
            "loiterRadius": 75,
            "stopTakingPhotos": True,
            "stopVideoPhotos": True,
            "type": "ComplexItem",
            "useLoiterToAlt": True,
            "valueSetIsDistance": False,
            "version": 2
        })

    def compile_plan_data(self, mission_items, geofence_coords, start_lat, start_lon, home_elevation):
        # Get aircraft-specific parameters using new system
        if self.parameter_ui.is_parameter_aware_enabled():
            aircraft_info = self.parameter_ui.get_aircraft_info_for_export()
        else:
            aircraft_info = self.get_aircraft_info_for_export()
        
        return {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [{"polygon": geofence_coords, "inclusion": True, "version": 1}],
                "version": 2
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": aircraft_info["cruiseSpeed"],
                "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                "globalPlanAltitudeMode": 0,
                "hoverSpeed": aircraft_info["hoverSpeed"],
                "items": mission_items,
                "plannedHomePosition": [start_lat, start_lon, home_elevation],
                "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                "version": 2
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QtWidgets.QApplication.processEvents()

    def generate_plan(self):
        # Validate takeoff and landing coordinates
        if not self.takeoff_point or not self.landing_point:
            QMessageBox.warning(self, "Missing Coordinates", "Please set both takeoff and landing locations using the map.")
            return
        
        start_lat, start_lon = self.takeoff_point["lat"], self.takeoff_point["lng"]
        end_lat, end_lon = self.landing_point["lat"], self.landing_point["lng"]

        # Use optimized progress dialog
        progress_dialog = create_optimized_progress_dialog("Generating Delivery Route", self)
        progress_dialog.show()

        # Get terrain elevation efficiently
        home_elevation = self.terrain_query.get_elevation(start_lat, start_lon)

        # Get aircraft-aware values
        if self.parameter_ui.is_parameter_aware_enabled():
            # Use aircraft parameters for optimized values
            mission_settings = self.parameter_ui.get_mission_settings()
            characteristics = self.parameter_ui.get_aircraft_characteristics()
            
            # Use parameter-aware altitude
            altitude_meters = self.get_aircraft_aware_altitude("delivery", 
                self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText()))
            
            # Use parameter-aware waypoint spacing
            interval_meters = self.get_aircraft_aware_waypoint_spacing("delivery", 
                self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText()))
            
            # Use parameter-aware geofence buffer
            geofence_buffer_meters = self.convert_to_meters(
                self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), 
                self.geofence_units.currentText())
            
            # Override aircraft type with detected type if available
            detected_aircraft_type = characteristics.get('aircraft_type', 'Unknown')
            if detected_aircraft_type != 'Unknown':
                aircraft_type = self._map_aircraft_type_to_ui(detected_aircraft_type)
            else:
                aircraft_type = self.aircraft_type.currentText()
                
        elif self.is_parameters_enabled():
            # Use legacy aircraft parameters for optimized values
            altitude_meters = self.get_aircraft_aware_altitude("delivery", 
                self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText()))
            interval_meters = self.get_aircraft_aware_waypoint_spacing("delivery", 
                self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText()))
            geofence_buffer_meters = self.convert_to_meters(
                self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), 
                self.geofence_units.currentText())
            aircraft_type = self.aircraft_type.currentText()
        else:
            # Use manual input values
            altitude_meters = self.validate_numeric_input(self.altitude.text(), "Altitude")
            interval_meters = self.validate_numeric_input(self.interval.text(), "Waypoint Interval")
            geofence_buffer_meters = self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer")
            if None in (altitude_meters, interval_meters, geofence_buffer_meters):
                progress_dialog.close()
        
        # Auto-visualize flight path after successful generation
        if self.waypoints:
            self.auto_visualize_flight_path()
                return

            altitude_meters = self.convert_to_meters(altitude_meters, self.altitude_units.currentText())
            interval_meters = self.convert_to_meters(interval_meters, self.interval_units.currentText())
            geofence_buffer_meters = self.convert_to_meters(geofence_buffer_meters, self.geofence_units.currentText())
            aircraft_type = self.aircraft_type.currentText()

        progress_dialog.update_with_stats(5, "Generating waypoints")
        self.waypoints = self.interpolate_waypoints((start_lat, start_lon), (end_lat, end_lon), interval_meters)
        mission_items = []

        progress_dialog.update_with_stats(10, "Generating geofence")
        offset_points = self.offset_waypoints(self.waypoints, geofence_buffer_meters)
        geofence_coords = self.generate_geofence(offset_points)

        aircraft_type = self.aircraft_type.currentText()
        landing_behavior = self.landing_behavior.currentText()

        # **1️⃣ Takeoff**
        progress_dialog.update_with_stats(15, "Adding takeoff command")
        self.add_takeoff_command(mission_items, start_lat, start_lon, altitude_meters)

        # **2️⃣ Outbound Waypoints (STOP before final delivery) - Use parallel processing**
        progress_dialog.update_with_stats(20, "Generating outbound waypoints")
        
        # Prepare waypoint data for parallel processing
        outbound_waypoints = self.waypoints[:-1]  # Exclude last delivery point for now
        waypoint_data = [(i + 1, lat, lon, altitude_meters) for i, (lat, lon) in enumerate(outbound_waypoints)]
        
        # Generate waypoints in parallel
        def progress_callback(progress):
            progress_dialog.update_with_stats(20 + int(progress * 0.25), "Processing outbound waypoints")
        
        parallel_waypoints = self.mission_generator.generate_mission_parallel(
            [(lat, lon) for _, lat, lon, _ in waypoint_data], 
            altitude_meters, 
            progress_callback
        )
        
        # Add waypoints to mission items
        for i, waypoint in enumerate(parallel_waypoints):
            waypoint["doJumpId"] = i + 2  # Start from 2 (after takeoff)
            mission_items.append(waypoint)

        # **3️⃣ Delivery Handling**
        progress_dialog.update_with_stats(45, "Configuring delivery sequence")
        final_lat, final_lon = self.waypoints[-1]

        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition to Multirotor Before Delivery**
            self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)

        # **Loiter at Delivery Waypoint (20 feet altitude)**
        self.add_landing_or_loiter_command(mission_items, final_lat, final_lon, altitude_meters)

        # **Payload Mechanism or Landing Behavior**
        if landing_behavior == "Land and Takeoff When Commanded to Return":
            if aircraft_type == "Multicopter/Helicopter":
                # **Land at Point B for multicopter**
                mission_items.append({
                    "AMSLAltAboveTerrain": None,
                    "Altitude": 0,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 21,  # LAND
                    "doJumpId": len(mission_items) + 1,
                    "frame": 3,
                    "params": [0, 0, 0, None, final_lat, final_lon, 0],
                    "type": "SimpleItem"
                })
            elif aircraft_type == "Fixed Wing":
                # **Land at Point B for fixed wing**
                mission_items.append({
                    "AMSLAltAboveTerrain": None,
                    "Altitude": 0,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 21,  # LAND
                    "doJumpId": len(mission_items) + 1,
                    "frame": 3,
                    "params": [0, 0, 0, None, final_lat, final_lon, 0],
                    "type": "SimpleItem"
                })
            elif aircraft_type == "Quadplane/VTOL Hybrid":
                # **Land at Point B for VTOL**
                mission_items.append({
                    "AMSLAltAboveTerrain": None,
                    "Altitude": 0,
                    "AltitudeMode": 1,
                    "autoContinue": True,
                    "command": 21,  # LAND
                    "doJumpId": len(mission_items) + 1,
                    "frame": 3,
                    "params": [0, 0, 0, None, final_lat, final_lon, 0],
                    "type": "SimpleItem"
                })

        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition Back to Fixed-Wing After Drop**
            self.add_vtol_transition_command(mission_items, 4)  # Transition to Fixed-Wing (mode 4)

        # **4️⃣ Return Waypoints (Back to Home) - Use parallel processing**
        progress_dialog.update_with_stats(50, "Generating return waypoints")
        
        # Prepare return waypoint data
        return_waypoints = list(reversed(self.waypoints[:-1]))  # Reverse outbound waypoints without last point
        
        def return_progress_callback(progress):
            progress_dialog.update_with_stats(50 + int(progress * 0.25), "Processing return waypoints")
        
        parallel_return_waypoints = self.mission_generator.generate_mission_parallel(
            return_waypoints, 
            altitude_meters, 
            return_progress_callback
        )
        
        # Add return waypoints to mission items
        for i, waypoint in enumerate(parallel_return_waypoints):
            waypoint["doJumpId"] = len(mission_items) + 1
            mission_items.append(waypoint)

        # **5️⃣ Landing at Home**
        progress_dialog.update_with_stats(75, "Configuring landing sequence")
        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition to Multirotor for Landing**
            self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)

            # **Land at Home**
            mission_items.append({
                "AMSLAltAboveTerrain": 0,
                "Altitude": 0,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 85,  # VTOL Land
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [0, 0, 0, 0, start_lat, start_lon, 0],
                "type": "SimpleItem"
            })
        elif aircraft_type == "Fixed Wing":
            # **Add Fixed-Wing Landing Pattern**
            self.add_fixed_wing_landing_pattern(mission_items, start_lat, start_lon, home_elevation, altitude_meters)
        else:
            # **Multicopter/Helicopter - Add simple landing command**
            mission_items.append({
                "AMSLAltAboveTerrain": None,
                "Altitude": 0,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 21,  # LAND
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, 0],
                "type": "SimpleItem"
            })

        # Compile the plan data
        progress_dialog.update_with_stats(85, "Compiling mission data")
        plan_data = self.compile_plan_data(mission_items, geofence_coords, start_lat, start_lon, home_elevation)

        # Save the plan file using new file generation system
        progress_dialog.update_with_stats(90, "Saving mission file")
        saved_file = self.save_mission_file(plan_data, "delivery_route")
        if saved_file:
            self.plan_file_path = saved_file
            self.visualize_btn.setEnabled(True)
            self.visualize_path_btn.setEnabled(True)
            self.export_btn.setEnabled(True)

        # Enable toolbar actions
        progress_dialog.update_with_stats(95, "Finalizing mission")
        self.toolbar.enable_actions(True)

        # Check for terrain proximity warnings
        altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
        proximity_warnings = self.check_terrain_proximity(altitude_meters)
        
        if proximity_warnings:
            self.show_terrain_proximity_warning(proximity_warnings)
        
        # Show completion statistics and close progress dialog
        progress_dialog.update_with_stats(100, "Complete")
        progress_dialog.show_completion_stats()
        progress_dialog.close()
        
        # Auto-visualize flight path after successful generation
        if self.waypoints:
            self.auto_visualize_flight_path()

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters and user's preferred units
        altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
        is_metric = settings_manager.is_metric()
        
        # Convert to display units
        if is_metric:
            altitude_display = altitude_meters
            unit_label = "meters"
            distance_unit = "meters"
        else:
            altitude_display = altitude_meters * 3.28084  # Convert to feet
            unit_label = "feet"
            distance_unit = "feet"
        
        # Calculate total distance
        total_distance_meters = self.haversine_distance(
            self.waypoints[0][0], self.waypoints[0][1], 
            self.waypoints[-1][0], self.waypoints[-1][1]
        )
        
        if is_metric:
            total_distance_display = total_distance_meters
        else:
            total_distance_display = total_distance_meters * 3.28084  # Convert to feet
        
        # Get terrain elevation data for all waypoints
        terrain_elevations = []
        amsl_altitudes = []
        agl_altitudes = []
        
        for lat, lon in self.waypoints:
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            terrain_elevations.append(terrain_elevation)
            
            # Calculate AMSL altitude (terrain + AGL)
            amsl_altitude = terrain_elevation + altitude_meters
            amsl_altitudes.append(amsl_altitude)
            agl_altitudes.append(altitude_meters)
        
        # Convert to display units if imperial
        if not is_metric:
            terrain_elevations = [elev * 3.28084 for elev in terrain_elevations]
            amsl_altitudes = [alt * 3.28084 for alt in amsl_altitudes]
            agl_altitudes = [alt * 3.28084 for alt in agl_altitudes]
        
        # Create matplotlib visualization
        plt.figure(figsize=(12, 10))
        
        # Plot altitude profile with terrain
        waypoint_indices = list(range(len(self.waypoints)))
        
        plt.subplot(2, 1, 1)
        plt.plot(waypoint_indices, amsl_altitudes, 'b-', linewidth=2, label=f'AMSL Altitude ({unit_label})')
        plt.plot(waypoint_indices, terrain_elevations, 'g-', linewidth=2, label=f'Terrain Elevation ({unit_label})')
        plt.plot(waypoint_indices, agl_altitudes, 'r--', linewidth=2, label=f'AGL Altitude ({unit_label})')
        plt.xlabel('Waypoint Index')
        plt.ylabel(f'Altitude ({unit_label})')
        plt.title('Flight Altitude Profile with Terrain')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Fill area between AMSL and terrain to show flight corridor
        plt.fill_between(waypoint_indices, terrain_elevations, amsl_altitudes, alpha=0.2, color='blue', label='Flight Corridor')
        
        # Add statistics text
        plt.subplot(2, 1, 2)
        plt.axis('off')
        
        # Calculate statistics
        min_terrain = min(terrain_elevations)
        max_terrain = max(terrain_elevations)
        avg_terrain = sum(terrain_elevations) / len(terrain_elevations)
        min_amsl = min(amsl_altitudes)
        max_amsl = max(amsl_altitudes)
        avg_amsl = sum(amsl_altitudes) / len(amsl_altitudes)
        
        stats_text = f"""Altitude Profile Summary with Terrain
=====================================

Total Waypoints: {len(self.waypoints)}
AGL Altitude: {altitude_display:.1f} {unit_label}

Terrain Elevation Statistics:
- Minimum: {min_terrain:.1f} {unit_label}
- Maximum: {max_terrain:.1f} {unit_label}
- Average: {avg_terrain:.1f} {unit_label}
- Range: {max_terrain - min_terrain:.1f} {unit_label}

AMSL Altitude Statistics:
- Minimum: {min_amsl:.1f} {unit_label}
- Maximum: {max_amsl:.1f} {unit_label}
- Average: {avg_amsl:.1f} {unit_label}
- Range: {max_amsl - min_amsl:.1f} {unit_label}

Flight Plan Summary:
- Start Point: {self.waypoints[0] if self.waypoints else 'N/A'}
- End Point: {self.waypoints[-1] if self.waypoints else 'N/A'}
- Total Distance: {total_distance_display:.1f} {distance_unit}

All waypoints will fly at {altitude_display:.1f} {unit_label} AGL.

Settings: {settings_manager.get_unit_system().title()} Units
"""
        
        plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes, 
                fontsize=10, verticalalignment='top', fontfamily='monospace')
        
        plt.tight_layout()
        
        # Save the plot to a temporary file and open it
        import tempfile
        import os
        import subprocess
        
        # Create a temporary file for the plot
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=300, bbox_inches='tight')
        plt.close()  # Close the figure to free memory
        
        # Open the saved image with the default image viewer
        try:
            if os.name == 'nt':  # Windows
                os.startfile(temp_file.name)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', temp_file.name])
        except Exception as e:
            QMessageBox.information(self, "Plot Saved", 
                                  f"Altitude profile saved to:\n{temp_file.name}\n\nError opening viewer: {e}")

    def check_terrain_proximity(self, altitude_meters):
        """Check if any waypoint gets too close to terrain (within 50ft/15.24m)"""
        proximity_warnings = []
        warning_threshold = 15.24  # 50 feet in meters
        
        for i, (lat, lon) in enumerate(self.waypoints):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            clearance = altitude_meters - terrain_elevation
            
            if clearance < warning_threshold:
                proximity_warnings.append({
                    'waypoint': i + 1,
                    'lat': lat,
                    'lon': lon,
                    'terrain_elevation': terrain_elevation,
                    'clearance': clearance,
                    'altitude_agl': altitude_meters
                })
        
        return proximity_warnings

    def show_terrain_proximity_warning(self, warnings):
        """Show warning dialog for terrain proximity issues"""
        if not warnings:
            return
        
        warning_text = "⚠️ TERRAIN PROXIMITY WARNING ⚠️\n\n"
        warning_text += f"Found {len(warnings)} waypoint(s) with terrain clearance less than 50ft (15.24m):\n\n"
        
        for warning in warnings:
            warning_text += f"Waypoint {warning['waypoint']}:\n"
            warning_text += f"  Coordinates: {warning['lat']:.6f}, {warning['lon']:.6f}\n"
            warning_text += f"  Terrain Elevation: {warning['terrain_elevation']:.1f}m\n"
            warning_text += f"  AGL Altitude: {warning['altitude_agl']:.1f}m\n"
            warning_text += f"  Clearance: {warning['clearance']:.1f}m\n\n"
        
        warning_text += "⚠️ RECOMMENDATION: Increase AGL altitude or adjust flight path to ensure safe terrain clearance."
        
        QMessageBox.warning(self, "Terrain Proximity Warning", warning_text)

    def export_flight_path(self):
        """Export flight path as KMZ/KML file"""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for export.")
            return
        
        try:
            # Get file save dialog
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Flight Path", 
                "", 
                "KMZ Files (*.kmz);;KML Files (*.kml)"
            )
            
            if not filename:
                return
            
            # Get altitude data
            altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
            
            # Create KML content
            kml_content = self.generate_kml_content(altitude_meters)
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            QMessageBox.information(self, "Export Successful", 
                                  f"Flight path exported to:\n{filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error exporting flight path: {str(e)}")

    def generate_kml_content(self, altitude_meters):
        """Generate KML content for the flight path"""
        # Get terrain data for all waypoints
        waypoint_data = []
        for i, (lat, lon) in enumerate(self.waypoints):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            amsl_altitude = terrain_elevation + altitude_meters
            waypoint_data.append({
                'lat': lat,
                'lon': lon,
                'terrain_elevation': terrain_elevation,
                'amsl_altitude': amsl_altitude,
                'agl_altitude': altitude_meters,
                'waypoint_number': i + 1
            })
        
        # Generate KML content
        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>AutoFlightGenerator Flight Path</name>
    <description>Flight path generated by AutoFlightGenerator</description>
    
    <!-- Flight Path Line -->
    <Placemark>
      <name>Flight Path</name>
      <description>Flight path with terrain following</description>
      <Style>
        <LineStyle>
          <color>ff0000ff</color>
          <width>4</width>
        </LineStyle>
      </Style>
      <LineString>
        <coordinates>
"""
        
        # Add coordinates for flight path
        for wp in waypoint_data:
            kml_content += f"          {wp['lon']:.6f},{wp['lat']:.6f},{wp['amsl_altitude']:.1f}\n"
        
        kml_content += """        </coordinates>
      </LineString>
    </Placemark>
    
    <!-- Waypoint Markers -->
"""
        
        # Add waypoint markers
        for wp in waypoint_data:
            kml_content += f"""    <Placemark>
      <name>Waypoint {wp['waypoint_number']}</name>
      <description>
        Coordinates: {wp['lat']:.6f}, {wp['lon']:.6f}
        Terrain Elevation: {wp['terrain_elevation']:.1f}m
        AMSL Altitude: {wp['amsl_altitude']:.1f}m
        AGL Altitude: {wp['agl_altitude']:.1f}m
      </description>
      <Style>
        <IconStyle>
          <color>ff00ff00</color>
          <scale>1.0</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{wp['lon']:.6f},{wp['lat']:.6f},{wp['amsl_altitude']:.1f}</coordinates>
      </Point>
    </Placemark>
"""
        
        # Add takeoff and landing points
        if waypoint_data:
            # Takeoff point
            first_wp = waypoint_data[0]
            kml_content += f"""    <Placemark>
      <name>Takeoff Point</name>
      <description>
        Takeoff location
        Coordinates: {first_wp['lat']:.6f}, {first_wp['lon']:.6f}
        Terrain Elevation: {first_wp['terrain_elevation']:.1f}m
        AMSL Altitude: {first_wp['amsl_altitude']:.1f}m
      </description>
      <Style>
        <IconStyle>
          <color>ff0000ff</color>
          <scale>1.5</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{first_wp['lon']:.6f},{first_wp['lat']:.6f},{first_wp['amsl_altitude']:.1f}</coordinates>
      </Point>
    </Placemark>
"""
            
            # Landing point
            last_wp = waypoint_data[-1]
            kml_content += f"""    <Placemark>
      <name>Landing Point</name>
      <description>
        Landing location
        Coordinates: {last_wp['lat']:.6f}, {last_wp['lon']:.6f}
        Terrain Elevation: {last_wp['terrain_elevation']:.1f}m
      </description>
      <Style>
        <IconStyle>
          <color>ffff0000</color>
          <scale>1.5</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{last_wp['lon']:.6f},{last_wp['lat']:.6f},{last_wp['terrain_elevation']:.1f}</coordinates>
      </Point>
    </Placemark>
"""
        
        kml_content += """  </Document>
</kml>"""
        
        return kml_content


    
    def on_flight_path_cleared(self):
        """Called when flight path is cleared on the map"""
        self.waypoints = []
        self.visualize_path_btn.setEnabled(False)
        self.visualize_btn.setEnabled(False)

        self.export_btn.setEnabled(False)
    
    def visualize_flight_path(self):
        """Visualize the flight path on the map"""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return
        
        try:
            # Prepare flight plan data for visualization
            flight_plan_data = {
                "waypoints": []
            }
            
            # Add takeoff point
            if self.waypoints:
                flight_plan_data["waypoints"].append({
                    "lat": self.waypoints[0][0],
                    "lng": self.waypoints[0][1],
                    "altitude": self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText()),
                    "title": "Takeoff"
                })
            
            # Add waypoints
            for i, (lat, lon) in enumerate(self.waypoints):
                flight_plan_data["waypoints"].append({
                    "lat": lat,
                    "lng": lon,
                    "altitude": self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText()),
                    "title": f"Waypoint {i+1}"
                })
            
            # Add landing point (same as last waypoint)
            if self.waypoints:
                flight_plan_data["waypoints"].append({
                    "lat": self.waypoints[-1][0],
                    "lng": self.waypoints[-1][1],
                    "altitude": 0,  # Landing altitude
                    "title": "Landing"
                })
            
            # Convert to JSON for JavaScript
            import json
            flight_plan_json = json.dumps(flight_plan_data)
            
            # Call JavaScript function to visualize flight plan
            js_code = f"visualizeFlightPlan({flight_plan_json});"
            self.map_view.page().runJavaScript(js_code)
            
            QMessageBox.information(self, "Flight Path Visualized", 
                                  f"Flight path with {len(self.waypoints)} waypoints has been visualized on the map.")
            
        except Exception as e:
            QMessageBox.warning(self, "Visualization Error", f"Error visualizing flight path: {str(e)}")
    
    
    def apply_settings(self):
        """Apply updated settings to the form"""
        # Update unit selections based on current settings
        if settings_manager.is_metric():
            self.altitude_units.setCurrentText("Meters")
            self.interval_units.setCurrentText("Meters")
            self.geofence_units.setCurrentText("Meters")
        else:
            self.altitude_units.setCurrentText("Feet")
            self.interval_units.setCurrentText("Feet")
            self.geofence_units.setCurrentText("Feet")
        
        # Update default values
        self.altitude.setText(str(settings_manager.get_default_altitude()))
        self.interval.setText(str(settings_manager.get_default_interval()))
        self.geofence_buffer.setText(str(settings_manager.get_default_geofence_buffer()))
    
    # Aircraft Configuration Methods
    
    def on_parameter_usage_changed(self, enabled: bool):
        """Handle parameter usage toggle"""
        self.set_parameter_usage(enabled)
    
    def on_parameter_file_loaded(self, filename: str, aircraft_type: str):
        """Handle parameter file loaded"""
        print(f"Parameter file loaded: {filename} for {aircraft_type}")
    
    def on_parameter_file_error(self, error_message: str):
        """Handle parameter file error"""
        print(f"Parameter file error: {error_message}")
    
    def _map_aircraft_type_to_ui(self, detected_type: str) -> str:
        """Map detected aircraft type to UI combo box options"""
        if detected_type == 'Multicopter':
            return "Multicopter/Helicopter"
        elif detected_type == 'FixedWing':
            return "Fixed Wing"
        elif detected_type == 'VTOL':
            return "Quadplane/VTOL Hybrid"
        else:
            return "Multicopter/Helicopter"  # Default fallback


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = DeliveryRoute()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()