
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
    QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout, QTextEdit, QLineEdit, QRadioButton, QButtonGroup,
    QHBoxLayout, QWidget, QGroupBox, QScrollArea, QGridLayout, QSplitter
)
from PyQt5.QtCore import QUrl, Qt, QObject, pyqtSlot
from PyQt5.QtWebChannel import QWebChannel
from shapely.geometry import LineString
from shapely.ops import transform
from pyproj import Proj, Transformer
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


class MissionPlannerMapBridge(QObject):
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


class MissionPlanner(MissionToolBase):
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("atob_mission_planner")
        self.mission_generator = get_optimized_mission_generator("atob_mission_planner")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("atob_mission_planner")
        
        self.plan_file_path = None
        self.kml_coordinates = []  # Store coordinates extracted from KML
        self.takeoff_point = None
        self.landing_point = None
        self.initUI()
        self.apply_qgc_theme()


    def initUI(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - A-to-B Mission Planner")
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

        # Collapsible Instructions with Toggle Button
        self.instructions_label = QLabel(
            "Instructions:\n"
            "1. Select whether to use a KML file or manually enter start and end points.\n"
            "2. If using a KML file, load it and view the extracted path.\n"
            "3. Adjust settings (altitude, interval, geofence) as required, then generate the plan."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setVisible(False)

        self.toggle_instructions_btn = QPushButton("Show Instructions", self)
        self.toggle_instructions_btn.setCheckable(True)
        self.toggle_instructions_btn.clicked.connect(self.toggle_instructions)

        left_layout.addWidget(self.toggle_instructions_btn)
        left_layout.addWidget(self.instructions_label)

        # Map View
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        from utils import get_map_html_path
        self.map_view.setUrl(QUrl.fromLocalFile(get_map_html_path()))
        
        # Set up communication channel for map interactions
        self.channel = QWebChannel()
        self.map_bridge = MissionPlannerMapBridge()
        self.map_bridge.parent_widget = self
        self.channel.registerObject('pywebchannel', self.map_bridge)
        self.map_view.page().setWebChannel(self.channel)
        
        left_layout.addWidget(self.map_view, 8)  # Give map 80% of vertical space (8 out of 10 total)

        # Choice between manual or KML path
        self.path_choice_label = QLabel("Select Path Input Method:")
        left_layout.addWidget(self.path_choice_label, 1)  # Give controls 10% of vertical space

        self.path_choice_group = QButtonGroup(self)
        self.manual_path_radio = QRadioButton("Manual Entry (Takeoff and Landing)")
        self.kml_path_radio = QRadioButton("Load KML Path File")
        self.manual_path_radio.setChecked(True)

        self.path_choice_group.addButton(self.manual_path_radio)
        self.path_choice_group.addButton(self.kml_path_radio)

        left_layout.addWidget(self.manual_path_radio, 1)
        left_layout.addWidget(self.kml_path_radio, 1)

        # KML Path File Controls (hidden by default)
        self.load_kml_btn = QPushButton("Load KML Path File")
        self.load_kml_btn.setVisible(False)
        self.load_kml_btn.clicked.connect(self.load_kml_file)
        left_layout.addWidget(self.load_kml_btn, 1)

        self.kml_file_label = QLabel("No KML file loaded.")
        self.kml_file_label.setVisible(False)
        left_layout.addWidget(self.kml_file_label, 1)

        self.kml_coordinates_text = QTextEdit()
        self.kml_coordinates_text.setReadOnly(True)
        self.kml_coordinates_text.setVisible(False)
        left_layout.addWidget(self.kml_coordinates_text, 1)

        # Connect radio buttons to toggle UI elements
        self.manual_path_radio.toggled.connect(self.toggle_path_input)
        self.kml_path_radio.toggled.connect(self.toggle_path_input)

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

        # Button to generate .plan file
        self.generate_btn = QPushButton("Generate .plan File", self)
        self.generate_btn.clicked.connect(self.generate_plan)
        form_layout.addWidget(self.generate_btn)




        # Button to visualize altitude profile (initially disabled)
        self.visualize_btn = QPushButton("Visualize Altitude Profile", self)
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self.visualize_altitude)
        form_layout.addWidget(self.visualize_btn)

        # Button to export flight path as KMZ/KML (initially disabled)
        self.export_btn = QPushButton("Export Flight Path (KMZ/KML)", self)
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

        self.waypoints = []  # Placeholder for storing waypoints for visualization

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

    # Aircraft Configuration Methods

    def toggle_instructions(self):
        if self.toggle_instructions_btn.isChecked():
            self.instructions_label.setVisible(True)
            self.toggle_instructions_btn.setText("Hide Instructions")
        else:
            self.instructions_label.setVisible(False)
            self.toggle_instructions_btn.setText("Show Instructions")

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

    def toggle_path_input(self):
        """Toggle visibility of KML tools based on user choice."""
        use_kml = self.kml_path_radio.isChecked()
        self.load_kml_btn.setVisible(use_kml)
        self.kml_file_label.setVisible(use_kml)
        self.kml_coordinates_text.setVisible(use_kml)

    def load_kml_file(self):
        """Loads a KML file and extracts path coordinates."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open KML Path File", "", "KML Files (*.kml)")
        if not file_path:
            return

        self.kml_file_label.setText(f"Loaded KML File: {file_path}")
        self.kml_coordinates = self.extract_kml_coordinates(file_path)

        if self.kml_coordinates:
            self.kml_coordinates_text.setText("\n".join(map(str, self.kml_coordinates)))
        else:
            self.kml_coordinates_text.setText("No valid coordinates found in the KML file.")

    def extract_kml_coordinates(self, file_path):
        """Extracts coordinates from the <LineString> tag in a KML file."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            line_elements = root.findall(".//kml:LineString/kml:coordinates", namespace)

            path_coordinates = []
            for element in line_elements:
                raw_coords = element.text.strip()
                for coord in raw_coords.split():
                    lon, lat, alt = map(float, coord.split(","))
                    path_coordinates.append((lat, lon, alt))
            return path_coordinates
        except Exception as e:
            print(f"Error parsing KML file: {e}")
            return []

    def parse_coordinates(self, coord_text):
        try:
            lat, lon = map(float, coord_text.split(','))
            return lat, lon
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in 'lat,lon' format.")
            return None, None

    def convert_units(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def interpolate_kml_path(self, start_coords, end_coords, interval):
        """Interpolates waypoints between two points based on the interval."""
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)

        interpolated_coords = [start_coords]

        num_intervals = int(distance // interval)
        for j in range(1, num_intervals):
            fraction = j / num_intervals
            interpolated_point = (
                start_lat + fraction * (end_lat - start_lat),
                start_lon + fraction * (end_lon - start_lon)
            )
            interpolated_coords.append(interpolated_point)

        interpolated_coords.append(end_coords)
        return interpolated_coords

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def generate_plan(self):
        """Generates a flight plan based on the selected input method."""
        if self.kml_path_radio.isChecked():
            if not self.kml_coordinates:
                QMessageBox.warning(self, "No KML Path", "Please load a KML path file first.")
                return

            # Get aircraft-aware waypoint interval
            if self.is_parameters_enabled():
                interval_meters = self.get_aircraft_aware_waypoint_spacing("atob", 50.0)  # Default 50m spacing
            else:
                interval_meters = self.convert_to_meters(
                    float(self.interval.text()), 
                    self.interval_units.currentText()
                )

            # Interpolate the KML path based on the interval
            self.waypoints = []
            for i in range(len(self.kml_coordinates) - 1):
                start_coords = (self.kml_coordinates[i][0], self.kml_coordinates[i][1])
                end_coords = (self.kml_coordinates[i + 1][0], self.kml_coordinates[i + 1][1])
                segment_waypoints = self.interpolate_kml_path(start_coords, end_coords, interval_meters)
                self.waypoints.extend(segment_waypoints[:-1])  # Avoid duplicating the last point of each segment

            # Add the final KML point
            self.waypoints.append((self.kml_coordinates[-1][0], self.kml_coordinates[-1][1]))
        else:
            # Handle manual entry for takeoff and landing
            if not self.takeoff_point or not self.landing_point:
                QMessageBox.warning(self, "Missing Coordinates", "Please set both takeoff and landing locations using the map.")
                return

            start_lat, start_lon = self.takeoff_point["lat"], self.takeoff_point["lng"]
            end_lat, end_lon = self.landing_point["lat"], self.landing_point["lng"]

            # Get aircraft-aware waypoint interval
            if self.is_parameters_enabled():
                interval_meters = self.get_aircraft_aware_waypoint_spacing("atob", 50.0)  # Default 50m spacing
            else:
                interval_meters = self.convert_to_meters(
                    float(self.interval.text()), 
                    self.interval_units.currentText()
                )

            # Interpolate waypoints between start and end locations
            self.waypoints = self.interpolate_kml_path((start_lat, start_lon), (end_lat, end_lon), interval_meters)

        # Progress bar setup
        total_steps = len(self.waypoints) + 2  # Add steps for takeoff and landing
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
        mission_items = []

        # Add takeoff sequence
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 22,  # TAKEOFF command for Multicopter
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, self.waypoints[0][0], self.waypoints[0][1], altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })
        self.progress_bar.setValue(1)
        QtWidgets.QApplication.processEvents()

        # Add waypoints
        for i, (lat, lon) in enumerate(self.waypoints):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)  # Get terrain height
            waypoint_amsl_altitude = terrain_elevation + altitude_meters  # ✅ Ensures correct terrain-following altitude

            mission_items.append({
                "AMSLAltAboveTerrain": waypoint_amsl_altitude,  # ✅ Now correctly set
                "Altitude": altitude_meters,  # ✅ User-defined AGL altitude (constant)
                "AltitudeMode": 3,  # ✅ Mode 3 = Terrain Following
                "autoContinue": True,
                "command": 16,  # Waypoint command
                "doJumpId": i + 2,
                "frame": 0,  # ✅ Absolute altitude (Terrain Following Mode)
                "params": [0, 0, 0, None, lat, lon, waypoint_amsl_altitude],  # ✅ Uses terrain-following altitude
                "type": "SimpleItem"
            })

            self.progress_bar.setValue(self.progress_bar.value() + 1)
            QtWidgets.QApplication.processEvents()

        # Add landing sequence
        final_lat, final_lon = self.waypoints[-1]  # Unpack lat and lon
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 21,  # LAND command for Multicopter
                "doJumpId": len(self.waypoints) + 2,
                "frame": 3,
                "params": [0, 0, 0, None, final_lat, final_lon, 0],
                "type": "SimpleItem",
                "autoContinue": True
            })

        # Calculate lateral geofence buffer using Shapely
        waypoints_line = LineString([(lon, lat) for lat, lon in self.waypoints])  # Convert to (lon, lat) format
        geofence_buffer_meters = self.convert_units(float(self.geofence_buffer.text()), self.geofence_units.currentText())

        # Define projections
        proj_wgs84 = Proj(proj='latlong', datum='WGS84')
        proj_aeqd = Proj(proj='aeqd', datum='WGS84', lat_0=self.waypoints[0][0], lon_0=self.waypoints[0][1])
        transformer_to_aeqd = Transformer.from_proj(proj_wgs84, proj_aeqd)
        transformer_to_wgs84 = Transformer.from_proj(proj_aeqd, proj_wgs84)

        # Apply buffer
        projected_line = transform(transformer_to_aeqd.transform, waypoints_line)
        buffered_polygon = projected_line.buffer(geofence_buffer_meters)
        buffered_polygon = transform(transformer_to_wgs84.transform, buffered_polygon)  # Convert back to lat/lon

        # Extract polygon coordinates for the geofence
        geofence_polygon = [[lat, lon] for lon, lat in list(buffered_polygon.exterior.coords)]

        geofence_data = {
            "circles": [],
            "polygons": [{
                "inclusion": True,
                "polygon": geofence_polygon,
                "version": 1
            }],
            "version": 2  # Geofence version
        }

        # Ensure home elevation is defined before using it
        home_elevation = self.terrain_query.get_elevation(self.waypoints[0][0], self.waypoints[0][1])  # ✅ Fetch terrain elevation
                
        # Get aircraft-specific parameters using new system
        aircraft_info = self.get_aircraft_info_for_export()

        # Save flight plan
        plan_data = {
            "fileType": "Plan",
            "version": 1,  # Root-level version
            "geoFence": geofence_data,
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": aircraft_info["cruiseSpeed"],
                "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                "globalPlanAltitudeMode": 0,
                "hoverSpeed": aircraft_info["hoverSpeed"],
                "items": mission_items,
                "plannedHomePosition": [self.waypoints[0][0], self.waypoints[0][1], home_elevation],  # ✅ Use real terrain altitude
                "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                "version": 2,  # Mission version
                "aircraftParameters": aircraft_info["aircraftParameters"]
            },
            "rallyPoints": {
                "points": [],
                "version": 2  # Rally points version
            }
        }

        # Use new file generation system
        saved_file = self.save_mission_file(plan_data, "atob_mission")
        if saved_file:
            self.plan_file_path = saved_file
            self.open_btn.setEnabled(True)
            self.visualize_btn.setEnabled(True)
            self.export_btn.setEnabled(True)

            # Enable toolbar actions
            self.toolbar.enable_actions(True)

        # Check for terrain proximity warnings
        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
        proximity_warnings = self.check_terrain_proximity(altitude_meters)
        
        if proximity_warnings:
            self.show_terrain_proximity_warning(proximity_warnings)

        # Hide progress bar after completion
        self.progress_bar.setValue(total_steps)
        self.progress_bar.setVisible(False)

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
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
        plt.title('A-to-B Mission Altitude Profile with Terrain')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Fill area between AMSL and terrain to show flight corridor
        plt.fill_between(waypoint_indices, terrain_elevations, amsl_altitudes, alpha=0.2, color='blue', label='Flight Corridor')
        
        # Add statistics text
        plt.subplot(2, 1, 2)
        plt.axis('off')
        stats_text = f"""A-to-B Mission Altitude Profile with Terrain
=============================================

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

Mission Summary:
- Start Point: {self.waypoints[0] if self.waypoints else 'N/A'}
- End Point: {self.waypoints[-1] if self.waypoints else 'N/A'}
- Aircraft Type: {self.aircraft_type.currentText()}

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
            altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
            
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
    <name>A-to-B Mission Flight Path</name>
    <description>Flight path generated by AutoFlightGenerator</description>
    
    <!-- Flight Path Line -->
    <Placemark>
      <name>Flight Path</name>
      <description>A-to-B mission flight path with terrain following</description>
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
    planner = MissionPlanner()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
