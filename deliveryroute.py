import json
import os
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
# Import plan visualizer for .plan file visualization
from plan_visualizer import PlanVisualizer


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
        
        try:
            # Use optimized components
            self.terrain_query = get_optimized_terrain_query("delivery_route")
            self.mission_generator = get_optimized_mission_generator("delivery_route")
            self.waypoint_optimizer = get_optimized_waypoint_optimizer("delivery_route")
            
            # Initialize parameter UI component
            self.parameter_ui = ParameterAwareUIComponent()
            self.parameter_ui.parameter_usage_changed.connect(self.on_parameter_usage_changed)
            self.parameter_ui.parameter_file_loaded.connect(self.on_parameter_file_loaded)
            self.parameter_ui.parameter_file_error.connect(self.on_parameter_file_error)
            
            # Initialize plan visualizer (will be set up after map_view is created)
            self.plan_visualizer = None
            
            self.plan_file_path = None
            self.waypoints = []  # Placeholder for storing waypoints for visualization
            self.takeoff_point = None
            self.landing_point = None
            self.initUI()
            self.apply_qgc_theme()
        except Exception as e:
            # Log the error and re-raise it so the dashboard can handle it
            import traceback
            error_details = traceback.format_exc()
            print(f"Error initializing DeliveryRoute: {e}")
            print(error_details)
            raise  # Re-raise so dashboard error handler can show appropriate message

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
        
        # Initialize plan visualizer now that map_view is available
        try:
            self.plan_visualizer = PlanVisualizer(self.map_view)
        except Exception as e:
            print(f"Warning: Could not initialize plan visualizer: {e}")
            self.plan_visualizer = None
        
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


        # Enhanced visualization button
        self.visualize_path_btn = QtWidgets.QPushButton("🗺️ Show Flight Path on Map")
        self.visualize_path_btn.setEnabled(False)
        self.visualize_path_btn.clicked.connect(self.visualize_flight_path)
        self.visualize_path_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        form_layout.addWidget(self.visualize_path_btn)
        
        # Clear flight path button
        self.clear_path_btn = QtWidgets.QPushButton("🗑️ Clear Flight Path")
        self.clear_path_btn.setEnabled(False)
        self.clear_path_btn.clicked.connect(self.clear_flight_path)
        self.clear_path_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        form_layout.addWidget(self.clear_path_btn)
        
        # Button to load and visualize .plan file
        self.load_plan_btn = QtWidgets.QPushButton("📁 Load .plan File")
        self.load_plan_btn.clicked.connect(self.load_plan_file)
        self.load_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        form_layout.addWidget(self.load_plan_btn)
        
        # Button to clear plan visualization
        self.clear_plan_btn = QtWidgets.QPushButton("🗑️ Clear Plan Visualization")
        self.clear_plan_btn.clicked.connect(self.clear_plan_visualization)
        self.clear_plan_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #EF6C00;
            }
        """)
        form_layout.addWidget(self.clear_plan_btn)

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
        try:
            self.takeoff_point = {"lat": lat, "lng": lng}
            
            # Try to get terrain elevation with timeout, but don't crash if it fails
            try:
                # Use timeout method if available, otherwise use regular method
                if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                    terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lng, timeout=5.0)
                else:
                    terrain_elevation = self.terrain_query.get_elevation(lat, lng)
                
                # Check if elevation is valid (not 0 or None)
                if terrain_elevation is not None and terrain_elevation != 0:
                    elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
                else:
                    # Try direct API call as fallback
                    import requests
                    try:
                        response = requests.get(
                            "https://api.opentopodata.org/v1/srtm90m",
                            params={'locations': f"{lat},{lng}"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if "results" in data and data["results"] and data["results"][0].get("elevation"):
                                terrain_elevation = data["results"][0]["elevation"]
                                elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
                            else:
                                elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
                        else:
                            elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
                    except Exception as api_error:
                        print(f"Direct API fallback failed: {api_error}")
                        elevation_text = f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
            except Exception as e:
                # If elevation query fails, still set the location but without elevation info
                print(f"Warning: Could not get elevation for takeoff location: {e}")
                import traceback
                traceback.print_exc()
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
            
            # Try to get terrain elevation with timeout, but don't crash if it fails
            try:
                # Use timeout method if available, otherwise use regular method
                if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                    terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lng, timeout=5.0)
                else:
                    terrain_elevation = self.terrain_query.get_elevation(lat, lng)
                
                # Check if elevation is valid (not 0 or None)
                if terrain_elevation is not None and terrain_elevation != 0:
                    elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
                else:
                    # Try direct API call as fallback
                    import requests
                    try:
                        response = requests.get(
                            "https://api.opentopodata.org/v1/srtm90m",
                            params={'locations': f"{lat},{lng}"},
                            timeout=5
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if "results" in data and data["results"] and data["results"][0].get("elevation"):
                                terrain_elevation = data["results"][0]["elevation"]
                                elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)"
                            else:
                                elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
                        else:
                            elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
                    except Exception as api_error:
                        print(f"Direct API fallback failed: {api_error}")
                        elevation_text = f"Landing: {lat:.6f}, {lng:.6f} (Elev: unavailable)"
            except Exception as e:
                # If elevation query fails, still set the location but without elevation info
                print(f"Warning: Could not get elevation for landing location: {e}")
                import traceback
                traceback.print_exc()
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
        
        # Get terrain elevation with error handling
        try:
            if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                terrain_elevation = self.terrain_query.get_elevation_with_timeout(start_lat, start_lon, timeout=5.0)
            else:
                terrain_elevation = self.terrain_query.get_elevation(start_lat, start_lon)
            
            # Validate elevation
            if terrain_elevation is None:
                terrain_elevation = 0.0
        except Exception as e:
            print(f"Warning: Could not get terrain elevation for takeoff, using 0: {e}")
            terrain_elevation = 0.0
        
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
        # Get terrain elevation with error handling
        try:
            if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lon, timeout=5.0)
            else:
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            
            # Validate elevation
            if terrain_elevation is None:
                terrain_elevation = 0.0
        except Exception as e:
            print(f"Warning: Could not get terrain elevation for waypoint, using 0: {e}")
            terrain_elevation = 0.0
        
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
                try:
                    if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                        terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lon, timeout=5.0)
                    else:
                        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                    
                    if terrain_elevation is None:
                        terrain_elevation = 0.0
                except Exception as e:
                    print(f"Warning: Could not get terrain elevation for delivery waypoint, using 0: {e}")
                    terrain_elevation = 0.0
                
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
                try:
                    if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                        terrain_elevation = self.terrain_query.get_elevation_with_timeout(lat, lon, timeout=5.0)
                    else:
                        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                    
                    if terrain_elevation is None:
                        terrain_elevation = 0.0
                except Exception as e:
                    print(f"Warning: Could not get terrain elevation for landing waypoint, using 0: {e}")
                    terrain_elevation = 0.0
                
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
        """Compile plan data with comprehensive error handling and QGC compatibility validation."""
        try:
            # Get aircraft-specific parameters using new system
            try:
                if self.parameter_ui.is_parameter_aware_enabled():
                    aircraft_info = self.parameter_ui.get_aircraft_info_for_export()
                else:
                    aircraft_info = self.get_aircraft_info_for_export()
            except Exception as e:
                print(f"Warning: Could not get aircraft info, using defaults: {e}")
                aircraft_info = {
                    "cruiseSpeed": 15.0,
                    "hoverSpeed": 5.0,
                    "firmwareType": "arducopter",
                    "vehicleType": "multicopter"
                }
            
            # Validate required fields with defaults
            cruise_speed = aircraft_info.get("cruiseSpeed", 15.0)
            hover_speed = aircraft_info.get("hoverSpeed", 5.0)
            firmware_type = aircraft_info.get("firmwareType", "arducopter")
            vehicle_type = aircraft_info.get("vehicleType", "multicopter")
            
            # Convert firmware type to QGC format (12 = ArduCopter, 11 = ArduPlane, 12 = default)
            firmware_type_code = 12  # Default to ArduCopter
            if firmware_type == "arduplane":
                firmware_type_code = 11
            elif firmware_type == "arducopter":
                firmware_type_code = 12
            else:
                firmware_type_code = 12  # Default fallback
            
            # Convert vehicle type to QGC format (1 = Fixed Wing, 2 = MultiRotor)
            vehicle_type_code = 2  # Default to MultiRotor
            if vehicle_type == "fixedwing":
                vehicle_type_code = 1
            else:
                vehicle_type_code = 2  # Default fallback
            
            # Validate mission items
            if not mission_items or len(mission_items) == 0:
                raise ValueError("Cannot compile plan: No mission items generated.")
            
            # Ensure all mission items have required fields for QGC
            for i, item in enumerate(mission_items):
                if "doJumpId" not in item:
                    item["doJumpId"] = i + 1
                if "autoContinue" not in item:
                    item["autoContinue"] = True
                if "type" not in item:
                    item["type"] = "SimpleItem"
            
            # Validate geofence coordinates
            if not geofence_coords or len(geofence_coords) == 0:
                print("Warning: No geofence coordinates provided, using empty geofence")
                geofence_polygons = []
            else:
                geofence_polygons = [{"polygon": geofence_coords, "inclusion": True, "version": 1}]
            
            # Validate coordinates
            if start_lat is None or start_lon is None:
                raise ValueError("Invalid home position coordinates")
            
            # Ensure home_elevation is a number
            if home_elevation is None:
                home_elevation = 0.0
            
            plan_data = {
                "fileType": "Plan",
                "geoFence": {
                    "circles": [],
                    "polygons": geofence_polygons,
                    "version": 2
                },
                "groundStation": "QGroundControl",
                "mission": {
                    "cruiseSpeed": float(cruise_speed),
                    "firmwareType": int(firmware_type_code),
                    "globalPlanAltitudeMode": 0,
                    "hoverSpeed": float(hover_speed),
                    "items": mission_items,
                    "plannedHomePosition": [float(start_lat), float(start_lon), float(home_elevation)],
                    "vehicleType": int(vehicle_type_code),
                    "version": 2
                },
                "rallyPoints": {"points": [], "version": 2},
                "version": 1
            }
            
            return plan_data
            
        except Exception as e:
            print(f"Error compiling plan data: {e}")
            import traceback
            traceback.print_exc()
            raise

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QtWidgets.QApplication.processEvents()

    def generate_plan(self):
        """Generate .plan file with comprehensive error handling."""
        try:
            # Validate takeoff and landing coordinates
            if not self.takeoff_point or not self.landing_point:
                QMessageBox.warning(self, "Missing Coordinates", "Please set both takeoff and landing locations using the map.")
                return
            
            start_lat, start_lon = self.takeoff_point["lat"], self.takeoff_point["lng"]
            end_lat, end_lon = self.landing_point["lat"], self.landing_point["lng"]

            # Use optimized progress dialog
            progress_dialog = None
            try:
                progress_dialog = create_optimized_progress_dialog("Generating Delivery Route", self)
                progress_dialog.show()
            except Exception as e:
                print(f"Warning: Could not create progress dialog: {e}")

            # Get terrain elevation efficiently with error handling
            try:
                if hasattr(self.terrain_query, 'get_elevation_with_timeout'):
                    home_elevation = self.terrain_query.get_elevation_with_timeout(start_lat, start_lon, timeout=5.0)
                else:
                    home_elevation = self.terrain_query.get_elevation(start_lat, start_lon)
                
                # Validate elevation
                if home_elevation is None:
                    home_elevation = 0.0
            except Exception as e:
                print(f"Warning: Could not get terrain elevation, using 0: {e}")
                home_elevation = 0.0

            # Get aircraft-aware values
            try:
                if self.parameter_ui.is_parameter_aware_enabled():
                    # Use aircraft parameters for optimized values
                    try:
                        mission_settings = self.parameter_ui.get_mission_settings()
                        characteristics = self.parameter_ui.get_aircraft_characteristics()
                    except Exception as e:
                        print(f"Warning: Could not get mission settings/characteristics: {e}")
                        mission_settings = {}
                        characteristics = {}
                    
                    # Use parameter-aware altitude
                    try:
                        altitude_meters = self.get_aircraft_aware_altitude("delivery", 
                            self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText()))
                    except Exception as e:
                        print(f"Warning: Could not get aircraft-aware altitude, using manual input: {e}")
                        altitude_meters = self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText())
                    
                    # Use parameter-aware waypoint spacing
                    try:
                        interval_meters = self.get_aircraft_aware_waypoint_spacing("delivery", 
                            self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText()))
                    except Exception as e:
                        print(f"Warning: Could not get aircraft-aware waypoint spacing, using manual input: {e}")
                        interval_meters = self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText())
                    
                    # Use parameter-aware geofence buffer
                    try:
                        geofence_buffer_meters = self.convert_to_meters(
                            self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), 
                            self.geofence_units.currentText())
                    except Exception as e:
                        print(f"Warning: Could not get geofence buffer, using manual input: {e}")
                        geofence_buffer_meters = self.convert_to_meters(self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), self.geofence_units.currentText())
                    
                    # Override aircraft type with detected type if available
                    try:
                        detected_aircraft_type = characteristics.get('aircraft_type', 'Unknown')
                        if detected_aircraft_type != 'Unknown':
                            aircraft_type = self._map_aircraft_type_to_ui(detected_aircraft_type)
                        else:
                            aircraft_type = self.aircraft_type.currentText()
                    except Exception as e:
                        print(f"Warning: Could not determine aircraft type from parameters: {e}")
                        aircraft_type = self.aircraft_type.currentText()
                        
                elif self.is_parameters_enabled():
                    # Use legacy aircraft parameters for optimized values
                    try:
                        altitude_meters = self.get_aircraft_aware_altitude("delivery", 
                            self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText()))
                        interval_meters = self.get_aircraft_aware_waypoint_spacing("delivery", 
                            self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText()))
                        geofence_buffer_meters = self.convert_to_meters(
                            self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), 
                            self.geofence_units.currentText())
                        aircraft_type = self.aircraft_type.currentText()
                    except Exception as e:
                        print(f"Warning: Legacy parameter-aware values failed, using manual input: {e}")
                        altitude_meters = self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText())
                        interval_meters = self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText())
                        geofence_buffer_meters = self.convert_to_meters(self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), self.geofence_units.currentText())
                        aircraft_type = self.aircraft_type.currentText()
                else:
                    # Use manual input values
                    altitude_meters = self.validate_numeric_input(self.altitude.text(), "Altitude")
                    interval_meters = self.validate_numeric_input(self.interval.text(), "Waypoint Interval")
                    geofence_buffer_meters = self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer")
                    if None in (altitude_meters, interval_meters, geofence_buffer_meters):
                        if progress_dialog:
                            try:
                                progress_dialog.close()
                            except:
                                pass
                        return

                    altitude_meters = self.convert_to_meters(altitude_meters, self.altitude_units.currentText())
                    interval_meters = self.convert_to_meters(interval_meters, self.interval_units.currentText())
                    geofence_buffer_meters = self.convert_to_meters(geofence_buffer_meters, self.geofence_units.currentText())
                    aircraft_type = self.aircraft_type.currentText()
            except Exception as e:
                print(f"Warning: Error in aircraft-aware value setup, using defaults: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to manual values
                altitude_meters = self.convert_to_meters(self.validate_numeric_input(self.altitude.text(), "Altitude"), self.altitude_units.currentText())
                interval_meters = self.convert_to_meters(self.validate_numeric_input(self.interval.text(), "Waypoint Interval"), self.interval_units.currentText())
                geofence_buffer_meters = self.convert_to_meters(self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer"), self.geofence_units.currentText())
                aircraft_type = self.aircraft_type.currentText()

            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(5, "Generating waypoints")
                self.waypoints = self.interpolate_waypoints((start_lat, start_lon), (end_lat, end_lon), interval_meters)
                
                if not self.waypoints or len(self.waypoints) == 0:
                    raise ValueError("Failed to generate waypoints. Please check your coordinates and interval settings.")
                
                mission_items = []

                if progress_dialog:
                    progress_dialog.update_with_stats(10, "Generating geofence")
                offset_points = self.offset_waypoints(self.waypoints, geofence_buffer_meters)
                geofence_coords = self.generate_geofence(offset_points)
                
                if not geofence_coords or len(geofence_coords) == 0:
                    raise ValueError("Failed to generate geofence. Please check your waypoints.")
            except Exception as e:
                print(f"Error in waypoint/geofence generation: {e}")
                raise  # Re-raise to be caught by outer try-except

            aircraft_type = self.aircraft_type.currentText()
            landing_behavior = self.landing_behavior.currentText()

            # **1️⃣ Takeoff**
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(15, "Adding takeoff command")
                    QtWidgets.QApplication.processEvents()  # Allow UI to update
                
                self.add_takeoff_command(mission_items, start_lat, start_lon, altitude_meters)
                
                # Validate that takeoff command was added
                if not mission_items or len(mission_items) == 0:
                    raise ValueError("Failed to add takeoff command. Mission items list is empty.")
                    
            except Exception as e:
                error_msg = f"Error adding takeoff command at 15%: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                
                # Close progress dialog before showing error
                if progress_dialog:
                    try:
                        progress_dialog.close()
                    except:
                        pass
                
                # Show specific error to user
                from error_handler import handle_error
                error_dialog = handle_error('plan_generation_error', 
                    f"{error_msg}\n\nPossible causes:\n"
                    f"- Terrain elevation API unavailable\n"
                    f"- Invalid coordinates\n"
                    f"- Network connection issues", 
                    self)
                error_dialog.exec_()
                return  # Exit early to prevent further errors

            # **2️⃣ Outbound Waypoints (STOP before final delivery) - Use parallel processing**
            try:
                if progress_dialog:
                    try:
                        progress_dialog.update_with_stats(20, "Generating outbound waypoints")
                    except:
                        pass
                
                # Prepare waypoint data for parallel processing
                outbound_waypoints = self.waypoints[:-1]  # Exclude last delivery point for now
                if not outbound_waypoints:
                    raise ValueError("No outbound waypoints to generate. Please check your route.")
                
                waypoint_data = [(i + 1, lat, lon, altitude_meters) for i, (lat, lon) in enumerate(outbound_waypoints)]
                
                # Generate waypoints in parallel
                def progress_callback(progress):
                    try:
                        if progress_dialog:
                            progress_dialog.update_with_stats(20 + int(progress * 0.25), "Processing outbound waypoints")
                    except:
                        pass
                
                try:
                    parallel_waypoints = self.mission_generator.generate_mission_parallel(
                        [(lat, lon) for _, lat, lon, _ in waypoint_data], 
                        altitude_meters, 
                        progress_callback
                    )
                except Exception as e:
                    print(f"Warning: Parallel waypoint generation failed, trying sequential: {e}")
                    # Fallback to sequential generation
                    parallel_waypoints = []
                    for i, (lat, lon) in enumerate(outbound_waypoints):
                        try:
                            self.add_waypoint_command(mission_items, i + 1, lat, lon, altitude_meters)
                        except Exception as e2:
                            print(f"Warning: Failed to add waypoint {i+1}: {e2}")
                            # Continue with next waypoint
                    # Skip the parallel_waypoints appending section
                    parallel_waypoints = None
                
                if parallel_waypoints is not None:
                    if not parallel_waypoints:
                        raise ValueError("Failed to generate outbound waypoints. Please check your settings.")
                    
                    # Add waypoints to mission items
                    for i, waypoint in enumerate(parallel_waypoints):
                        if waypoint and isinstance(waypoint, dict):
                            try:
                                waypoint["doJumpId"] = i + 2  # Start from 2 (after takeoff)
                                mission_items.append(waypoint)
                            except Exception as e:
                                print(f"Warning: Failed to add parallel waypoint {i}: {e}")
                                # Continue with next waypoint
            except Exception as e:
                error_msg = f"Error generating outbound waypoints: {e}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                raise  # Re-raise to be caught by outer try-except

            # **3️⃣ Delivery Handling**
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(45, "Configuring delivery sequence")
                    QtWidgets.QApplication.processEvents()  # Allow UI to update
                
                # Validate waypoints exist
                if not self.waypoints or len(self.waypoints) == 0:
                    raise ValueError("No waypoints available for delivery sequence. Waypoint generation may have failed.")
                
                # Get final waypoint
                final_lat, final_lon = self.waypoints[-1]
                
                # Validate coordinates
                if final_lat is None or final_lon is None:
                    raise ValueError("Invalid coordinates for delivery location. Final waypoint has invalid lat/lon.")
                    
            except Exception as e:
                error_msg = f"Error in delivery handling at 45%: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                
                # Close progress dialog before showing error
                if progress_dialog:
                    try:
                        progress_dialog.close()
                    except:
                        pass
                
                # Show specific error to user
                from error_handler import handle_error
                error_dialog = handle_error('plan_generation_error', 
                    f"{error_msg}\n\nPossible causes:\n"
                    f"- Waypoint generation failed\n"
                    f"- Invalid waypoint coordinates\n"
                    f"- Empty waypoint list", 
                    self)
                error_dialog.exec_()
                return  # Exit early to prevent further errors

            try:
                if aircraft_type == "Quadplane/VTOL Hybrid":
                    # **Transition to Multirotor Before Delivery**
                    self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)

                # **Loiter at Delivery Waypoint (20 feet altitude)**
                self.add_landing_or_loiter_command(mission_items, final_lat, final_lon, altitude_meters)
            except Exception as e:
                error_msg = f"Error adding delivery commands at 45%: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                
                # Close progress dialog before showing error
                if progress_dialog:
                    try:
                        progress_dialog.close()
                    except:
                        pass
                
                # Show specific error to user
                from error_handler import handle_error
                error_dialog = handle_error('plan_generation_error', 
                    f"{error_msg}\n\nPossible causes:\n"
                    f"- Terrain elevation API unavailable\n"
                    f"- Invalid coordinates\n"
                    f"- Network connection issues", 
                    self)
                error_dialog.exec_()
                return  # Exit early to prevent further errors

            # **Payload Mechanism or Landing Behavior**
            try:
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
                    try:
                        self.add_vtol_transition_command(mission_items, 4)  # Transition to Fixed-Wing (mode 4)
                    except Exception as e:
                        print(f"Warning: Could not add VTOL transition command: {e}")
            except Exception as e:
                print(f"Warning: Error in payload/landing behavior section: {e}")
                # Continue anyway

            # **4️⃣ Return Waypoints (Back to Home) - Use parallel processing**
            try:
                if progress_dialog:
                    try:
                        progress_dialog.update_with_stats(50, "Generating return waypoints")
                    except:
                        pass
                
                # Prepare return waypoint data
                return_waypoints = list(reversed(self.waypoints[:-1]))  # Reverse outbound waypoints without last point
                
                if not return_waypoints:
                    raise ValueError("No return waypoints to generate. Please check your route.")
                
                def return_progress_callback(progress):
                    try:
                        if progress_dialog:
                            progress_dialog.update_with_stats(50 + int(progress * 0.25), "Processing return waypoints")
                    except:
                        pass
                
                try:
                    parallel_return_waypoints = self.mission_generator.generate_mission_parallel(
                        return_waypoints, 
                        altitude_meters, 
                        return_progress_callback
                    )
                except Exception as e:
                    print(f"Warning: Parallel return waypoint generation failed, trying sequential: {e}")
                    # Fallback to sequential generation
                    parallel_return_waypoints = []
                    for i, (lat, lon) in enumerate(return_waypoints):
                        try:
                            self.add_waypoint_command(mission_items, len(mission_items) + 1, lat, lon, altitude_meters)
                        except Exception as e2:
                            print(f"Warning: Failed to add return waypoint {i+1}: {e2}")
                            # Continue with next waypoint
                    # Skip the parallel_waypoints appending section
                    parallel_return_waypoints = None
                
                if parallel_return_waypoints is not None:
                    if not parallel_return_waypoints:
                        raise ValueError("Failed to generate return waypoints. Please check your settings.")
                    
                    # Add return waypoints to mission items
                    for i, waypoint in enumerate(parallel_return_waypoints):
                        if waypoint and isinstance(waypoint, dict):
                            try:
                                waypoint["doJumpId"] = len(mission_items) + 1
                                mission_items.append(waypoint)
                            except Exception as e:
                                print(f"Warning: Failed to add parallel return waypoint {i}: {e}")
                                # Continue with next waypoint
            except Exception as e:
                error_msg = f"Error generating return waypoints: {e}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                raise  # Re-raise to be caught by outer try-except

            # **5️⃣ Landing at Home**
            try:
                if progress_dialog:
                    try:
                        progress_dialog.update_with_stats(75, "Configuring landing sequence")
                    except Exception as e:
                        print(f"Error updating progress: {e}")
                        # Continue anyway
                
                if aircraft_type == "Quadplane/VTOL Hybrid":
                    # **Transition to Multirotor for Landing**
                    try:
                        self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)
                    except Exception as e:
                        print(f"Warning: Could not add VTOL transition for landing: {e}")

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
                    try:
                        self.add_fixed_wing_landing_pattern(mission_items, start_lat, start_lon, home_elevation, altitude_meters)
                    except Exception as e:
                        print(f"Warning: Could not add fixed-wing landing pattern: {e}")
                        # Add simple landing as fallback
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
            except Exception as e:
                print(f"Warning: Error in landing sequence configuration: {e}")
                import traceback
                traceback.print_exc()
                # Add simple landing as absolute fallback
                try:
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
                except Exception as e2:
                    print(f"Critical: Could not add fallback landing command: {e2}")

            # Compile the plan data
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(85, "Compiling mission data")
                plan_data = self.compile_plan_data(mission_items, geofence_coords, start_lat, start_lon, home_elevation)
                
                # Validate plan data structure
                if not plan_data or 'mission' not in plan_data:
                    raise ValueError("Failed to compile plan data. Mission structure is invalid.")
            except Exception as e:
                print(f"Error compiling plan data: {e}")
                raise  # Re-raise to be caught by outer try-except

            # Save the plan file using new file generation system
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(90, "Saving mission file")
                saved_file = self.save_mission_file(plan_data, "delivery_route")
                if not saved_file:
                    raise ValueError("Failed to save mission file. Please check file permissions and disk space.")
            except Exception as e:
                print(f"Error saving mission file: {e}")
                raise  # Re-raise to be caught by outer try-except
            
            if saved_file:
                self.plan_file_path = saved_file
                self.visualize_btn.setEnabled(True)
                self.visualize_path_btn.setEnabled(True)
                self.clear_path_btn.setEnabled(True)
                self.export_btn.setEnabled(True)
                
                # Auto-visualize the generated .plan file using MapsolutionLocal method
                try:
                    if progress_dialog:
                        progress_dialog.update_with_stats(92, "Visualizing mission on map")
                    if self.plan_visualizer:
                        try:
                            self.plan_visualizer.auto_visualize_after_generation(saved_file)
                        except Exception as e:
                            print(f"Warning: Could not auto-visualize plan file: {e}")
                except Exception as e:
                    print(f"Warning: Error in plan visualization: {e}")

            # Enable toolbar actions
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(95, "Finalizing mission")
                self.toolbar.enable_actions(True)

                # Check for terrain proximity warnings
                altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
                proximity_warnings = self.check_terrain_proximity(altitude_meters)
                
                if proximity_warnings:
                    self.show_terrain_proximity_warning(proximity_warnings)
            except Exception as e:
                print(f"Warning: Error in finalization steps: {e}")
                # Continue anyway since main generation succeeded
            
            # Show completion statistics and close progress dialog
            try:
                if progress_dialog:
                    progress_dialog.update_with_stats(100, "Complete")
                    progress_dialog.show_completion_stats()
                    progress_dialog.close()
            except Exception as e:
                print(f"Error closing progress dialog: {e}")
            
            # Auto-visualize flight path after successful generation
            try:
                if self.waypoints:
                    self.auto_visualize_flight_path()
            except Exception as e:
                print(f"Error in auto-visualization: {e}")
        
        except Exception as e:
            # Comprehensive error handling for the entire generation process
            import traceback
            error_details = traceback.format_exc()
            print(f"Error generating plan: {e}")
            print(error_details)
            
            # Close progress dialog if it exists
            try:
                if progress_dialog:
                    progress_dialog.close()
            except:
                pass
            
            # Show user-friendly error message
            QMessageBox.critical(
                self,
                "Plan Generation Error",
                f"An error occurred while generating the .plan file:\n\n{str(e)}\n\n"
                f"Please check:\n"
                f"- All required fields are filled correctly\n"
                f"- Takeoff and landing locations are set\n"
                f"- Network connection (for elevation data)\n"
                f"- File permissions in the current directory"
            )

    def auto_visualize_flight_path(self):
        """Automatically visualize flight path after mission generation."""
        try:
            if not self.waypoints:
                return
                
            # Prepare enhanced flight plan data
            flight_plan_data = {
                "waypoints": [],
                "mission_type": "Delivery Route",
                "total_waypoints": len(self.waypoints),
                "auto_visualized": True
            }
            
            # Get altitude in meters
            altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
            
            # Add takeoff point with enhanced data
            if self.takeoff_point:
                terrain_elevation = self.terrain_query.get_elevation(self.takeoff_point["lat"], self.takeoff_point["lng"])
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": self.takeoff_point["lat"],
                    "lng": self.takeoff_point["lng"],
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": "Takeoff",
                    "type": "takeoff"
                })
            elif self.waypoints:
                # Use first waypoint as takeoff if no specific takeoff point
                terrain_elevation = self.terrain_query.get_elevation(self.waypoints[0][0], self.waypoints[0][1])
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": self.waypoints[0][0],
                    "lng": self.waypoints[0][1],
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": "Takeoff",
                    "type": "takeoff"
                })
            
            # Add waypoints with enhanced information
            for i, (lat, lon) in enumerate(self.waypoints):
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": lat,
                    "lng": lon,
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": f"Waypoint {i+1}",
                    "type": "waypoint",
                    "sequence": i + 1
                })
            
            # Add landing point with enhanced data
            if self.landing_point:
                terrain_elevation = self.terrain_query.get_elevation(self.landing_point["lat"], self.landing_point["lng"])
                
                flight_plan_data["waypoints"].append({
                    "lat": self.landing_point["lat"],
                    "lng": self.landing_point["lng"],
                    "altitude": 0,
                    "amsl_altitude": terrain_elevation,
                    "terrain_elevation": terrain_elevation,
                    "title": "Landing",
                    "type": "landing"
                })
            elif self.waypoints:
                # Use last waypoint as landing if no specific landing point
                last_waypoint = self.waypoints[-1]
                terrain_elevation = self.terrain_query.get_elevation(last_waypoint[0], last_waypoint[1])
                
                flight_plan_data["waypoints"].append({
                    "lat": last_waypoint[0],
                    "lng": last_waypoint[1],
                    "altitude": 0,
                    "amsl_altitude": terrain_elevation,
                    "terrain_elevation": terrain_elevation,
                    "title": "Landing",
                    "type": "landing"
                })
            
            # Convert to JSON and visualize - pass waypoints array directly
            import json
            try:
                # Extract waypoints array from flight_plan_data
                waypoints_array = flight_plan_data.get("waypoints", [])
                # Use ensure_ascii=False to handle Unicode characters properly
                waypoints_json = json.dumps(waypoints_array, ensure_ascii=False)
                
                # Call JavaScript function to visualize flight plan with waypoints array
                js_code = f"visualizeFlightPlan({waypoints_json});"
                self.map_view.page().runJavaScript(js_code)
                
                # Auto-fit to bounds
                fit_js = "fitFlightPathBounds();"
                self.map_view.page().runJavaScript(fit_js)
            except UnicodeEncodeError as e:
                # Fallback: use ASCII encoding if Unicode fails
                print(f"Warning: Unicode encoding error in visualization, using ASCII fallback: {e}")
                waypoints_array = flight_plan_data.get("waypoints", [])
                waypoints_json = json.dumps(waypoints_array, ensure_ascii=True)
                js_code = f"visualizeFlightPlan({waypoints_json});"
                self.map_view.page().runJavaScript(js_code)
                fit_js = "fitFlightPathBounds();"
                self.map_view.page().runJavaScript(fit_js)
            except Exception as e:
                print(f"Error in visualization JSON encoding: {e}")
                import traceback
                traceback.print_exc()
                # Try with minimal data
                try:
                    waypoints_array = flight_plan_data.get("waypoints", [])
                    waypoints_json = json.dumps(waypoints_array, ensure_ascii=True)
                    js_code = f"visualizeFlightPlan({waypoints_json});"
                    self.map_view.page().runJavaScript(js_code)
                except Exception as e2:
                    print(f"Failed to visualize waypoints: {e2}")
                    raise
            
            # Show notification (remove emojis to avoid encoding issues)
            try:
                QtWidgets.QMessageBox.information(
                    self, 
                    "Flight Path Auto-Visualized", 
                    f"Flight path with {len(self.waypoints)} waypoints has been automatically displayed on the map!\n\n"
                    f"Mission Type: Delivery Route\n"
                    f"Total Waypoints: {len(self.waypoints)}\n"
                    f"Click 'Show Flight Path on Map' to re-display anytime."
                )
            except Exception as e:
                print(f"Warning: Could not show notification message: {e}")
            
        except Exception as e:
            print(f"Auto-visualization error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Visualization Error", f"Error visualizing flight path: {str(e)}")

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
        self.clear_path_btn.setEnabled(False)
        self.visualize_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
    
    def visualize_flight_path(self):
        """Enhanced visualization of the flight path on the map"""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return
        
        try:
            # Prepare enhanced flight plan data for visualization
            flight_plan_data = {
                "waypoints": [],
                "mission_type": "Delivery Route",
                "total_waypoints": len(self.waypoints),
                "auto_visualized": False
            }
            
            # Get altitude in meters
            altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())
            
            # Add takeoff point with enhanced data
            if self.takeoff_point:
                terrain_elevation = self.terrain_query.get_elevation(self.takeoff_point["lat"], self.takeoff_point["lng"])
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": self.takeoff_point["lat"],
                    "lng": self.takeoff_point["lng"],
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": "Takeoff",
                    "type": "takeoff"
                })
            elif self.waypoints:
                # Use first waypoint as takeoff if no specific takeoff point
                terrain_elevation = self.terrain_query.get_elevation(self.waypoints[0][0], self.waypoints[0][1])
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": self.waypoints[0][0],
                    "lng": self.waypoints[0][1],
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": "Takeoff",
                    "type": "takeoff"
                })
            
            # Add waypoints with enhanced information
            for i, (lat, lon) in enumerate(self.waypoints):
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude_meters
                
                flight_plan_data["waypoints"].append({
                    "lat": lat,
                    "lng": lon,
                    "altitude": altitude_meters,
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": f"Waypoint {i+1}",
                    "type": "waypoint",
                    "sequence": i + 1
                })
            
            # Add landing point with enhanced data
            if self.landing_point:
                terrain_elevation = self.terrain_query.get_elevation(self.landing_point["lat"], self.landing_point["lng"])
                
                flight_plan_data["waypoints"].append({
                    "lat": self.landing_point["lat"],
                    "lng": self.landing_point["lng"],
                    "altitude": 0,
                    "amsl_altitude": terrain_elevation,
                    "terrain_elevation": terrain_elevation,
                    "title": "Landing",
                    "type": "landing"
                })
            elif self.waypoints:
                # Use last waypoint as landing if no specific landing point
                last_waypoint = self.waypoints[-1]
                terrain_elevation = self.terrain_query.get_elevation(last_waypoint[0], last_waypoint[1])
                
                flight_plan_data["waypoints"].append({
                    "lat": last_waypoint[0],
                    "lng": last_waypoint[1],
                    "altitude": 0,
                    "amsl_altitude": terrain_elevation,
                    "terrain_elevation": terrain_elevation,
                    "title": "Landing",
                    "type": "landing"
                })
            
            # Convert to JSON for JavaScript - pass waypoints array directly
            import json
            # Extract waypoints array from flight_plan_data
            waypoints_array = flight_plan_data.get("waypoints", [])
            waypoints_json = json.dumps(waypoints_array, ensure_ascii=False)
            
            # Call JavaScript function to visualize flight plan with waypoints array
            js_code = f"visualizeFlightPlan({waypoints_json});"
            self.map_view.page().runJavaScript(js_code)
            
            # Auto-fit to bounds
            fit_js = "fitFlightPathBounds();"
            self.map_view.page().runJavaScript(fit_js)
            
            # Show enhanced success message
            QMessageBox.information(
                self, 
                "Flight Path Visualized", 
                f"✅ Flight path with {len(self.waypoints)} waypoints has been visualized on the map!\n\n"
                f"Mission Type: Delivery Route\n"
                f"Total Waypoints: {len(self.waypoints)}\n"
                f"Altitude: {altitude_meters} meters AGL"
            )
            
        except Exception as e:
            QMessageBox.warning(self, "Visualization Error", f"Error visualizing flight path: {str(e)}")
    
    def clear_flight_path(self):
        """Clear the flight path from the map."""
        try:
            # Clear flight path using JavaScript
            js_code = "clearFlightPath();"
            self.map_view.page().runJavaScript(js_code)
            
            # Disable buttons
            self.visualize_path_btn.setEnabled(False)
            self.clear_path_btn.setEnabled(False)
            
            QtWidgets.QMessageBox.information(
                self, 
                "Flight Path Cleared", 
                "Flight path has been cleared from the map."
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 
                "Clear Error", 
                f"Error clearing flight path: {str(e)}"
            )
    
    def load_plan_file(self):
        """Load and visualize a .plan file on the map using MapsolutionLocal method."""
        try:
            # Open file dialog to select .plan file
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select .plan File", 
                "", 
                "QGroundControl Plan Files (*.plan);;All Files (*)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Use plan visualizer to load and visualize the file
            if self.plan_visualizer:
                success = self.plan_visualizer.auto_visualize_after_generation(file_path)
                if success:
                    # Get visualization stats
                    stats = self.plan_visualizer.get_visualization_stats()
                    
                    QtWidgets.QMessageBox.information(
                        self, 
                        "Plan File Loaded", 
                        f"Successfully loaded and visualized .plan file!\n\n"
                        f"Waypoints: {stats['waypoints']}\n"
                        f"Geofence Polygons: {stats['geofence_polygons']}\n"
                        f"Rally Points: {stats['rally_points']}\n\n"
                        f"File: {os.path.basename(file_path)}"
                    )
                else:
                    QtWidgets.QMessageBox.warning(
                        self, 
                        "Load Error", 
                        "Failed to load and visualize the .plan file. Please check the file format."
                    )
            else:
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Error", 
                    "Plan visualizer not available."
                )
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 
                "Load Error", 
                f"Error loading .plan file: {str(e)}"
            )
    
    def clear_plan_visualization(self):
        """Clear plan visualization from the map."""
        try:
            if self.plan_visualizer:
                self.plan_visualizer.clear_visualization()
                QtWidgets.QMessageBox.information(
                    self, 
                    "Plan Visualization Cleared", 
                    "Plan visualization has been cleared from the map."
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, 
                    "Error", 
                    "Plan visualizer not available."
                )
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, 
                "Clear Error", 
                f"Error clearing plan visualization: {str(e)}"
            )
    
    def validate_plan_file(self, plan_data):
        """Validate that the plan data has the correct structure."""
        try:
            # Check for required fields
            if 'fileType' not in plan_data or plan_data['fileType'] != 'Plan':
                return False
            
            if 'mission' not in plan_data:
                return False
            
            if 'items' not in plan_data['mission']:
                return False
            
            return True
        except:
            return False
    
    def extract_waypoints_from_plan(self, plan_data):
        """Extract waypoint coordinates from plan data."""
        waypoints = []
        
        for item in plan_data['mission']['items']:
            # Check if this is a waypoint command (command 16 = NAV_WAYPOINT)
            if item.get('command') == 16 and 'params' in item:
                params = item['params']
                # Params format: [0, 0, 0, null, lat, lon, alt]
                if len(params) >= 7 and params[4] is not None and params[5] is not None:
                    lat = params[4]
                    lon = params[5]
                    alt = params[6] if len(params) > 6 else 0
                    waypoints.append({
                        'lat': lat,
                        'lon': lon,
                        'alt': alt,
                        'type': 'waypoint'
                    })
        
        return waypoints
    
    def visualize_plan_file(self, waypoints, plan_data):
        """Visualize the loaded plan file on the map."""
        try:
            # Prepare flight plan data for visualization
            flight_plan_data = {
                "waypoints": [],
                "mission_type": "Loaded Plan File",
                "total_waypoints": len(waypoints),
                "auto_visualized": False,
                "source": "plan_file"
            }
            
            # Add waypoints with enhanced information
            for i, waypoint in enumerate(waypoints):
                # Get terrain elevation for each waypoint
                terrain_elevation = self.terrain_query.get_elevation(waypoint['lat'], waypoint['lon'])
                amsl_altitude = terrain_elevation + waypoint['alt']
                
                flight_plan_data["waypoints"].append({
                    "lat": waypoint['lat'],
                    "lng": waypoint['lon'],
                    "altitude": waypoint['alt'],
                    "amsl_altitude": amsl_altitude,
                    "terrain_elevation": terrain_elevation,
                    "title": f"Waypoint {i+1}",
                    "type": "waypoint",
                    "sequence": i + 1
                })
            
            # Convert to JSON and visualize
            flight_plan_json = json.dumps(flight_plan_data)
            
            # Call JavaScript function to visualize flight plan
            js_code = f"visualizeFlightPlan({flight_plan_json});"
            self.map_view.page().runJavaScript(js_code)
            
            # Auto-fit to bounds
            fit_js = "fitFlightPathBounds();"
            self.map_view.page().runJavaScript(fit_js)
            
        except Exception as e:
            print(f"Error visualizing plan file: {e}")
    
    
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
    
    def save_mission_file(self, plan_data, mission_type):
        """Save mission file using the mission file generator with file dialog."""
        try:
            from mission_file_generator import create_file_generator
            
            # Use the mission file generator
            file_generator = create_file_generator(settings_manager.get_ground_control_station())
            
            # Generate suggested filename with timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            suggested_filename = f"{mission_type}_{timestamp}{file_generator.get_file_extension()}"
            
            # Get file extension and filter
            file_extension = file_generator.get_file_extension()
            if file_extension == ".plan":
                file_filter = "QGroundControl Plan Files (*.plan);;All Files (*)"
            else:
                file_filter = f"Mission Files (*{file_extension});;All Files (*)"
            
            # Open file save dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Mission File",
                os.path.join(os.getcwd(), suggested_filename),
                file_filter
            )
            
            # Check if user cancelled the dialog
            if not file_path:
                return None
            
            # Ensure the file has the correct extension if user didn't specify it
            if not file_path.endswith(file_extension):
                file_path += file_extension
            
            # Save the file
            if file_generator.generate_file(plan_data, file_path):
                return file_path
            else:
                QMessageBox.warning(
                    self,
                    "Save Error",
                    f"Failed to save mission file to:\n{file_path}\n\nPlease check file permissions and try again."
                )
                return None
                
        except Exception as e:
            print(f"Error saving mission file: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "Save Error",
                f"An error occurred while saving the mission file:\n\n{str(e)}"
            )
            return None


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = DeliveryRoute()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()