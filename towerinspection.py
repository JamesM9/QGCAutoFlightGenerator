#!/usr/bin/env python3
"""
Tower Inspection Tool - Automated Tower Inspection Mission Planning
"""

import sys
import json
import requests
import time
import math
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, Point
# Matplotlib imports - only when needed for visualization
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for PyQt compatibility
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: Matplotlib not available. Terrain visualization will be disabled.")
from PyQt5 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QMessageBox, QScrollArea, QWidget, QGroupBox, QHBoxLayout
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebChannel import QWebChannel
from PyQt5 import QtCore
import math
# Import new aircraft parameter system
from aircraft_parameters import MissionToolBase
from shared_toolbar import SharedToolBar


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
                elif response.status_code == 429:  # Too many requests
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0



class TowerInspection(MissionToolBase):
    def __init__(self):
        super().__init__()
        
        self.terrain_query = TerrainQuery()
        
        self.init_ui()
        self.apply_qgc_theme()

    def init_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Tower Inspection Planner")
        self.setGeometry(100, 100, 1200, 800)

        # Add shared toolbar
        self.toolbar = SharedToolBar(self)
        self.addToolBar(self.toolbar)

        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QHBoxLayout(central_widget)

        # Left Panel: Map View
        left_layout = QtWidgets.QVBoxLayout()
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        from utils import get_map_html_path
        self.map_view.setUrl(QUrl.fromLocalFile(get_map_html_path()))
        
        # Set up communication channel for map interactions
        self.channel = QWebChannel()
        self.map_object = QtCore.QObject()
        self.map_object.setStartLocation = self.set_start_location
        self.map_object.setEndLocation = self.set_end_location
        self.map_object.receive_location = self.handle_location_selected
        self.map_object.receive_tower_location = self.handle_tower_location_selected
        self.channel.registerObject('pywebchannel', self.map_object)
        self.map_view.page().setWebChannel(self.channel)
        
        left_layout.addWidget(self.map_view)

        # Right Panel: Input Form and Buttons with scrollable area
        right_panel = QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        
        # Create scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Control container
        control_widget = QWidget()
        control_layout = QtWidgets.QVBoxLayout(control_widget)
        control_layout.setContentsMargins(20, 20, 20, 20)
        control_layout.setSpacing(15)

        # Takeoff/Landing Configuration
        takeoff_landing_group = QGroupBox("Takeoff/Landing Configuration")
        takeoff_landing_layout = QVBoxLayout(takeoff_landing_group)
        
        # Takeoff/Landing location (same location)
        takeoff_landing_layout.addWidget(QLabel("Takeoff/Landing Location:"))
        self.takeoff_landing_location_label = QLabel("Not set - Click 'Set Location' and click on map")
        self.takeoff_landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        takeoff_landing_layout.addWidget(self.takeoff_landing_location_label)
        
        location_btn_layout = QHBoxLayout()
        self.set_location_btn = QPushButton("Set Location")
        self.set_location_btn.clicked.connect(self.start_location_selection)
        location_btn_layout.addWidget(self.set_location_btn)
        
        self.clear_location_btn = QPushButton("Clear")
        self.clear_location_btn.clicked.connect(self.clear_location)
        location_btn_layout.addWidget(self.clear_location_btn)
        takeoff_landing_layout.addLayout(location_btn_layout)
        
        control_layout.addWidget(takeoff_landing_group)

        # Tower Configuration
        tower_group = QGroupBox("Tower Configuration")
        tower_layout = QVBoxLayout(tower_group)
        
        # Tower location
        tower_layout.addWidget(QLabel("Tower Location:"))
        self.tower_location_label = QLabel("Not set - Click 'Set Tower' and click on map")
        self.tower_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        tower_layout.addWidget(self.tower_location_label)
        
        tower_btn_layout = QHBoxLayout()
        self.set_tower_btn = QPushButton("Set Tower")
        self.set_tower_btn.clicked.connect(self.start_tower_selection)
        tower_btn_layout.addWidget(self.set_tower_btn)
        
        self.clear_tower_btn = QPushButton("Clear")
        self.clear_tower_btn.clicked.connect(self.clear_tower_location)
        tower_btn_layout.addWidget(self.clear_tower_btn)
        tower_layout.addLayout(tower_btn_layout)
        
        control_layout.addWidget(tower_group)

        # Offset Distance Input
        control_layout.addWidget(QLabel("Waypoint Offset Distance:"))
        offset_layout = QtWidgets.QHBoxLayout()
        self.offset_distance = QLineEdit()
        self.offset_distance.setPlaceholderText("Enter offset distance")
        offset_layout.addWidget(self.offset_distance)

        self.offset_units = QComboBox()
        self.offset_units.addItems(["Meters", "Feet"])
        offset_layout.addWidget(self.offset_units)
        control_layout.addLayout(offset_layout)


        # Generate Plan Button
        self.generate_btn = QPushButton("Generate Flight Plan")
        self.generate_btn.clicked.connect(self.generate_flight_plan)
        control_layout.addWidget(self.generate_btn)

        # Button to export flight path as KMZ/KML (initially disabled)
        self.export_btn = QPushButton("Export Flight Path (KMZ/KML)")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_flight_path)
        control_layout.addWidget(self.export_btn)

        # Set up scroll area
        scroll.setWidget(control_widget)
        right_layout.addWidget(scroll)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addWidget(right_panel, 1)
        self.setLayout(main_layout)
    
    def set_start_location(self, lat, lng):
        """Set the clicked location as the takeoff/landing coordinates (legacy method)."""
        self.handle_location_selected(lat, lng)
    
    def set_end_location(self, lat, lng):
        """Set the clicked location as the tower coordinates (legacy method)."""
        self.handle_tower_location_selected(lat, lng)
    
    def handle_location_selected(self, lat, lng):
        """Handle takeoff/landing location selection from map click."""
        self.takeoff_landing_location_label.setText(f"{lat:.6f}, {lng:.6f}")
        self.takeoff_landing_location_label.setStyleSheet("color: #00d4aa; font-style: normal;")
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "Takeoff/Landing Location Set", 
                              f"Takeoff/Landing coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
                              f"Terrain Elevation:\n{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")
    
    def handle_tower_location_selected(self, lat, lng):
        """Handle tower location selection from map click."""
        self.tower_location_label.setText(f"{lat:.6f}, {lng:.6f}")
        self.tower_location_label.setStyleSheet("color: #00d4aa; font-style: normal;")
        
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        QMessageBox.information(self, "Tower Location Set", 
                              f"Tower coordinates set to:\n{lat:.6f}, {lng:.6f}\n\n"
                              f"Terrain Elevation:\n{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")
    
    def start_location_selection(self):
        """Start takeoff/landing location selection mode."""
        self.map_view.page().runJavaScript("startLocationSelection();")
    
    def start_tower_selection(self):
        """Start tower location selection mode."""
        self.map_view.page().runJavaScript("startTowerSelection();")
    
    def clear_location(self):
        """Clear the takeoff/landing location."""
        self.takeoff_landing_location_label.setText("Not set - Click 'Set Location' and click on map")
        self.takeoff_landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
    
    def clear_tower_location(self):
        """Clear the tower location."""
        self.tower_location_label.setText("Not set - Click 'Set Tower' and click on map")
        self.tower_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
    
    # Aircraft Configuration Methods

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
        """
        self.setStyleSheet(self.styleSheet() + additional_style)

    def generate_flight_plan(self):
        try:
            # Check if locations are set
            if "Not set" in self.takeoff_landing_location_label.text():
                QMessageBox.warning(self, "Missing Takeoff/Landing Location", "Please set the takeoff/landing location by clicking 'Set Location' and clicking on the map.")
                return
                
            if "Not set" in self.tower_location_label.text():
                QMessageBox.warning(self, "Missing Tower Location", "Please set the tower location by clicking 'Set Tower' and clicking on the map.")
                return
            
            # Parse input coordinates from labels
            takeoff_lat, takeoff_lon = map(float, self.takeoff_landing_location_label.text().split(","))
            landing_lat, landing_lon = takeoff_lat, takeoff_lon  # Same location for takeoff and landing
            tower_lat, tower_lon = map(float, self.tower_location_label.text().split(","))
            
            # Get aircraft-aware values
            if self.is_parameters_enabled():
                # Use aircraft parameters for optimized values
                offset_distance = self.get_aircraft_aware_waypoint_spacing("tower_inspection", 50.0)  # Default 50m offset
                altitude_takeoff = self.get_aircraft_aware_altitude("tower_inspection", 3.048)  # 10 feet default
                altitude_inspection = self.get_aircraft_aware_altitude("tower_inspection", 30.48)  # 100 feet default
            else:
                # Use manual input values
                offset_distance = float(self.offset_distance.text())
                if self.offset_units.currentText() == "Feet":
                    offset_distance *= 0.3048  # Convert feet to meters
                altitude_takeoff = 3.048  # 10 feet (fixed for takeoff)
                altitude_inspection = 30.48  # 100 feet (fixed for inspection)

            # Define waypoints and mission items
            mission_items = self.create_mission_items(
                takeoff_lat, takeoff_lon, landing_lat, landing_lon, tower_lat, tower_lon, altitude_takeoff, altitude_inspection, offset_distance
            )

            # Define rectangular geofence
            geofence_polygon = self.create_geofence_rectangle(takeoff_lat, takeoff_lon, tower_lat, tower_lon)

            # Save the .plan file
            self.save_plan_file(takeoff_lat, takeoff_lon, mission_items, geofence_polygon)

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid coordinates and offset distance.")

    def create_mission_items(self, takeoff_lat, takeoff_lon, landing_lat, landing_lon, tower_lat, tower_lon, altitude_takeoff, altitude_inspection, offset_distance):
        """Generate mission items with user-defined takeoff, landing, and ROI."""
        mission_items = []

        # 1. Takeoff
        terrain_elevation = self.terrain_query.get_elevation(takeoff_lat, takeoff_lon)
        amsl_altitude = terrain_elevation + altitude_takeoff
        
        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,
            "Altitude": altitude_takeoff,
            "AltitudeMode": 3,
            "autoContinue": True,
            "command": 22,
            "doJumpId": 1,
            "frame": 0,
            "params": [0, 0, 0, None, takeoff_lat, takeoff_lon, amsl_altitude],
            "type": "SimpleItem",
        })

        # 2. ROI (Region of Interest) - Tower Center
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": 0,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 201,  # MAV_CMD_DO_SET_ROI_LOCATION
            "doJumpId": 2,
            "frame": 3,
            "params": [0, 0, 0, None, tower_lat, tower_lon, 0],
            "type": "SimpleItem",
        })

        # Adjust latitude and longitude offsets for the given distance
        lat_offset = offset_distance / 111320  # Approximate meters to degrees latitude
        lon_offset = offset_distance / (111320 * math.cos(math.radians(tower_lat)))

        # Generate waypoints offset from the tower
        waypoints = [
            (tower_lat + lat_offset, tower_lon + lon_offset),
            (tower_lat - lat_offset, tower_lon + lon_offset),
            (tower_lat - lat_offset, tower_lon - lon_offset),
            (tower_lat + lat_offset, tower_lon - lon_offset),
        ]

        for i, (way_lat, way_lon) in enumerate(waypoints, start=3):
            # Low-altitude waypoint
            terrain_elevation_low = self.terrain_query.get_elevation(way_lat, way_lon)
            amsl_altitude_low = terrain_elevation_low + altitude_takeoff
            
            mission_items.append({
                "AMSLAltAboveTerrain": amsl_altitude_low,
                "Altitude": altitude_takeoff,
                "AltitudeMode": 3,
                "autoContinue": True,
                "command": 16,
                "doJumpId": i * 2 - 1,
                "frame": 0,
                "params": [0, 0, 0, None, way_lat, way_lon, amsl_altitude_low],
                "type": "SimpleItem",
            })

            # High-altitude waypoint
            terrain_elevation_high = self.terrain_query.get_elevation(way_lat, way_lon)
            amsl_altitude_high = terrain_elevation_high + altitude_inspection
            
            mission_items.append({
                "AMSLAltAboveTerrain": amsl_altitude_high,
                "Altitude": altitude_inspection,
                "AltitudeMode": 3,
                "autoContinue": True,
                "command": 16,
                "doJumpId": i * 2,
                "frame": 0,
                "params": [0, 0, 0, None, way_lat, way_lon, amsl_altitude_high],
                "type": "SimpleItem",
            })

        # Return to Takeoff/Landing Location
        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,
            "Altitude": altitude_takeoff,
            "AltitudeMode": 3,
            "autoContinue": True,
            "command": 16,
            "doJumpId": len(mission_items) + 1,
            "frame": 0,
            "params": [0, 0, 0, None, takeoff_lat, takeoff_lon, amsl_altitude],
            "type": "SimpleItem",
        })

        # Land at takeoff location
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": 0,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 21,  # MAV_CMD_NAV_LAND
            "doJumpId": len(mission_items) + 2,
            "frame": 3,
            "params": [0, 0, 0, None, takeoff_lat, takeoff_lon, 0],
            "type": "SimpleItem",
        })

        return mission_items

    def create_geofence_rectangle(self, takeoff_lat, takeoff_lon, tower_lat, tower_lon):
        """Create a rectangular geofence combining takeoff and tower areas."""
        lat_offset = 0.0003  # ~30 meters offset
        lon_offset = 0.0005  # ~50 meters offset

        # Find the bounds that include both locations
        min_lat = min(takeoff_lat, tower_lat)
        max_lat = max(takeoff_lat, tower_lat)
        min_lon = min(takeoff_lon, tower_lon)
        max_lon = max(takeoff_lon, tower_lon)

        return [
            [max_lat + lat_offset, min_lon - lon_offset],
            [max_lat + lat_offset, max_lon + lon_offset],
            [min_lat - lat_offset, max_lon + lon_offset],
            [min_lat - lat_offset, min_lon - lon_offset],
        ]

    def save_plan_file(self, takeoff_lat, takeoff_lon, mission_items, geofence_polygon):
        """Save the flight plan to a .plan file."""
        # Use new file generation system instead of direct file dialog

        # Get aircraft-specific parameters using new system
        aircraft_info = self.get_aircraft_info_for_export()

        plan_data = {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [{"inclusion": True, "polygon": geofence_polygon, "version": 1}],
                "version": 2,
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": aircraft_info["cruiseSpeed"],
                "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                "globalPlanAltitudeMode": 0,
                "hoverSpeed": aircraft_info["hoverSpeed"],
                "items": mission_items,
                "plannedHomePosition": [takeoff_lat, takeoff_lon, 70],
                "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                "version": 2,
                "aircraftParameters": aircraft_info["aircraftParameters"]
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1,
        }

        # Use new file generation system
        saved_file = self.save_mission_file(plan_data, "tower_inspection")
        if saved_file:
            # Store mission items for export functionality
            self.mission_items = mission_items
            
            # Enable export button
            self.export_btn.setEnabled(True)
        
        # Check for terrain proximity warnings
        altitude_takeoff = 3.048  # 10 feet in meters
        altitude_inspection = 30.48  # 100 feet in meters
        proximity_warnings = self.check_terrain_proximity(altitude_takeoff, altitude_inspection)
        
        if proximity_warnings:
            self.show_terrain_proximity_warning(proximity_warnings)

        QMessageBox.information(self, "Plan Saved", f"Plan saved to {filename}")

    def check_terrain_proximity(self, altitude_takeoff, altitude_inspection):
        """Check if any waypoint gets too close to terrain (within 50ft/15.24m)"""
        proximity_warnings = []
        warning_threshold = 15.24  # 50 feet in meters
        
        if not hasattr(self, 'mission_items') or not self.mission_items:
            return proximity_warnings
        
        for i, waypoint in enumerate(self.mission_items):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat, lon = waypoint['params'][4], waypoint['params'][5]
                altitude = waypoint['params'][6]
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                clearance = altitude - terrain_elevation
                
                if clearance < warning_threshold:
                    proximity_warnings.append({
                        'waypoint': i + 1,
                        'lat': lat,
                        'lon': lon,
                        'terrain_elevation': terrain_elevation,
                        'clearance': clearance,
                        'altitude_agl': altitude
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
        if not hasattr(self, 'mission_items') or not self.mission_items:
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
            
            # Create KML content
            kml_content = self.generate_kml_content()
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(kml_content)
            
            QMessageBox.information(self, "Export Successful", 
                                  f"Flight path exported to:\n{filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Error exporting flight path: {str(e)}")

    def generate_kml_content(self):
        """Generate KML content for the flight path"""
        # Get waypoint data
        waypoint_data = []
        for i, waypoint in enumerate(self.mission_items):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat, lon = waypoint['params'][4], waypoint['params'][5]
                altitude = waypoint['params'][6]
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude
                waypoint_data.append({
                    'lat': lat,
                    'lon': lon,
                    'terrain_elevation': terrain_elevation,
                    'amsl_altitude': amsl_altitude,
                    'agl_altitude': altitude,
                    'waypoint_number': i + 1,
                    'command': waypoint.get('command', 'Unknown')
                })
        
        # Generate KML content
        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Tower Inspection Flight Path</name>
    <description>Tower inspection flight path generated by AutoFlightGenerator</description>
    
    <!-- Flight Path Line -->
    <Placemark>
      <name>Flight Path</name>
      <description>Tower inspection flight path with terrain following</description>
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
      <name>Waypoint {wp['waypoint_number']} ({wp['command']})</name>
      <description>
        Coordinates: {wp['lat']:.6f}, {wp['lon']:.6f}
        Terrain Elevation: {wp['terrain_elevation']:.1f}m
        AMSL Altitude: {wp['amsl_altitude']:.1f}m
        AGL Altitude: {wp['agl_altitude']:.1f}m
        Command: {wp['command']}
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
        
        # Add takeoff and tower points
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
            
            # Tower point (find the inspection waypoint)
            tower_wp = None
            for wp in waypoint_data:
                if wp['command'] == 201:  # ROI command
                    tower_wp = wp
                    break
            
            if tower_wp:
                kml_content += f"""    <Placemark>
      <name>Tower Location</name>
      <description>
        Tower inspection location
        Coordinates: {tower_wp['lat']:.6f}, {tower_wp['lon']:.6f}
        Terrain Elevation: {tower_wp['terrain_elevation']:.1f}m
        AMSL Altitude: {tower_wp['amsl_altitude']:.1f}m
      </description>
      <Style>
        <IconStyle>
          <color>ffff0000</color>
          <scale>1.5</scale>
        </IconStyle>
      </Style>
      <Point>
        <coordinates>{tower_wp['lon']:.6f},{tower_wp['lat']:.6f},{tower_wp['amsl_altitude']:.1f}</coordinates>
      </Point>
    </Placemark>
"""
        
        kml_content += """  </Document>
</kml>"""
        
        return kml_content

    def apply_settings(self):
        """Apply current settings to the flight plan generation."""
        # This method can be used to apply any settings changes
        pass

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not hasattr(self, 'mission_items') or not self.mission_items:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters
        altitude_meters = 3.048  # Default to 10 feet (fixed for takeoff)
        try:
            altitude_meters = float(self.offset_distance.text()) * 0.3048  # Convert feet to meters
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid altitude in feet.")
            return
        
        # Extract waypoint data from the mission_items list
        waypoint_coords = []
        for i, waypoint in enumerate(self.mission_items):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat = waypoint['params'][4]
                lon = waypoint['params'][5]
                waypoint_coords.append((lat, lon))
        
        if not waypoint_coords:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return
        
        # Get terrain elevation data for all waypoints
        terrain_elevations = []
        amsl_altitudes = []
        agl_altitudes = []
        
        for lat, lon in waypoint_coords:
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            terrain_elevations.append(terrain_elevation)
            
            # Calculate AMSL altitude (terrain + AGL)
            amsl_altitude = terrain_elevation + altitude_meters
            amsl_altitudes.append(amsl_altitude)
            agl_altitudes.append(altitude_meters)
        
        # Convert to feet for display
        terrain_elevations_ft = [elev * 3.28084 for elev in terrain_elevations]
        amsl_altitudes_ft = [alt * 3.28084 for alt in amsl_altitudes]
        agl_altitudes_ft = [alt * 3.28084 for alt in agl_altitudes]
        
        # Calculate distances
        distances = []
        total_distance = 0
        prev_lat = None
        prev_lon = None
        
        for lat, lon in waypoint_coords:
            if prev_lat is not None and prev_lon is not None:
                distance = self.haversine_distance(prev_lat, prev_lon, lat, lon)
                total_distance += distance
            else:
                distance = 0
            distances.append(total_distance)
            prev_lat = lat
            prev_lon = lon
        
        # Convert distances to feet
        distances_ft = [d * 3.28084 for d in distances]
        
        # Create matplotlib visualization
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 10))
        
        # Plot altitude profile with terrain
        waypoint_indices = list(range(len(waypoint_coords)))
        
        plt.subplot(2, 1, 1)
        plt.plot(distances_ft, amsl_altitudes_ft, 'b-', linewidth=2, label='AMSL Altitude (feet)')
        plt.plot(distances_ft, terrain_elevations_ft, 'g-', linewidth=2, label='Terrain Elevation (feet)')
        plt.plot(distances_ft, agl_altitudes_ft, 'r--', linewidth=2, label='AGL Altitude (feet)')
        plt.xlabel('Distance (feet)')
        plt.ylabel('Altitude (feet)')
        plt.title('Tower Inspection Altitude Profile with Terrain')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Fill area between AMSL and terrain to show flight corridor
        plt.fill_between(distances_ft, terrain_elevations_ft, amsl_altitudes_ft, alpha=0.2, color='blue', label='Flight Corridor')
        
        # Add waypoint markers
        for i, (dist, amsl_alt) in enumerate(zip(distances_ft, amsl_altitudes_ft)):
            plt.plot(dist, amsl_alt, 'o', color='orange', markersize=8, markeredgecolor='black', markeredgewidth=2)
            if i == 0:
                plt.annotate('T/O', (dist, amsl_alt), xytext=(5, 5), textcoords='offset points', 
                           fontsize=10, fontweight='bold')
            elif i == len(waypoint_coords) - 1:
                plt.annotate('LND', (dist, amsl_alt), xytext=(5, 5), textcoords='offset points', 
                           fontsize=10, fontweight='bold')
            else:
                plt.annotate(str(i), (dist, amsl_alt), xytext=(5, 5), textcoords='offset points', 
                           fontsize=10, fontweight='bold')
        
        # Add statistics text
        plt.subplot(2, 1, 2)
        plt.axis('off')
        
        # Calculate statistics
        min_terrain = min(terrain_elevations_ft)
        max_terrain = max(terrain_elevations_ft)
        avg_terrain = sum(terrain_elevations_ft) / len(terrain_elevations_ft)
        min_amsl = min(amsl_altitudes_ft)
        max_amsl = max(amsl_altitudes_ft)
        avg_amsl = sum(amsl_altitudes_ft) / len(amsl_altitudes_ft)
        
        stats_text = f"""Tower Inspection Altitude Profile Summary
=========================================

Total Waypoints: {len(waypoint_coords)}
AGL Altitude: {altitude_meters * 3.28084:.1f} feet

Terrain Elevation Statistics:
- Minimum: {min_terrain:.1f} feet
- Maximum: {max_terrain:.1f} feet
- Average: {avg_terrain:.1f} feet
- Range: {max_terrain - min_terrain:.1f} feet

AMSL Altitude Statistics:
- Minimum: {min_amsl:.1f} feet
- Maximum: {max_amsl:.1f} feet
- Average: {avg_amsl:.1f} feet
- Range: {max_amsl - min_amsl:.1f} feet

Flight Plan Summary:
- Start Point: {waypoint_coords[0] if waypoint_coords else 'N/A'}
- End Point: {waypoint_coords[-1] if waypoint_coords else 'N/A'}
- Total Distance: {total_distance * 3.28084:.1f} feet

All waypoints will fly at {altitude_meters * 3.28084:.1f} feet AGL.
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

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula."""
        import math
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c

    def apply_qgc_theme(self):
        """Apply QGroundControl-inspired dark theme styling."""
        # Import the dark theme from utils
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


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = TowerInspection()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
