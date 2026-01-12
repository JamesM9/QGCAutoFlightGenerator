#!/usr/bin/env python3
"""
Enhanced Structure Scan Flight Tool - 3D Structure Scanning Mission Planning
Features:
- Interactive polygon drawing on map for scan area definition
- QGroundControl-compatible structure scan pattern generation
- Terrain-aware altitude planning
- Multiple structure type support
"""

import sys
import json
import requests
import time
import math
import random
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, Point
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, QThread, pyqtSlot, QTimer
from PyQt5.QtWebChannel import QWebChannel
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit,
    QSpinBox, QDoubleSpinBox, QLineEdit, QHBoxLayout, QProgressBar, QComboBox, QMessageBox,
    QGroupBox, QGridLayout, QSplitter, QFrame, QScrollArea
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont
from cpu_optimizer import (get_optimized_terrain_query, get_optimized_mission_generator, 
                          get_optimized_waypoint_optimizer, create_optimized_progress_dialog)
from shared_toolbar import SharedToolBar
# Import new aircraft parameter system
from aircraft_parameters import MissionToolBase

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
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0


class StructureScanMapBridge(QObject):
    """Bridge class for QWebChannel communication."""
    
    @pyqtSlot(list)
    def receive_polygon(self, coordinates):
        """Receive polygon coordinates from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_polygon_received(coordinates)
    
    @pyqtSlot(float, float)
    def receive_map_click(self, lat, lng):
        """Receive map click from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
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
    def start_drawing_mode(self):
        """Start drawing mode from Python."""
        pass  # This will be called from Python to trigger JavaScript
    
    @pyqtSlot()
    def clear_drawing_mode(self):
        """Clear drawing mode from Python."""
        pass  # This will be called from Python to trigger JavaScript


class StructureScan(MissionToolBase):
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("structure_scan")
        self.mission_generator = get_optimized_mission_generator("structure_scan")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("structure_scan")
        
        self.polygon_coordinates = []
        self.polygon = None
        self.waypoints = []
        self.takeoff_location = None
        self.landing_location = None
        self.init_ui()
        self.apply_qgc_theme()

    def init_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Structure Scan Generator")
        self.resize(1600, 900)

        # Add shared toolbar
        self.toolbar = SharedToolBar(self)
        self.addToolBar(self.toolbar)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panels
        splitter = QSplitter(QtCore.Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left control panel
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)

        # Right map panel
        map_panel = self.create_map_panel()
        splitter.addWidget(map_panel)

        # Set splitter proportions (50% controls, 50% map)
        splitter.setSizes([800, 800])

    def create_control_panel(self):
        """Create the left control panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel_layout = QVBoxLayout(panel)
        
        # Create scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # Control container
        control_widget = QWidget()
        layout = QVBoxLayout(control_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("Structure Scan Generator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Structure Configuration Group
        structure_group = QGroupBox("Structure Configuration")
        structure_layout = QGridLayout(structure_group)

        # Structure type selection (spans both columns)
        structure_layout.addWidget(QLabel("Structure Type:"), 0, 0)
        self.structure_type_combo = QComboBox()
        self.structure_type_combo.addItems(["Building/Tower", "Bridge", "Industrial Structure", "Custom Structure"])
        self.structure_type_combo.setCurrentText("Building/Tower")
        self.structure_type_combo.currentTextChanged.connect(self.on_structure_type_changed)
        structure_layout.addWidget(self.structure_type_combo, 0, 1, 1, 2)

        # Structure dimensions - Column 1
        structure_layout.addWidget(QLabel("Structure Height (m):"), 1, 0)
        self.structure_height_input = QDoubleSpinBox()
        self.structure_height_input.setRange(1, 1000)
        self.structure_height_input.setValue(50)
        structure_layout.addWidget(self.structure_height_input, 1, 1)

        structure_layout.addWidget(QLabel("Structure Width (m):"), 2, 0)
        self.structure_width_input = QDoubleSpinBox()
        self.structure_width_input.setRange(1, 500)
        self.structure_width_input.setValue(20)
        structure_layout.addWidget(self.structure_width_input, 2, 1)

        structure_layout.addWidget(QLabel("Structure Depth (m):"), 3, 0)
        self.structure_depth_input = QDoubleSpinBox()
        self.structure_depth_input.setRange(1, 500)
        self.structure_depth_input.setValue(20)
        structure_layout.addWidget(self.structure_depth_input, 3, 1)

        # Scan settings - Column 1
        structure_layout.addWidget(QLabel("Scan Altitude (m):"), 4, 0)
        self.scan_altitude_input = QDoubleSpinBox()
        self.scan_altitude_input.setRange(5, 200)
        self.scan_altitude_input.setValue(30)
        structure_layout.addWidget(self.scan_altitude_input, 4, 1)

        structure_layout.addWidget(QLabel("Scan Distance (m):"), 5, 0)
        self.scan_distance_input = QDoubleSpinBox()
        self.scan_distance_input.setRange(5, 100)
        self.scan_distance_input.setValue(20)
        structure_layout.addWidget(self.scan_distance_input, 5, 1)

        structure_layout.addWidget(QLabel("Entrance/Exit Alt (m):"), 6, 0)
        self.entrance_altitude_input = QDoubleSpinBox()
        self.entrance_altitude_input.setRange(5, 200)
        self.entrance_altitude_input.setValue(30)
        structure_layout.addWidget(self.entrance_altitude_input, 6, 1)

        structure_layout.addWidget(QLabel("Scan Bottom Alt (m):"), 7, 0)
        self.scan_bottom_alt_input = QDoubleSpinBox()
        self.scan_bottom_alt_input.setRange(0, 100)
        self.scan_bottom_alt_input.setValue(0)
        structure_layout.addWidget(self.scan_bottom_alt_input, 7, 1)

        # Camera settings - Column 2
        structure_layout.addWidget(QLabel("Camera Angle (°):"), 1, 2)
        self.camera_angle_input = QDoubleSpinBox()
        self.camera_angle_input.setRange(0, 90)
        self.camera_angle_input.setValue(45)
        structure_layout.addWidget(self.camera_angle_input, 1, 3)

        structure_layout.addWidget(QLabel("Photo Interval (°):"), 2, 2)
        self.photo_interval_input = QDoubleSpinBox()
        self.photo_interval_input.setRange(1, 100)
        self.photo_interval_input.setValue(10)
        structure_layout.addWidget(self.photo_interval_input, 2, 3)

        # Scan pattern options - Column 2
        structure_layout.addWidget(QLabel("Vertical Layers:"), 3, 2)
        self.vertical_layers_input = QSpinBox()
        self.vertical_layers_input.setRange(1, 20)
        self.vertical_layers_input.setValue(5)
        structure_layout.addWidget(self.vertical_layers_input, 3, 3)

        structure_layout.addWidget(QLabel("Orbit Direction:"), 4, 2)
        self.orbit_direction_combo = QComboBox()
        self.orbit_direction_combo.addItems(["Clockwise", "Counter-clockwise"])
        structure_layout.addWidget(self.orbit_direction_combo, 4, 3)

        structure_layout.addWidget(QLabel("Start From:"), 5, 2)
        self.start_from_combo = QComboBox()
        self.start_from_combo.addItems(["Top", "Bottom"])
        self.start_from_combo.setCurrentText("Top")
        structure_layout.addWidget(self.start_from_combo, 5, 3)

        layout.addWidget(structure_group)

        # Takeoff/Landing Configuration Group
        takeoff_landing_group = QGroupBox("Takeoff & Landing Configuration")
        takeoff_landing_layout = QVBoxLayout(takeoff_landing_group)

        # Same location option
        self.same_location_checkbox = QComboBox()
        self.same_location_checkbox.addItems(["Same Location", "Different Locations"])
        self.same_location_checkbox.currentTextChanged.connect(self.on_location_mode_changed)
        takeoff_landing_layout.addWidget(QLabel("Takeoff/Landing Mode:"))
        takeoff_landing_layout.addWidget(self.same_location_checkbox)

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

        # Landing location (initially hidden)
        self.landing_location_label = QLabel("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.landing_location_label.setVisible(False)
        takeoff_landing_layout.addWidget(self.landing_location_label)

        landing_btn_layout = QHBoxLayout()
        self.set_landing_btn = QPushButton("Set Landing")
        self.set_landing_btn.clicked.connect(self.start_landing_selection)
        self.set_landing_btn.setVisible(False)
        landing_btn_layout.addWidget(self.set_landing_btn)

        self.clear_landing_btn = QPushButton("Clear")
        self.clear_landing_btn.clicked.connect(self.clear_landing_location)
        self.clear_landing_btn.setVisible(False)
        landing_btn_layout.addWidget(self.clear_landing_btn)
        takeoff_landing_layout.addLayout(landing_btn_layout)

        layout.addWidget(takeoff_landing_group)


        # Vehicle Configuration Group (fallback)
        vehicle_group = QGroupBox("Vehicle Configuration")
        vehicle_layout = QGridLayout(vehicle_group)

        # Vehicle type selection (spans both columns)
        vehicle_layout.addWidget(QLabel("Vehicle Type:"), 0, 0)
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems(["Multicopter", "Fixed-Wing", "VTOL"])
        self.vehicle_type_combo.setCurrentText("Multicopter")
        vehicle_layout.addWidget(self.vehicle_type_combo, 0, 1, 1, 2)

        # Speed settings - Column 1
        vehicle_layout.addWidget(QLabel("Cruise Speed (m/s):"), 1, 0)
        self.cruise_speed_input = QDoubleSpinBox()
        self.cruise_speed_input.setRange(1, 50)
        self.cruise_speed_input.setValue(5)
        vehicle_layout.addWidget(self.cruise_speed_input, 1, 1)

        # Speed settings - Column 2
        vehicle_layout.addWidget(QLabel("Hover Speed (m/s):"), 1, 2)
        self.hover_speed_input = QDoubleSpinBox()
        self.hover_speed_input.setRange(0, 20)
        self.hover_speed_input.setValue(2)
        vehicle_layout.addWidget(self.hover_speed_input, 1, 3)

        layout.addWidget(vehicle_group)

        # Polygon Drawing Group
        polygon_group = QGroupBox("Scan Area Definition")
        polygon_layout = QVBoxLayout(polygon_group)

        # Drawing instructions
        instructions = QLabel(
            "1. Click 'Start Drawing' to begin\n"
            "2. Click on the map to add polygon points\n"
            "3. Double-click to finish the polygon\n"
            "4. Use 'Clear Polygon' to start over"
        )
        instructions.setWordWrap(True)
        polygon_layout.addWidget(instructions)

        # Drawing buttons
        button_layout = QHBoxLayout()
        self.start_drawing_btn = QPushButton("Start Drawing")
        self.start_drawing_btn.clicked.connect(self.start_polygon_drawing)
        button_layout.addWidget(self.start_drawing_btn)

        self.clear_polygon_btn = QPushButton("Clear Polygon")
        self.clear_polygon_btn.clicked.connect(self.clear_polygon)
        button_layout.addWidget(self.clear_polygon_btn)

        polygon_layout.addLayout(button_layout)

        # Load KML button
        self.load_kml_btn = QPushButton("Load KML File")
        self.load_kml_btn.clicked.connect(self.load_kml_file)
        polygon_layout.addWidget(self.load_kml_btn)

        layout.addWidget(polygon_group)

        # Mission Generation Group
        mission_group = QGroupBox("Mission Generation")
        mission_layout = QVBoxLayout(mission_group)

        # Generate button
        self.generate_btn = QPushButton("Generate Structure Scan")
        self.generate_btn.clicked.connect(self.generate_scan)
        self.generate_btn.setEnabled(False)
        mission_layout.addWidget(self.generate_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        mission_layout.addWidget(self.progress_bar)

        # Export button
        self.export_btn = QPushButton("Export Flight Plan")
        self.export_btn.clicked.connect(self.export_flight_plan)
        self.export_btn.setEnabled(False)
        mission_layout.addWidget(self.export_btn)

        layout.addWidget(mission_group)



        # Add stretch to push everything to the top
        layout.addStretch()

        # Set up scroll area
        scroll.setWidget(control_widget)
        panel_layout.addWidget(scroll)

        return panel

    def create_map_panel(self):
        """Create the right map panel."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to maximize map space

        # Create web view for map (no title, map fills entire panel)
        self.web_view = QWebEngineView()
        layout.addWidget(self.web_view)

        # Setup web channel for communication
        self.setup_web_channel()

        # Load the enhanced map
        self.load_enhanced_map()

        return panel

    def setup_web_channel(self):
        """Setup communication between Python and JavaScript."""
        self.channel = QWebChannel()
        
        # Create bridge object for QWebChannel communication
        self.map_bridge = StructureScanMapBridge()
        self.map_bridge.parent_widget = self
        
        self.channel.registerObject('pywebchannel', self.map_bridge)
        self.web_view.page().setWebChannel(self.channel)

    def load_enhanced_map(self):
        """Load the enhanced map with polygon drawing capabilities."""
        # Create enhanced map HTML content
        map_html = self.create_enhanced_map_html()
        
        # Create a temporary HTML file (like the working tools)
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(map_html)
            temp_path = f.name
        
        self.web_view.setUrl(QUrl.fromLocalFile(temp_path))
        
        # Clean up the temporary file after loading
        QTimer.singleShot(1000, lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)

    def create_enhanced_map_html(self):
        """Create enhanced map HTML with polygon drawing capabilities."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Structure Scan Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                  crossorigin=""/>
            
            <!-- Leaflet Draw CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.css"/>
            
            <!-- Leaflet JavaScript -->
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                    crossorigin=""></script>
            
            <!-- Leaflet Draw JavaScript -->
            <script src="https://unpkg.com/leaflet-draw@1.0.4/dist/leaflet.draw.js"></script>
            
            <!-- Leaflet GeometryUtil for area calculations -->
            <script src="https://unpkg.com/leaflet-geometryutil@0.10.0/src/leaflet.geometryutil.js"></script>
            
            <!-- QWebChannel JavaScript -->
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }
                #map {
                    width: 100%;
                    height: 100vh;
                }
                .info-panel {
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    z-index: 1000;
                    max-width: 300px;
                }
                .drawing-controls {
                    position: absolute !important;
                    bottom: 10px !important;
                    right: 10px !important;
                    background: white !important;
                    padding: 15px !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
                    z-index: 1000 !important;
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    min-width: 150px !important;
                }
                .drawing-controls h4 {
                    margin: 0 0 10px 0 !important;
                    color: #333 !important;
                    font-size: 14px !important;
                    text-align: center !important;
                }
                .drawing-controls button {
                    width: 100% !important;
                    margin-bottom: 8px !important;
                    padding: 10px !important;
                    border: none !important;
                    border-radius: 4px !important;
                    cursor: pointer !important;
                    font-weight: bold !important;
                    font-size: 12px !important;
                    display: block !important;
                }
                .drawing-controls button#start-drawing {
                    background: #007bff !important;
                    color: white !important;
                }
                .drawing-controls button#finish-drawing {
                    background: #28a745 !important;
                    color: white !important;
                }
                .drawing-controls button#clear-polygon {
                    background: #dc3545 !important;
                    color: white !important;
                }
                .point-marker {
                    background-color: red;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    border: 2px solid white;
                }
                .takeoff-marker {
                    background-color: #28a745;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                .landing-marker {
                    background-color: #dc3545;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                }
                
                /* Coordinate popup styles (match map.html) */
                .coordinate-popup { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; }
                .coordinate-popup .label { font-weight: bold; color: #333; }
                .coordinate-popup .value { color: #666; font-family: 'Courier New', monospace; }
                .elevation-info { margin-top: 8px; padding-top: 8px; border-top: 1px solid #ccc; }
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <div class="info-panel">
                <h4>Structure Scan Area Drawing</h4>
                <p><strong>Points:</strong> <span id="point-count">0</span></p>
                <p><strong>Area:</strong> <span id="area-size">0</span> km²</p>
            </div>
            
            <!-- Drawing Controls -->
            <div class="drawing-controls">
                <h4>Drawing Tools</h4>
                <button id="start-drawing">Start Drawing</button>
                <button id="finish-drawing" disabled>Finish Polygon</button>
                <button id="clear-polygon">Clear</button>
            </div>
            
            <script>
                // Initialize QWebChannel
                let pywebchannel;
                new QWebChannel(qt.webChannelTransport, function(channel) {
                    pywebchannel = channel.objects.pywebchannel;
                    console.log('QWebChannel initialized');
                });
                
                // Initialize map
                let map = L.map('map').setView([40.7128, -74.0060], 10);
                
                // Elevation and coordinate helpers (same as map.html)
                async function getElevation(lat, lng) {
                    try {
                        const response = await fetch(`https://api.open-elevation.com/api/v1/lookup?locations=${lat},${lng}`);
                        const data = await response.json();
                        if (data.results && data.results.length > 0) {
                            return data.results[0].elevation;
                        } else {
                            throw new Error('No elevation data');
                        }
                    } catch (e) {
                        console.error('Elevation fetch error', e);
                        return null;
                    }
                }

                function formatCoordinates(lat, lng) {
                    const latDeg = Math.floor(Math.abs(lat));
                    const latMin = (Math.abs(lat) - latDeg) * 60;
                    const latSec = (latMin - Math.floor(latMin)) * 60;
                    const latDir = lat >= 0 ? 'N' : 'S';
                    const lngDeg = Math.floor(Math.abs(lng));
                    const lngMin = (Math.abs(lng) - lngDeg) * 60;
                    const lngSec = (lngMin - Math.floor(lngMin)) * 60;
                    const lngDir = lng >= 0 ? 'E' : 'W';
                    return {
                        decimal: `${lat.toFixed(6)}, ${lng.toFixed(6)}`,
                        dms: `${latDeg}°${Math.floor(latMin)}'${latSec.toFixed(2)}"${latDir}, ${lngDeg}°${Math.floor(lngMin)}'${lngSec.toFixed(2)}"${lngDir}`
                    };
                }

                function createPopupContent(lat, lng, elevation = null) {
                    const coords = formatCoordinates(lat, lng);
                    let elevationHtml = '';
                    
                    if (elevation !== null) {
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="label">Elevation:</div>
                                <div class="value">${elevation.toFixed(1)} meters (${(elevation * 3.28084).toFixed(1)} feet)</div>
                            </div>
                        `;
                    } else if (elevation === null) {
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="loading">Loading elevation data...</div>
                            </div>
                        `;
                    } else {
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="error">Elevation data unavailable</div>
                            </div>
                        `;
                    }
                    
                    return `
                        <div class="coordinate-popup">
                            <div class="label">Decimal Coordinates:</div>
                            <div class="value">${coords.decimal}</div>
                            <div class="label">DMS Coordinates:</div>
                            <div class="value">${coords.dms}</div>
                            ${elevationHtml}
                        </div>
                    `;
                }
                
                // Add tile layers with updated sources for the most current maps
                // 1. OpenStreetMap - Latest community-driven street data
                let openStreetMapLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 19
                });
                
                // 2. CartoDB Positron - Clean, modern street map with latest data
                let cartoPositronLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                });
                
                // 3. CartoDB Voyager - Enhanced street map with more details and latest updates
                let cartoVoyagerLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                });
                
                // 4. High-Resolution Satellite (Esri World Imagery) - Latest satellite imagery
                let satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                });
                
                // 5. Google Satellite - Alternative high-resolution satellite source (DEFAULT LAYER)
                let googleSatelliteLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
                    attribution: '© Google',
                    maxZoom: 20
                }).addTo(map);
                
                // 6. Hybrid layer (Satellite + Labels)
                let hybridLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                });
                
                // 7. Hybrid labels layer
                let hybridLabelsLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                });
                
                // 8. Terrain layer with contours and elevation data
                let terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
                    attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                    maxZoom: 17
                });
                
                // Create layer groups with updated options
                let baseMaps = {
                    "OpenStreetMap": openStreetMapLayer,
                    "CartoDB Light": cartoPositronLayer,
                    "CartoDB Voyager": cartoVoyagerLayer,
                    "Satellite (Esri)": satelliteLayer,
                    "Satellite (Google)": googleSatelliteLayer,
                    "Hybrid": L.layerGroup([hybridLayer, hybridLabelsLayer]),
                    "Terrain": terrainLayer
                };
                
                // Add layer control
                L.control.layers(baseMaps).addTo(map);
                
                // Drawing variables
                let drawing = false;
                let polygonPoints = [];
                let polygonLayer = null;
                let pointMarkers = [];
                
                // Location selection variables
                let takeoffSelectionMode = false;
                let landingSelectionMode = false;
                let takeoffMarker = null;
                let landingMarker = null;
                
                function startDrawing() {
                    drawing = true;
                    takeoffSelectionMode = false;
                    landingSelectionMode = false;
                    polygonPoints = [];
                    clearMarkers();
                    document.getElementById('start-drawing').disabled = true;
                    document.getElementById('finish-drawing').disabled = false;
                    document.getElementById('start-drawing').classList.add('active');
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function startTakeoffSelection() {
                    drawing = false;
                    takeoffSelectionMode = true;
                    landingSelectionMode = false;
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function startLandingSelection() {
                    drawing = false;
                    takeoffSelectionMode = false;
                    landingSelectionMode = true;
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function finishPolygon() {
                    if (polygonPoints.length < 3) {
                        alert('Need at least 3 points to create a polygon');
                        return;
                    }
                    
                    drawing = false;
                    takeoffSelectionMode = false;
                    landingSelectionMode = false;
                    document.getElementById('start-drawing').disabled = false;
                    document.getElementById('finish-drawing').disabled = true;
                    document.getElementById('start-drawing').classList.remove('active');
                    map.getContainer().style.cursor = '';
                    
                    if (polygonLayer) {
                        map.removeLayer(polygonLayer);
                    }
                    
                    polygonLayer = L.polygon(polygonPoints, {
                        color: 'red',
                        weight: 2,
                        fillColor: '#f03',
                        fillOpacity: 0.2
                    }).addTo(map);
                    
                    let area = L.GeometryUtil.geodesicArea(polygonPoints);
                    let areaKm2 = (area / 1000000).toFixed(2);
                    document.getElementById('area-size').textContent = areaKm2;
                    
                    if (pywebchannel) {
                        pywebchannel.receive_polygon(polygonPoints);
                    }
                }
                
                function clearPolygon() {
                    drawing = false;
                    takeoffSelectionMode = false;
                    landingSelectionMode = false;
                    polygonPoints = [];
                    clearMarkers();
                    document.getElementById('start-drawing').disabled = false;
                    document.getElementById('finish-drawing').disabled = true;
                    document.getElementById('start-drawing').classList.remove('active');
                    map.getContainer().style.cursor = '';
                    
                    if (polygonLayer) {
                        map.removeLayer(polygonLayer);
                        polygonLayer = null;
                    }
                    
                    document.getElementById('point-count').textContent = '0';
                    document.getElementById('area-size').textContent = '0';
                }
                
                function clearTakeoffMarker() {
                    if (takeoffMarker) {
                        map.removeLayer(takeoffMarker);
                        takeoffMarker = null;
                    }
                }
                
                function clearLandingMarker() {
                    if (landingMarker) {
                        map.removeLayer(landingMarker);
                        landingMarker = null;
                    }
                }
                
                function clearMarkers() {
                    pointMarkers.forEach(marker => map.removeLayer(marker));
                    pointMarkers = [];
                }
                

                
                // Map click handler
                map.on('click', async function(e) {
                    let lat = e.latlng.lat;
                    let lng = e.latlng.lng;
                    
                    if (drawing) {
                        polygonPoints.push([lat, lng]);
                        
                        let marker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'point-marker',
                                html: '<div style="background-color: red; width: 8px; height: 8px; border-radius: 50%; border: 2px solid white;"></div>',
                                iconSize: [12, 12]
                            })
                        }).addTo(map);
                        pointMarkers.push(marker);
                        
                        document.getElementById('point-count').textContent = polygonPoints.length;
                        
                        if (polygonPoints.length > 1) {
                            let line = L.polyline(polygonPoints.slice(-2), {
                                color: 'red',
                                weight: 2,
                                dashArray: '5, 5'
                            }).addTo(map);
                            setTimeout(() => map.removeLayer(line), 2000);
                        }
                    } else if (takeoffSelectionMode) {
                        // Clear existing takeoff marker
                        clearTakeoffMarker();
                        
                        // Add new takeoff marker
                        takeoffMarker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'takeoff-marker',
                                html: '<div style="background-color: #28a745; width: 12px; height: 12px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
                                iconSize: [18, 18]
                            })
                        }).addTo(map);
                        
                        takeoffMarker.bindPopup('<b>Takeoff Location</b><br>' + lat.toFixed(6) + ', ' + lng.toFixed(6));
                        
                        takeoffSelectionMode = false;
                        map.getContainer().style.cursor = '';
                        
                        if (pywebchannel) {
                            pywebchannel.receive_takeoff_location(lat, lng);
                        }
                    } else if (landingSelectionMode) {
                        // Clear existing landing marker
                        clearLandingMarker();
                        
                        // Add new landing marker
                        landingMarker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'landing-marker',
                                html: '<div style="background-color: #dc3545; width: 12px; height: 12px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
                                iconSize: [18, 18]
                            })
                        }).addTo(map);
                        
                        landingMarker.bindPopup('<b>Landing Location</b><br>' + lat.toFixed(6) + ', ' + lng.toFixed(6));
                        
                        landingSelectionMode = false;
                        map.getContainer().style.cursor = '';
                        
                        if (pywebchannel) {
                            pywebchannel.receive_landing_location(lat, lng);
                        }
                    } else {
                        // Show coordinate/elevation popup when not in drawing or selection modes
                        const popup = L.popup()
                            .setLatLng([lat, lng])
                            .setContent(createPopupContent(lat, lng, null))
                            .openOn(map);
                        
                        // Fetch elevation and update popup
                        const elevation = await getElevation(lat, lng);
                        if (elevation !== null) {
                            popup.setContent(createPopupContent(lat, lng, elevation));
                        }
                        
                        // Also call Python method if available
                        if (pywebchannel && pywebchannel.receive_map_click) {
                            pywebchannel.receive_map_click(lat, lng);
                        }
                    }
                });
                
                // Double-click to finish polygon
                map.on('dblclick', function(e) {
                    if (drawing && polygonPoints.length >= 3) {
                        finishPolygon();
                    }
                });
                
                // Drawing controls event listeners
                document.addEventListener('DOMContentLoaded', function() {
                    const startDrawingBtn = document.getElementById('start-drawing');
                    const finishDrawingBtn = document.getElementById('finish-drawing');
                    const clearPolygonBtn = document.getElementById('clear-polygon');
                    
                    if (startDrawingBtn) {
                        startDrawingBtn.addEventListener('click', startDrawing);
                    }
                    if (finishDrawingBtn) {
                        finishDrawingBtn.addEventListener('click', finishPolygon);
                    }
                    if (clearPolygonBtn) {
                        clearPolygonBtn.addEventListener('click', clearPolygon);
                    }
                });
            </script>
        </body>
        </html>
        """

    def on_structure_type_changed(self, structure_type):
        """Update default values based on structure type"""
        if structure_type == "Building/Tower":
            self.structure_height_input.setValue(50)
            self.structure_width_input.setValue(20)
            self.structure_depth_input.setValue(20)
            self.scan_distance_input.setValue(20)
            self.entrance_altitude_input.setValue(60)
            self.scan_bottom_alt_input.setValue(10)
        elif structure_type == "Bridge":
            self.structure_height_input.setValue(30)
            self.structure_width_input.setValue(100)
            self.structure_depth_input.setValue(20)
            self.scan_distance_input.setValue(30)
            self.entrance_altitude_input.setValue(50)
            self.scan_bottom_alt_input.setValue(5)
        elif structure_type == "Industrial Structure":
            self.structure_height_input.setValue(25)
            self.structure_width_input.setValue(50)
            self.structure_depth_input.setValue(50)
            self.scan_distance_input.setValue(25)
            self.entrance_altitude_input.setValue(45)
            self.scan_bottom_alt_input.setValue(5)

    def on_location_mode_changed(self, mode):
        """Handle location mode change (same vs different locations)"""
        if mode == "Same Location":
            self.landing_location_label.setVisible(False)
            self.set_landing_btn.setVisible(False)
            self.clear_landing_btn.setVisible(False)
            # Clear landing location when switching to same location mode
            self.landing_location = None
            self.landing_location_label.setText("Not set - Click 'Set Landing' and click on map")
        else:  # Different Locations
            self.landing_location_label.setVisible(True)
            self.set_landing_btn.setVisible(True)
            self.clear_landing_btn.setVisible(True)

    def start_takeoff_selection(self):
        """Start takeoff location selection mode."""
        self.web_view.page().runJavaScript("startTakeoffSelection();")

    def start_landing_selection(self):
        """Start landing location selection mode."""
        self.web_view.page().runJavaScript("startLandingSelection();")

    def clear_takeoff_location(self):
        """Clear the takeoff location."""
        self.takeoff_location = None
        self.takeoff_location_label.setText("Not set - Click 'Set Takeoff' and click on map")
        self.takeoff_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.web_view.page().runJavaScript("clearTakeoffMarker();")

    def clear_landing_location(self):
        """Clear the landing location."""
        self.landing_location = None
        self.landing_location_label.setText("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.web_view.page().runJavaScript("clearLandingMarker();")

    def handle_takeoff_location_selected(self, lat, lng):
        """Handle takeoff location selection from map."""
        self.takeoff_location = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.takeoff_location_label.setText(f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.takeoff_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # If same location mode, also set landing location
        if self.same_location_checkbox.currentText() == "Same Location":
            self.landing_location = {"lat": lat, "lng": lng}
            self.landing_location_label.setText(f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
            self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def handle_landing_location_selected(self, lat, lng):
        """Handle landing location selection from map."""
        self.landing_location = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.landing_location_label.setText(f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

    def start_polygon_drawing(self):
        """Start polygon drawing mode."""
        self.web_view.page().runJavaScript("startDrawing();")

    def clear_polygon(self):
        """Clear the current polygon."""
        self.polygon_coordinates = []
        self.polygon = None
        self.generate_btn.setEnabled(False)
        self.web_view.page().runJavaScript("clearPolygon();")

    def handle_polygon_received(self, coordinates):
        """Handle polygon coordinates received from JavaScript via bridge."""
        print(f"Polygon received with {len(coordinates)} coordinates")
        self.polygon_coordinates = coordinates
        if len(coordinates) >= 3:
            self.polygon = Polygon(coordinates)
            area_km2 = self.polygon.area * 111 * 111
            
            coord_display = "\n".join([f"Point {i+1}: {lat:.6f}, {lng:.6f}" for i, (lat, lng) in enumerate(coordinates)])
            
            self.generate_btn.setEnabled(True)
        else:
            pass

    def handle_map_click(self, lat, lng):
        """Handle map click events with coordinate display."""
        # The popup is now handled by the JavaScript createPopupContent function
        # No need to show a QMessageBox dialog
        pass

    def decimal_to_dms(self, decimal_degrees):
        """Convert decimal degrees to degrees, minutes, seconds format."""
        degrees = int(decimal_degrees)
        minutes_decimal = abs(decimal_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        return degrees, minutes, seconds

    def format_dms(self, lat, lon):
        """Format coordinates in DMS format."""
        lat_deg, lat_min, lat_sec = self.decimal_to_dms(lat)
        lon_deg, lon_min, lon_sec = self.decimal_to_dms(abs(lon))
        
        lat_dir = "N" if lat >= 0 else "S"
        lon_dir = "E" if lon >= 0 else "W"
        
        return f"{lat_deg}°{lat_min}'{lat_sec:.2f}\"{lat_dir}, {lon_deg}°{lon_min}'{lon_sec:.2f}\"{lon_dir}"

    def load_kml_file(self):
        """Load polygon from KML file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Load KML File", "", "KML Files (*.kml)")
        if filename:
            try:
                tree = ET.parse(filename)
                root = tree.getroot()
                
                coords_elem = root.find('.//{http://www.opengis.net/kml/2.2}coordinates')
                if coords_elem is not None:
                    coords_text = coords_elem.text.strip()
                    coordinates = []
                    
                    for coord_pair in coords_text.split():
                        lon, lat, _ = map(float, coord_pair.split(','))
                        coordinates.append([lat, lon])
                    
                    if len(coordinates) >= 3:
                        self.polygon_coordinates = coordinates
                        self.polygon = Polygon(coordinates)
                        
                        area_km2 = self.polygon.area * 111 * 111
                        coord_display = "\n".join([f"Point {i+1}: {lat:.6f}, {lng:.6f}" for i, (lat, lng) in enumerate(coordinates)])
            
                        self.generate_btn.setEnabled(True)
                    else:
                        QMessageBox.warning(self, "Invalid KML", "KML file must contain at least 3 polygon points.")
                else:
                    QMessageBox.warning(self, "Invalid KML", "No polygon coordinates found in KML file.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading KML file: {str(e)}")

    def generate_scan(self):
        """Generate the structure scan mission."""
        if not self.polygon:
            QMessageBox.warning(self, "No Area", "Please define a scan area first.")
            return

        if not self.takeoff_location:
            QMessageBox.warning(self, "No Takeoff Location", "Please set a takeoff location first.")
            return

        if self.same_location_checkbox.currentText() == "Different Locations" and not self.landing_location:
            QMessageBox.warning(self, "No Landing Location", "Please set a landing location first.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            # Get takeoff and landing locations
            takeoff_lat = self.takeoff_location["lat"]
            takeoff_lng = self.takeoff_location["lng"]
            
            if self.same_location_checkbox.currentText() == "Same Location":
                landing_lat = takeoff_lat
                landing_lng = takeoff_lng
            else:
                landing_lat = self.landing_location["lat"]
                landing_lng = self.landing_location["lng"]
            
            # Get settings
            scan_altitude = self.scan_altitude_input.value()
            structure_height = self.structure_height_input.value()
            vertical_layers = self.vertical_layers_input.value()
            scan_distance = self.scan_distance_input.value()
            entrance_altitude = self.entrance_altitude_input.value()
            scan_bottom_alt = self.scan_bottom_alt_input.value()
            start_from_top = self.start_from_combo.currentText() == "Top"
            
            # Generate waypoints for QGroundControl structure scan
            waypoints = []
            
            # Add takeoff command (command 530 - Vehicle Mode)
            waypoints.append({
                "autoContinue": True,
                "command": 530,
                "doJumpId": 1,
                "frame": 2,
                "params": [0, 2, None, None, None, None, None],
                "type": "SimpleItem"
            })
            
            # Add takeoff waypoint at selected takeoff location
            waypoints.append({
                "AMSLAltAboveTerrain": None,
                "Altitude": entrance_altitude,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 22,
                "doJumpId": 2,
                "frame": 3,
                "params": [0, 0, 0, None, takeoff_lat, takeoff_lng, entrance_altitude],
                "type": "SimpleItem"
            })
            
            # Add structure scan complex item with proper QGroundControl format
            structure_scan_item = {
                "CameraCalc": {
                    "AdjustedFootprintFrontal": 25,
                    "AdjustedFootprintSide": 25,
                    "CameraName": "Manual (no camera specs)",
                    "DistanceMode": 3,
                    "DistanceToSurface": scan_distance,
                    "FixedOrientation": False,
                    "FocalLength": 5.2,
                    "FrontalOverlap": 80,
                    "ImageDensity": 0.5,
                    "ImageHeight": 3000,
                    "ImageWidth": 4000,
                    "Landscape": True,
                    "MinTriggerInterval": 0,
                    "SensorHeight": 5.7,
                    "SensorWidth": 7.6,
                    "SideOverlap": 80,
                    "ValueSetIsDistance": True,
                    "version": 2
                },
                "EntranceAltitude": entrance_altitude,
                "GimbalPitch": 0,
                "Layers": vertical_layers,
                "ScanBottomAlt": scan_bottom_alt,
                "StartFromTop": start_from_top,
                "StructureHeight": structure_height,
                "complexItemType": "StructureScan",
                "polygon": self.polygon_coordinates,
                "type": "ComplexItem",
                "version": 3
            }
            
            waypoints.append(structure_scan_item)
            
            # Add RTL command (Command 20 - Return to Launch)
            waypoints.append({
                "autoContinue": True,
                "command": 20,
                "doJumpId": len(waypoints) + 1,
                "frame": 2,
                "params": [0, 0, 0, 0, 0, 0, 0],
                "type": "SimpleItem"
            })
            
            self.waypoints = waypoints
            self.progress_bar.setValue(100)
            self.export_btn.setEnabled(True)
            
            # Check for terrain proximity warnings
            altitude_meters = scan_altitude * 0.3048  # Convert feet to meters
            proximity_warnings = self.check_terrain_proximity(altitude_meters)
            
            if proximity_warnings:
                self.show_terrain_proximity_warning(proximity_warnings)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating scan: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def export_flight_plan(self):
        """Export the flight plan to a .plan file."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for export.")
            return
        
        try:
            # Create geofence polygon
            geo_fence_polygon = [{
                "polygon": self.polygon_coordinates,
                "inclusion": True,
                "version": 1
            }]
            
            # Get aircraft-specific parameters using new system
            aircraft_info = self.get_aircraft_info_for_export()

            # Create flight plan
            flight_plan = {
                "fileType": "Plan",
                "version": 1,
                "groundStation": "QGroundControl",
                "mission": {
                    "items": self.waypoints,
                    "plannedHomePosition": [
                        self.takeoff_location["lat"],
                        self.takeoff_location["lng"],
                        self.terrain_query.get_elevation(self.takeoff_location["lat"], self.takeoff_location["lng"]) + (self.scan_altitude_input.value() * 0.3048)
                    ],
                    "cruiseSpeed": aircraft_info["cruiseSpeed"],
                    "hoverSpeed": aircraft_info["hoverSpeed"],
                    "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                    "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                    "globalPlanAltitudeMode": 0,
                    "version": 2,
                    "aircraftParameters": aircraft_info["aircraftParameters"]
                },
                "geoFence": {
                    "circles": [],
                    "polygons": geo_fence_polygon,
                    "version": 2
                },
                "rallyPoints": {
                    "points": [],
                    "version": 2
                }
            }

            # Save file using new file generation system
            saved_file = self.save_mission_file(flight_plan, "structure_scan")
            if saved_file:
                self.status_text.setText(f"Flight plan saved to:\n{saved_file}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving flight plan: {str(e)}")

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not hasattr(self, 'waypoints') or not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters
        altitude_meters = self.scan_altitude_input.value() * 0.3048  # Convert feet to meters
        
        # Extract waypoint data from the waypoints list
        waypoint_coords = []
        for waypoint in self.waypoints:
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
        plt.title('Structure Scan Altitude Profile with Terrain')
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
        
        stats_text = f"""Structure Scan Altitude Profile Summary
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

    def check_terrain_proximity(self, altitude_meters):
        """Check if any waypoint gets too close to terrain (within 50ft/15.24m)"""
        proximity_warnings = []
        warning_threshold = 15.24  # 50 feet in meters
        
        for i, waypoint in enumerate(self.waypoints):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat = waypoint['params'][4]
                lon = waypoint['params'][5]
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

    # Aircraft Configuration Methods

    def apply_qgc_theme(self):
        """Apply QGroundControl-inspired dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
                color: white;
            }
            QWidget {
                background-color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                color: white;
                background-color: #1E1E1E;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: white;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
                border-color: #666666;
            }
            QPushButton:pressed {
                background-color: #3A3A3A;
            }
            QPushButton:disabled {
                background-color: #2C2C2C;
                color: #888888;
                border-color: #444444;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #FFD700;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                selection-background-color: #007bff;
            }
            QLabel {
                color: white;
                background-color: transparent;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #FFD700;
                border-radius: 3px;
            }
            QScrollArea {
                background-color: #000000;
                border: none;
            }
            QFrame {
                background-color: #1E1E1E;
                border: 1px solid #555555;
            }
        """)

def main():
    app = QApplication(sys.argv)
    window = StructureScan()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
