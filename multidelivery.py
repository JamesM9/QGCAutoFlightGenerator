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
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout, QLineEdit, QListWidget, QHBoxLayout, QGroupBox, QWidget, QTextEdit, QScrollArea, QGridLayout, QSplitter
from PyQt5.QtCore import QUrl, Qt, QObject, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from geopy.distance import distance as geopy_distance
from settings_manager import settings_manager
from shared_toolbar import SharedToolBar
from cpu_optimizer import (get_optimized_terrain_query, get_optimized_mission_generator, 
                          get_optimized_waypoint_optimizer, create_optimized_progress_dialog)
# Import new aircraft parameter system
from aircraft_parameters import MissionToolBase


class TerrainQuery:
    """Class to fetch terrain elevation using OpenTopography API."""
    def __init__(self):
        self.api_url = "https://api.opentopodata.org/v1/srtm90m"

    def get_elevation(self, lat, lon):
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(self.api_url, params={'locations': f"{lat},{lon}"}, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if "results" in data and data["results"]:
                        elevation = data["results"][0]["elevation"]
                        return elevation if elevation is not None else 0
                elif response.status_code == 429:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0


class MultiDeliveryMapBridge(QObject):
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


class MultiDelivery(MissionToolBase):
    """
    MultiDelivery: UI and logic for the multi-delivery mission planning tool.
    """
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("multi_delivery")
        self.mission_generator = get_optimized_mission_generator("multi_delivery")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("multi_delivery")
        
        self.plan_file_path = None
        self.delivery_points = []  # To store delivery locations
        self.takeoff_point = None
        self.landing_point = None
        self.initUI()
        self.apply_qgc_theme()

    def initUI(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Multiple Delivery Mission Planner")
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
        self.map_bridge = MultiDeliveryMapBridge()
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


        # Delivery Points Section
        form_layout.addWidget(QLabel("Add Delivery Coordinates (lat,lon):"))
        delivery_input_layout = QHBoxLayout()
        self.delivery_coords_input = QLineEdit(self)
        self.add_delivery_btn = QPushButton("Add Delivery Point")
        self.add_delivery_btn.clicked.connect(self.add_delivery_point)
        delivery_input_layout.addWidget(self.delivery_coords_input)
        delivery_input_layout.addWidget(self.add_delivery_btn)
        form_layout.addLayout(delivery_input_layout)

        # List of delivery points
        self.delivery_points_list = QListWidget()
        self.delivery_points_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        form_layout.addWidget(self.delivery_points_list)

        # Aircraft Type Selection
        form_layout.addWidget(QLabel("Select Aircraft Type:"))
        self.aircraft_type = QComboBox(self)
        self.aircraft_type.addItems(["Multicopter/Helicopter", "Fixed Wing", "VTOL/Fixed Wing Hybrid"])
        form_layout.addWidget(self.aircraft_type)

        # Altitude Above Terrain
        form_layout.addWidget(QLabel("Altitude Above Terrain:"))
        self.altitude = QLineEdit(self)
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
        self.interval = QLineEdit(self)
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
        self.geofence_buffer = QLineEdit(self)
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

        # Delivery Action Selection
        form_layout.addWidget(QLabel("Delivery Action:"))
        self.delivery_action = QComboBox(self)
        self.delivery_action.addItems(["Release Mechanism", "Land at Delivery Location"])
        form_layout.addWidget(self.delivery_action)

        # Final Action Selection
        form_layout.addWidget(QLabel("Final Action:"))
        self.final_action = QComboBox(self)
        self.final_action.addItems(["Land at Final Delivery Location", "Return to Takeoff Location"])
        form_layout.addWidget(self.final_action)

        # Button to generate .plan file
        self.generate_btn = QPushButton("Generate .plan File", self)
        self.generate_btn.clicked.connect(self.generate_plan)
        form_layout.addWidget(self.generate_btn)

        # Button to visualize altitude profile (initially disabled)
        self.visualize_btn = QPushButton("Visualize Altitude Profile", self)
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self.visualize_altitude)
        form_layout.addWidget(self.visualize_btn)

        # Progress bar for generating .plan file
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)

        # Set up scroll area
        scroll.setWidget(settings_widget)
        right_layout.addWidget(scroll)
        
        main_layout.addWidget(right_panel, 1)
        self.setLayout(main_layout)

        self.waypoints = []  # Placeholder for storing waypoints for visualization

    def set_start_location(self, lat, lng):
        """Set the clicked location as the start coordinates."""
        coordinates = f"{lat:.6f},{lng:.6f}"
        self.start_coords.setText(coordinates)
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "Start Location Set", 
                              f"Start coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
                              f"Terrain Elevation:\n{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")
    
    def set_end_location(self, lat, lng):
        """Set the clicked location as a delivery point."""
        coordinates = f"{lat:.6f},{lng:.6f}"
        self.delivery_coords_input.setText(coordinates)
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "Delivery Location Set", 
                              f"Delivery coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
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
        try:
            self.takeoff_point = {"lat": lat, "lng": lng}
            
            # Try to get terrain elevation, but don't crash if it fails
            try:
                terrain_elevation = self.terrain_query.get_elevation(lat, lng)
                elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
            except Exception as e:
                # If elevation query fails, still set the location but without elevation info
                print(f"Warning: Could not get elevation for takeoff location: {e}")
                elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
            
            self.takeoff_location_label.setText(elevation_text)
            self.takeoff_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        except Exception as e:
            # Catch any other unexpected errors to prevent crash
            print(f"Error handling takeoff location selection: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self, 
                "Error Setting Takeoff Location", 
                f"An error occurred while setting the takeoff location:\n{str(e)}\n\nCoordinates: {lat:.6f}, {lng:.6f}"
            )

    def handle_landing_location_selected(self, lat, lng):
        """Handle landing location selection from map."""
        try:
            self.landing_point = {"lat": lat, "lng": lng}
            
            # Try to get terrain elevation, but don't crash if it fails
            try:
                terrain_elevation = self.terrain_query.get_elevation(lat, lng)
                elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
            except Exception as e:
                # If elevation query fails, still set the location but without elevation info
                print(f"Warning: Could not get elevation for landing location: {e}")
                elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
            
            self.landing_location_label.setText(elevation_text)
            self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        except Exception as e:
            # Catch any other unexpected errors to prevent crash
            print(f"Error handling landing location selection: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self, 
                "Error Setting Landing Location", 
                f"An error occurred while setting the landing location:\n{str(e)}\n\nCoordinates: {lat:.6f}, {lng:.6f}"
            )


    
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
        QListWidget {
            background-color: #2C2C2C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
        }
        QListWidget::item {
            padding: 6px 8px;
            border-bottom: 1px solid #3C3C3C;
        }
        QListWidget::item:selected {
            background-color: #FFD700;
            color: #1E1E1E;
        }
        QListWidget::item:hover {
            background-color: #3C3C3C;
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

    def add_delivery_point(self):
        """Adds a delivery location to the list."""
        lat, lon = self.parse_coordinates(self.delivery_coords_input.text())
        if lat is not None and lon is not None:
            self.delivery_points.append((lat, lon))
            self.delivery_points_list.addItem(f"{lat}, {lon}")
            self.delivery_coords_input.clear()



    def interpolate_waypoints(self, start, end, interval):
        """
        Generates interpolated waypoints between two geographic coordinates.

        Args:
            start (tuple): Starting coordinates as (latitude, longitude).
            end (tuple): Ending coordinates as (latitude, longitude).
            interval (float): Distance between waypoints in meters.

        Returns:
            list: List of interpolated waypoints as (latitude, longitude) tuples.
        """
        start_lat, start_lon = start
        end_lat, end_lon = end
        distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)

        # Calculate the number of waypoints needed
        num_points = max(int(distance // interval) + 1, 2)

        # Interpolate waypoints between start and end points
        latitudes = np.linspace(start_lat, end_lat, num_points)
        longitudes = np.linspace(start_lon, end_lon, num_points)
        return list(zip(latitudes, longitudes))

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculates the great-circle distance between two points on Earth.

        Args:
            lat1 (float): Latitude of the first point in decimal degrees.
            lon1 (float): Longitude of the first point in decimal degrees.
            lat2 (float): Latitude of the second point in decimal degrees.
            lon2 (float): Longitude of the second point in decimal degrees.

        Returns:
            float: Distance in meters.
        """
        R = 6371000  # Radius of Earth in meters
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)

        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def generate_geofence(self, waypoints, buffer_distance, extra_buffer_points, loiter_radius=None):
        """
        Generates a geofence around the flight path with additional buffer points for takeoff and landing.

        Args:
            waypoints (list): List of (latitude, longitude) tuples for the flight path.
            buffer_distance (float): Buffer distance in meters for the flight path.
            extra_buffer_points (list): List of (latitude, longitude) points for additional buffers (e.g., takeoff and landing).
            loiter_radius (float): Radius of the loiter waypoint in meters (optional).

        Returns:
            list: List of [longitude, latitude] pairs representing the geofence.
        """
        # Create a LineString from the waypoints
        line = LineString([(lon, lat) for lat, lon in waypoints])

        # Buffer the flight path
        buffered_area = line.buffer(buffer_distance / 111320.0, cap_style=2)  # Convert meters to degrees

        # Add buffers around extra points (e.g., takeoff and landing)
        extra_buffers = [Point(lon, lat).buffer(200 / 111320.0) for lat, lon in extra_buffer_points]  # 200 ft buffer

        # If a loiter radius is provided, add a buffer for the loiter area
        if loiter_radius is not None:
            # Add a buffer for the loiter waypoint
            loiter_buffer = Point(waypoints[-1][1], waypoints[-1][0]).buffer(loiter_radius / 111320.0)
            extra_buffers.append(loiter_buffer)

        # Combine all buffers
        combined_area = unary_union([buffered_area] + extra_buffers)

        # Extract the exterior of the combined polygon
        geofence_coords = list(combined_area.exterior.coords)

        # Convert back to [latitude, longitude] format
        return [[coord[1], coord[0]] for coord in geofence_coords]

    def add_takeoff_command(self, mission_items, start_lat, start_lon, altitude_meters):
        """Adds a takeoff command based on aircraft type."""
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "Fixed Wing":
            mission_items.append({
                "command": 22,  # FIXED_WING_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, start_lat, start_lon, altitude_meters],  # 15 m/s pitch
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "VTOL/Fixed Wing Hybrid":
            mission_items.append({
                "command": 84,  # VTOL_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })

    def add_waypoint_command(self, mission_items, index, lat, lon, altitude_meters):
        """Adds a waypoint command to the mission."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = elevation + altitude_meters
        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,
            "Altitude": altitude_meters,
            "AltitudeMode": 3,
            "autoContinue": True,
            "command": 16,
            "doJumpId": index + 2,
            "frame": 0,  # Use absolute altitude frame
            "params": [0, 0, 0, None, lat, lon, amsl_altitude],
            "type": "SimpleItem"
        })

    def add_loiter_command(self, mission_items, lat, lon, altitude_meters):
        """Adds a loiter command to the mission."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = elevation + altitude_meters
        mission_items.append({
            "autoContinue": True,
            "command": 183,  # LOITER_TO_ALT
            "doJumpId": len(mission_items) + 1,
            "frame": 2,
            "params": [1, 2000, 0, 0, 0, 0, 0],  # Loiter for 2000 seconds
            "type": "SimpleItem"
        })

    def add_landing_pattern(self, mission_items, land_lat, land_lon, approach_lat, approach_lon, altitude_meters):
        """Adds a fixed-wing landing pattern to the mission with dynamic distance offset."""
        # Calculate the distance offset based on altitude
        base_altitude_meters = 15.24  # 50 feet in meters
        base_distance_meters = 75  # Base distance offset at 50 feet
        altitude_difference = altitude_meters - base_altitude_meters
        distance_offset = base_distance_meters + (altitude_difference * (15 / 3.048))  # 15 meters per 10 feet

        # Ensure the distance offset is not too small
        distance_offset = max(distance_offset, 50)  # Minimum distance offset of 50 meters

        # Calculate the approach coordinates based on the distance offset
        approach_lat = land_lat + (distance_offset / 111320.0)  # 1 degree ≈ 111,320 meters
        approach_lon = land_lon + (distance_offset / (111320.0 * np.cos(np.radians(land_lat))))

        mission_items.append({
            "altitudesAreRelative": True,
            "complexItemType": "fwLandingPattern",
            "landCoordinate": [land_lat, land_lon, 0],
            "landingApproachCoordinate": [approach_lat, approach_lon, altitude_meters],
            "loiterClockwise": True,
            "loiterRadius": distance_offset,  # Use dynamic distance offset
            "stopTakingPhotos": True,
            "stopVideoPhotos": True,
            "type": "ComplexItem",
            "useLoiterToAlt": True,
            "valueSetIsDistance": False,
            "version": 2
        })

    def generate_plan(self):
        """Generates a flight plan for multiple delivery locations."""
        # Validate takeoff coordinates
        if not self.takeoff_point:
            QMessageBox.warning(self, "Missing Coordinates", "Please set the takeoff location using the map.")
            return
        
        start_lat, start_lon = self.takeoff_point["lat"], self.takeoff_point["lng"]

        # Get aircraft-aware values
        if self.is_parameters_enabled():
            # Use aircraft parameters for optimized values
            altitude_meters = self.get_aircraft_aware_altitude("delivery", 
                self.convert_units(float(self.altitude.text()), self.altitude_units.currentText()))
            interval_meters = self.get_aircraft_aware_waypoint_spacing("delivery", 
                self.convert_units(float(self.interval.text()), self.interval_units.currentText()))
            geofence_buffer_meters = self.convert_units(float(self.geofence_buffer.text()), self.geofence_units.currentText())
        else:
            # Use manual input values
            altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
            interval_meters = self.convert_units(float(self.interval.text()), self.interval_units.currentText())
            geofence_buffer_meters = self.convert_units(float(self.geofence_buffer.text()), self.geofence_units.currentText())
        mission_items = []

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.delivery_points) * 10 + 10)  # Approximation
        self.progress_bar.setValue(0)

        # Takeoff based on aircraft type
        self.add_takeoff_command(mission_items, start_lat, start_lon, altitude_meters)

        # Delivery points
        current_location = (start_lat, start_lon)
        all_waypoints = [current_location]
        for i, (lat, lon) in enumerate(self.delivery_points):
            waypoints = self.interpolate_waypoints(current_location, (lat, lon), interval_meters)
            all_waypoints.extend(waypoints)
            for waypoint_lat, waypoint_lon in waypoints:
                self.add_waypoint_command(mission_items, i, waypoint_lat, waypoint_lon, altitude_meters)
                self.progress_bar.setValue(self.progress_bar.value() + 1)

            # Add delivery-specific actions (Loiter, Gripper, or Land)
            self.add_delivery_action(mission_items, i, lat, lon, altitude_meters)
            current_location = (lat, lon)

        # Handle final action and geofence points
        extra_buffer_points = [(start_lat, start_lon)]  # Always include takeoff point
        if self.final_action.currentText() == "Return to Takeoff Location":
            # Interpolate return route
            waypoints = self.interpolate_waypoints(current_location, (start_lat, start_lon), interval_meters)
            all_waypoints.extend(waypoints)
            for waypoint_lat, waypoint_lon in waypoints:
                self.add_waypoint_command(mission_items, len(mission_items), waypoint_lat, waypoint_lon, altitude_meters)
                self.progress_bar.setValue(self.progress_bar.value() + 1)

            # Add loiter command before landing
            self.add_loiter_command(mission_items, start_lat, start_lon, altitude_meters)

            # Add landing based on aircraft type
            aircraft_type = self.aircraft_type.currentText()
            if aircraft_type == "Fixed Wing":
                # Add landing pattern with dynamic distance offset for fixed wing
                approach_lat = start_lat + 0.001  # Temporary value, will be recalculated
                approach_lon = start_lon + 0.001  # Temporary value, will be recalculated
                self.add_landing_pattern(mission_items, start_lat, start_lon, approach_lat, approach_lon, altitude_meters)
            else:
                # For multicopter and VTOL, add simple landing command
                self.add_landing_command(mission_items, start_lat, start_lon)

            # Generate geofence with loiter radius
            loiter_radius = self.calculate_loiter_radius(altitude_meters)
            geofence_coords = self.generate_geofence(all_waypoints, geofence_buffer_meters, extra_buffer_points, loiter_radius)
        else:
            # Add loiter command before landing
            self.add_loiter_command(mission_items, current_location[0], current_location[1], altitude_meters)

            # Add landing based on aircraft type
            aircraft_type = self.aircraft_type.currentText()
            if aircraft_type == "Fixed Wing":
                # Add landing pattern with dynamic distance offset for fixed wing
                approach_lat = current_location[0] + 0.001  # Temporary value, will be recalculated
                approach_lon = current_location[1] + 0.001  # Temporary value, will be recalculated
                self.add_landing_pattern(mission_items, current_location[0], current_location[1], approach_lat, approach_lon, altitude_meters)
            else:
                # For multicopter and VTOL, add simple landing command
                self.add_landing_command(mission_items, current_location[0], current_location[1])
            
            extra_buffer_points.append(current_location)  # Include final delivery point

            # Generate geofence with loiter radius
            loiter_radius = self.calculate_loiter_radius(altitude_meters)
            geofence_coords = self.generate_geofence(all_waypoints, geofence_buffer_meters, extra_buffer_points, loiter_radius)

        # Compile the plan data
        plan_data = self.compile_plan_data(mission_items, start_lat, start_lon, geofence_coords)

        # Save the plan file using new file generation system
        saved_file = self.save_mission_file(plan_data, "multi_delivery")
        if saved_file:
            self.plan_file_path = saved_file
            self.visualize_btn.setEnabled(True)

            # Enable toolbar actions
            self.toolbar.enable_actions(True)

        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Check for terrain proximity warnings
        proximity_warnings = self.check_terrain_proximity(altitude_meters)
        
        if proximity_warnings:
            self.show_terrain_proximity_warning(proximity_warnings)

    def add_delivery_action(self, mission_items, index, lat, lon, altitude_meters):
        """Adds delivery-specific actions (Loiter, Gripper, or Land)."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        loiter_altitude = self.convert_units(20, "Feet")  # 20 feet above terrain

        if self.delivery_action.currentText() == "Release Mechanism":
            # Loiter waypoint
            mission_items.append({
                "AMSLAltAboveTerrain": elevation + loiter_altitude,
                "Altitude": loiter_altitude,
                "AltitudeMode": 3,
                "autoContinue": False,
                "command": 19,  # LOITER_UNLIMITED
                "doJumpId": index + 3,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, elevation + loiter_altitude],
                "type": "SimpleItem"
            })

            # Gripper mechanism (package release)
            mission_items.append({
                "command": 211,  # DO_GRIPPER
                "doJumpId": index + 4,
                "frame": 3,
                "params": [2, 0, 0, 0, 0, 0, 0],  # Gripper release
                "type": "SimpleItem",
                "autoContinue": True
            })
        else:
            # Land at delivery location
            self.add_landing_command(mission_items, lat, lon)

            # Takeoff after landing
            self.add_takeoff_command(mission_items, lat, lon, altitude_meters)

    def add_landing_command(self, mission_items, lat, lon):
        """Adds a landing command based on aircraft type."""
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            command = 21  # LAND
        elif aircraft_type == "Fixed Wing":
            command = 21  # LAND
        elif aircraft_type == "VTOL/Fixed Wing Hybrid":
            command = 85  # VTOL_LAND

        mission_items.append({
            "command": command,
            "doJumpId": len(mission_items) + 1,
            "frame": 3,
            "params": [0, 0, 0, None, lat, lon, 0],
            "type": "SimpleItem",
            "autoContinue": True
        })

    def compile_plan_data(self, mission_items, start_lat, start_lon, geofence_coords):
        """Compiles the mission data into the .plan format."""
        # Get aircraft-specific parameters using new system
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
                "hoverSpeed": aircraft_info["hoverSpeed"],
                "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                "globalPlanAltitudeMode": 0,
                "items": mission_items,
                "plannedHomePosition": [start_lat, start_lon, 70],
                "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                "version": 2,
                "aircraftParameters": aircraft_info["aircraftParameters"]
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

    def convert_units(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def calculate_loiter_radius(self, altitude_meters):
        """Calculates the loiter radius based on altitude."""
        base_altitude_meters = 15.24  # 50 feet in meters
        base_radius_meters = 75  # Base radius at 50 feet
        altitude_difference = altitude_meters - base_altitude_meters
        loiter_radius = base_radius_meters + (altitude_difference * (15 / 3.048))  # 15 meters per 10 feet
        return max(loiter_radius, 50)  # Minimum radius of 50 meters

    def visualize_altitude(self):
        """Displays altitude profile information for the mission with AMSL terrain elevation."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters and user's preferred units
        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
        is_metric = settings_manager.is_metric()
        
        # Convert to display units
        if is_metric:
            altitude_display = altitude_meters
            unit_label = "meters"
        else:
            altitude_display = altitude_meters * 3.28084  # Convert to feet
            unit_label = "feet"
        
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
        
        # Calculate statistics
        min_terrain = min(terrain_elevations)
        max_terrain = max(terrain_elevations)
        avg_terrain = sum(terrain_elevations) / len(terrain_elevations)
        min_amsl = min(amsl_altitudes)
        max_amsl = max(amsl_altitudes)
        avg_amsl = sum(amsl_altitudes) / len(amsl_altitudes)
        
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
        plt.title('Multi-Delivery Mission Altitude Profile with Terrain')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Fill area between AMSL and terrain to show flight corridor
        plt.fill_between(waypoint_indices, terrain_elevations, amsl_altitudes, alpha=0.2, color='blue', label='Flight Corridor')
        
        # Add statistics text
        plt.subplot(2, 1, 2)
        plt.axis('off')
        stats_text = f"""Multi-Delivery Mission Altitude Profile with Terrain
=====================================================

Total Waypoints: {len(self.waypoints)}
Delivery Points: {len(self.delivery_points)}
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

Mission Summary:
- Start Point: {self.waypoints[0] if self.waypoints else 'N/A'}
- End Point: {self.waypoints[-1] if self.waypoints else 'N/A'}
- Aircraft Type: {self.aircraft_type.currentText()}
- Final Action: {self.final_action.currentText()}

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

    # Aircraft Configuration Methods

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


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = MultiDelivery()  # Updated class name
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()