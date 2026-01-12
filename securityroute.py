#!/usr/bin/env python3
"""
Enhanced Security Route Generator
Features:
- Interactive polygon drawing on map
- Fixed perimeter route generation
- Random route generation within polygon
- Terrain-aware altitude planning
- Multiple aircraft type support
"""

import sys
import json
import requests
import time
import math
import random
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





class SecurityRouteMapBridge(QObject):
    """Bridge class for QWebChannel communication."""
    
    @pyqtSlot(list)
    def receive_polygon(self, coordinates):
        """Receive polygon coordinates from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_polygon_received(coordinates)
    
    @pyqtSlot(float, float)
    def setStartLocation(self, lat, lng):
        """Set start location from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def setEndLocation(self, lat, lng):
        """Set end location from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_map_click(self, lat, lng):
        """Receive map click from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def set_takeoff_location(self, lat, lng):
        """Set takeoff/landing location from JavaScript."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_takeoff_setting(lat, lng)
    
    @pyqtSlot()
    def start_drawing_mode(self):
        """Start drawing mode from Python."""
        pass  # This will be called from Python to trigger JavaScript
    
    @pyqtSlot()
    def clear_drawing_mode(self):
        """Clear drawing mode from Python."""
        pass  # This will be called from Python to trigger JavaScript





class SecurityRoute(MissionToolBase):
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("security_route")
        self.mission_generator = get_optimized_mission_generator("security_route")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("security_route")
        
        self.polygon_coordinates = []
        self.polygon = None
        self.takeoff_point = None
        self.waypoints = []
        self.setting_takeoff = False  # Flag to track if we're setting takeoff location
        self.init_ui()
        self.apply_delivery_theme()

    def init_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Security Route Generator")
        self.resize(1400, 800)

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

        # Set splitter proportions (30% controls, 70% map)
        splitter.setSizes([400, 1000])

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
        title = QLabel("Security Route Generator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        
        # Vehicle type selection (fallback)
        vehicle_type_layout = QHBoxLayout()
        vehicle_type_layout.addWidget(QLabel("Vehicle Type:"))
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems(["Multicopter", "Fixed-Wing", "VTOL"])
        self.vehicle_type_combo.setCurrentText("Multicopter")
        vehicle_type_layout.addWidget(self.vehicle_type_combo)
        layout.addLayout(vehicle_type_layout)

        # Route type selection
        route_type_layout = QHBoxLayout()
        route_type_layout.addWidget(QLabel("Route Type:"))
        self.route_type_combo = QComboBox()
        self.route_type_combo.addItems(["Perimeter Route", "Random Route", "Grid Pattern"])
        self.route_type_combo.setCurrentText("Perimeter Route")
        self.route_type_combo.currentTextChanged.connect(self.on_route_type_changed)
        route_type_layout.addWidget(self.route_type_combo)
        layout.addLayout(route_type_layout)

        # Altitude input
        altitude_layout = QHBoxLayout()
        altitude_layout.addWidget(QLabel("Altitude (ft):"))
        self.altitude_input = QDoubleSpinBox()
        self.altitude_input.setRange(10, 1000)
        self.altitude_input.setValue(100)
        self.altitude_input.setSuffix(" ft")
        altitude_layout.addWidget(self.altitude_input)
        layout.addLayout(altitude_layout)

        # Waypoints input (for random route)
        waypoints_layout = QHBoxLayout()
        waypoints_layout.addWidget(QLabel("Waypoints:"))
        self.waypoints_input = QSpinBox()
        self.waypoints_input.setRange(5, 50)
        self.waypoints_input.setValue(15)
        waypoints_layout.addWidget(self.waypoints_input)
        layout.addLayout(waypoints_layout)

        # Takeoff/Landing Location Group
        takeoff_group = QGroupBox("Takeoff/Landing Location")
        takeoff_layout = QVBoxLayout(takeoff_group)

        # Instructions
        takeoff_instructions = QLabel(
            "Click 'Set Takeoff/Landing' then click on the map to set the location.\n"
            "This will be used for both takeoff and landing."
        )
        takeoff_instructions.setWordWrap(True)
        takeoff_layout.addWidget(takeoff_instructions)

        # Takeoff/Landing button
        self.set_takeoff_btn = QPushButton("Set Takeoff/Landing Location")
        self.set_takeoff_btn.clicked.connect(self.start_takeoff_setting)
        takeoff_layout.addWidget(self.set_takeoff_btn)

        # Takeoff/Landing display
        self.takeoff_location_label = QLabel("No takeoff/landing location set")
        self.takeoff_location_label.setWordWrap(True)
        takeoff_layout.addWidget(self.takeoff_location_label)

        layout.addWidget(takeoff_group)

        # Polygon Drawing Group
        polygon_group = QGroupBox("Area Definition")
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
        self.generate_btn = QPushButton("Generate Security Route")
        self.generate_btn.clicked.connect(self.generate_route)
        self.generate_btn.setEnabled(False)
        mission_layout.addWidget(self.generate_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        mission_layout.addWidget(self.progress_bar)

        # Export button
        self.export_btn = QPushButton("Re-export Flight Plan")
        self.export_btn.clicked.connect(self.export_flight_plan)
        self.export_btn.setEnabled(False)
        mission_layout.addWidget(self.export_btn)
        
        # Terrain visualization button
        self.visualize_btn = QPushButton("Visualize Terrain Profile")
        self.visualize_btn.clicked.connect(self.show_terrain_visualization)
        self.visualize_btn.setEnabled(False)
        mission_layout.addWidget(self.visualize_btn)

        layout.addWidget(mission_group)

        # Status display
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)

        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        self.status_text.setText("Ready to define security area...")
        status_layout.addWidget(self.status_text)

        layout.addWidget(status_group)

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
        self.map_bridge = SecurityRouteMapBridge()
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
            <title>Security Route Map</title>
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
                    background: #3C3C3C;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    z-index: 1000;
                    max-width: 300px;
                    border: 1px solid #555555;
                }
                .drawing-controls {
                    position: absolute !important;
                    bottom: 10px !important;
                    right: 10px !important;
                    background: #3C3C3C !important;
                    color: white !important;
                    padding: 15px !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
                    z-index: 1000 !important;
                    display: block !important;
                    visibility: visible !important;
                    opacity: 1 !important;
                    min-width: 150px !important;
                    border: 1px solid #555555 !important;
                }
                /* Coordinate popup styles (dark theme) */
                .coordinate-popup { font-family: Arial, sans-serif; font-size: 12px; line-height: 1.4; color: white; }
                .coordinate-popup .label { font-weight: bold; color: #FFD700; }
                .coordinate-popup .value { color: white; font-family: 'Courier New', monospace; }
                .elevation-info { margin-top: 8px; padding-top: 8px; border-top: 1px solid #555555; }
                
                .drawing-controls h4 {
                    margin: 0 0 10px 0 !important;
                    color: white !important;
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
                    background: #FFD700 !important;
                    color: #1E1E1E !important;
                }
                
                .drawing-controls button#finish-drawing {
                    background: #4CAF50 !important;
                    color: white !important;
                }
                
                .drawing-controls button#clear-polygon {
                    background: #f44336 !important;
                    color: white !important;
                }
                .drawing-controls button:hover {
                    background: #4C4C4C !important;
                    color: white !important;
                }
                .drawing-controls button.active {
                    background: #FFD700 !important;
                    color: #1E1E1E !important;
                }
                
                .drawing-controls button:disabled {
                    background: #2C2C2C !important;
                    color: #888888 !important;
                    cursor: not-allowed;
                }
                
                .point-marker {
                    background-color: red;
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    border: 2px solid white;
                }
                
                /* Address Search Styles */
                .search-container {
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    z-index: 1000;
                    background: #3C3C3C;
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    min-width: 300px;
                    border: 1px solid #555555;
                }
                
                .search-container h4 {
                    margin: 0 0 10px 0;
                    color: white;
                    font-size: 14px;
                }
                
                .search-input {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    font-size: 14px;
                    box-sizing: border-box;
                    background: #2C2C2C;
                    color: white;
                }
                
                .search-button {
                    margin-top: 5px;
                    padding: 8px 12px;
                    background: #FFD700;
                    color: #1E1E1E;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 14px;
                }
                
                .search-button:hover {
                    background: #4C4C4C;
                    color: white;
                }
                
                .search-results {
                    margin-top: 10px;
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #555555;
                    border-radius: 3px;
                    background: #2C2C2C;
                }
                
                .search-result-item {
                    padding: 8px;
                    border-bottom: 1px solid #555555;
                    cursor: pointer;
                    font-size: 12px;
                    color: white;
                }
                
                .search-result-item:hover {
                    background: #4C4C4C;
                }
                
                .search-result-item:last-child {
                    border-bottom: none;
                }
                
                .search-result-title {
                    font-weight: bold;
                    color: #FFD700;
                }
                
                .search-result-address {
                    color: white;
                    font-size: 11px;
                }
                
                .search-result-item.selected {
                    background: #FFD700;
                    color: #1E1E1E;
                }
                
                .search-result-item.selected .search-result-title,
                .search-result-item.selected .search-result-address {
                    color: #1E1E1E;
                }
                

                

            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <div class="info-panel">
                <h4>Security Area Drawing</h4>
                <p><strong>Status:</strong> <span id="drawing-status">Ready</span></p>
                <p><strong>Points:</strong> <span id="point-count">0</span></p>
                <p><strong>Area:</strong> <span id="area-size">0</span> km²</p>
            </div>
            
            <!-- Address Search Container -->
            <div class="search-container">
                <h4>Search Address</h4>
                <input type="text" id="search-input" class="search-input" placeholder="Enter address, city, or landmark...">
                <button id="search-button" class="search-button">Search</button>
                <div id="search-results" class="search-results" style="display: none;"></div>
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

                // Elevation and popup helpers (same as map.html)
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
                
                // Drawing variables
                let drawing = false;
                let polygonPoints = [];
                let polygonLayer = null;
                let pointMarkers = [];
                
                // Address Search Functionality
                const searchInput = document.getElementById('search-input');
                const searchButton = document.getElementById('search-button');
                const searchResults = document.getElementById('search-results');
                let searchMarker = null;
                let searchTimeout = null;
                let currentSearchResults = [];
                
                // Function to search for addresses using Nominatim
                async function searchAddress(query) {
                    try {
                        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5`);
                        const data = await response.json();
                        return data;
                    } catch (error) {
                        console.error('Error searching for address:', error);
                        return [];
                    }
                }
                
                // Function to display search results
                function displaySearchResults(results) {
                    searchResults.innerHTML = '';
                    currentSearchResults = results;
                    
                    if (results.length === 0) {
                        searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
                        searchResults.style.display = 'block';
                        return;
                    }
                    
                    results.forEach((result, index) => {
                        const resultItem = document.createElement('div');
                        resultItem.className = 'search-result-item';
                        resultItem.innerHTML = `
                            <div class="search-result-title">${result.display_name.split(',')[0]}</div>
                            <div class="search-result-address">${result.display_name}</div>
                        `;
                        
                        resultItem.addEventListener('click', () => {
                            selectSearchResult(result);
                        });
                        
                        resultItem.addEventListener('mouseenter', () => {
                            // Preview the location on map
                            previewLocation(result);
                        });
                        
                        resultItem.addEventListener('mouseleave', () => {
                            // Remove preview marker
                            if (searchMarker && searchMarker._preview) {
                                map.removeLayer(searchMarker);
                                searchMarker = null;
                            }
                        });
                        
                        searchResults.appendChild(resultItem);
                    });
                    
                    searchResults.style.display = 'block';
                }
                
                // Function to preview location on map
                function previewLocation(result) {
                    const lat = parseFloat(result.lat);
                    const lon = parseFloat(result.lon);
                    
                    // Remove previous preview marker
                    if (searchMarker && searchMarker._preview) {
                        map.removeLayer(searchMarker);
                    }
                    
                    // Add preview marker
                    searchMarker = L.marker([lat, lon], {
                        icon: L.divIcon({
                            className: 'preview-marker',
                            html: '<div style="background-color: #007bff; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
                            iconSize: [12, 12],
                            iconAnchor: [6, 6]
                        })
                    }).addTo(map);
                    searchMarker._preview = true;
                    
                    // Center map on preview location
                    map.setView([lat, lon], 16);
                }
                
                // Function to select a search result
                function selectSearchResult(result) {
                    const lat = parseFloat(result.lat);
                    const lon = parseFloat(result.lon);
                    
                    // Remove previous search marker
                    if (searchMarker) {
                        map.removeLayer(searchMarker);
                    }
                    
                    // Add new marker at searched location
                    searchMarker = L.marker([lat, lon])
                        .addTo(map)
                        .bindPopup(`<b>Searched Location:</b><br>${result.display_name}`)
                        .openPopup();
                    
                    // Center map on the searched location
                    map.setView([lat, lon], 16);
                    
                    // Hide search results
                    searchResults.style.display = 'none';
                    
                    // Update search input with selected result
                    searchInput.value = result.display_name;
                }
                
                // Real-time search as user types (autocomplete)
                searchInput.addEventListener('input', (event) => {
                    const query = event.target.value.trim();
                    
                    // Clear previous timeout
                    if (searchTimeout) {
                        clearTimeout(searchTimeout);
                    }
                    
                    // Hide results if input is empty
                    if (query.length === 0) {
                        searchResults.style.display = 'none';
                        if (searchMarker && searchMarker._preview) {
                            map.removeLayer(searchMarker);
                            searchMarker = null;
                        }
                        return;
                    }
                    
                    // Only search if query is at least 3 characters
                    if (query.length < 3) {
                        searchResults.style.display = 'none';
                        return;
                    }
                    
                    // Set timeout to avoid too many API calls
                    searchTimeout = setTimeout(async () => {
                        searchButton.textContent = 'Searching...';
                        searchButton.disabled = true;
                        
                        const results = await searchAddress(query);
                        displaySearchResults(results);
                        
                        searchButton.textContent = 'Search';
                        searchButton.disabled = false;
                    }, 300); // 300ms delay
                });
                
                // Search button click handler
                searchButton.addEventListener('click', async () => {
                    const query = searchInput.value.trim();
                    if (query) {
                        searchButton.textContent = 'Searching...';
                        searchButton.disabled = true;
                        
                        const results = await searchAddress(query);
                        displaySearchResults(results);
                        
                        searchButton.textContent = 'Search';
                        searchButton.disabled = false;
                    }
                });
                
                // Enter key handler for search input
                searchInput.addEventListener('keypress', async (event) => {
                    if (event.key === 'Enter') {
                        const query = searchInput.value.trim();
                        if (query) {
                            searchButton.textContent = 'Searching...';
                            searchButton.disabled = true;
                            
                            const results = await searchAddress(query);
                            displaySearchResults(results);
                            
                            searchButton.textContent = 'Search';
                            searchButton.disabled = false;
                        }
                    }
                });
                
                // Arrow key navigation for search results
                searchInput.addEventListener('keydown', (event) => {
                    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                        event.preventDefault();
                        
                        const resultItems = searchResults.querySelectorAll('.search-result-item');
                        if (resultItems.length === 0) return;
                        
                        let currentIndex = -1;
                        for (let i = 0; i < resultItems.length; i++) {
                            if (resultItems[i].classList.contains('selected')) {
                                currentIndex = i;
                                break;
                            }
                        }
                        
                        if (event.key === 'ArrowDown') {
                            currentIndex = (currentIndex + 1) % resultItems.length;
                        } else {
                            currentIndex = currentIndex <= 0 ? resultItems.length - 1 : currentIndex - 1;
                        }
                        
                        // Remove previous selection
                        resultItems.forEach(item => item.classList.remove('selected'));
                        
                        // Add selection to current item
                        resultItems[currentIndex].classList.add('selected');
                        
                        // Preview the selected location
                        if (currentSearchResults[currentIndex]) {
                            previewLocation(currentSearchResults[currentIndex]);
                        }
                    } else if (event.key === 'Enter' && searchResults.style.display === 'block') {
                        event.preventDefault();
                        
                        const selectedItem = searchResults.querySelector('.search-result-item.selected');
                        if (selectedItem) {
                            const index = Array.from(searchResults.querySelectorAll('.search-result-item')).indexOf(selectedItem);
                            if (currentSearchResults[index]) {
                                selectSearchResult(currentSearchResults[index]);
                            }
                        }
                    }
                });
                
                // Click outside search results to hide them
                document.addEventListener('click', (event) => {
                    if (!event.target.closest('.search-container')) {
                        searchResults.style.display = 'none';
                    }
                });
                
                // Drawing controls - ensure DOM is ready
                document.addEventListener('DOMContentLoaded', function() {
                    const startDrawingBtn = document.getElementById('start-drawing');
                    const finishDrawingBtn = document.getElementById('finish-drawing');
                    const clearPolygonBtn = document.getElementById('clear-polygon');
                    
                    if (startDrawingBtn) {
                        startDrawingBtn.addEventListener('click', function() {
                            startDrawing();
                        });
                    }
                    
                    if (finishDrawingBtn) {
                        finishDrawingBtn.addEventListener('click', function() {
                            finishPolygon();
                        });
                    }
                    
                    if (clearPolygonBtn) {
                        clearPolygonBtn.addEventListener('click', function() {
                            clearPolygon();
                        });
                    }
                });
                
                // Also try immediate attachment as fallback
                setTimeout(function() {
                    const startDrawingBtn = document.getElementById('start-drawing');
                    const finishDrawingBtn = document.getElementById('finish-drawing');
                    const clearPolygonBtn = document.getElementById('clear-polygon');
                    
                    if (startDrawingBtn && !startDrawingBtn.hasAttribute('data-listener-attached')) {
                        startDrawingBtn.setAttribute('data-listener-attached', 'true');
                        startDrawingBtn.addEventListener('click', function() {
                            startDrawing();
                        });
                    }
                    
                    if (finishDrawingBtn && !finishDrawingBtn.hasAttribute('data-listener-attached')) {
                        finishDrawingBtn.setAttribute('data-listener-attached', 'true');
                        finishDrawingBtn.addEventListener('click', function() {
                            finishPolygon();
                        });
                    }
                    
                    if (clearPolygonBtn && !clearPolygonBtn.hasAttribute('data-listener-attached')) {
                        clearPolygonBtn.setAttribute('data-listener-attached', 'true');
                        clearPolygonBtn.addEventListener('click', function() {
                            clearPolygon();
                        });
                    }
                }, 100);
                
                function startDrawing() {
                    drawing = true;
                    polygonPoints = [];
                    clearMarkers();
                    updateStatus('Drawing - Click to add points');
                    document.getElementById('start-drawing').disabled = true;
                    document.getElementById('finish-drawing').disabled = false;
                    document.getElementById('start-drawing').classList.add('active');
                    
                    // Change cursor to indicate drawing mode
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function finishPolygon() {
                    if (polygonPoints.length < 3) {
                        alert('Need at least 3 points to create a polygon');
                        return;
                    }
                    
                    drawing = false;
                    updateStatus('Polygon complete');
                    document.getElementById('start-drawing').disabled = false;
                    document.getElementById('finish-drawing').disabled = true;
                    document.getElementById('start-drawing').classList.remove('active');
                    
                    // Reset cursor
                    map.getContainer().style.cursor = '';
                    
                    // Create polygon
                    if (polygonLayer) {
                        map.removeLayer(polygonLayer);
                    }
                    
                    polygonLayer = L.polygon(polygonPoints, {
                        color: 'red',
                        weight: 2,
                        fillColor: '#f03',
                        fillOpacity: 0.2
                    }).addTo(map);
                    
                    // Calculate area
                    let area = L.GeometryUtil.geodesicArea(polygonPoints);
                    let areaKm2 = (area / 1000000).toFixed(2);
                    document.getElementById('area-size').textContent = areaKm2;
                    
                    // Send coordinates to Python
                    if (pywebchannel) {
                        pywebchannel.receive_polygon(polygonPoints);
                    }
                }
                
                function clearPolygon() {
                    drawing = false;
                    polygonPoints = [];
                    clearMarkers();
                    updateStatus('Ready');
                    document.getElementById('start-drawing').disabled = false;
                    document.getElementById('finish-drawing').disabled = true;
                    document.getElementById('start-drawing').classList.remove('active');
                    
                    // Reset cursor
                    map.getContainer().style.cursor = '';
                    
                    if (polygonLayer) {
                        map.removeLayer(polygonLayer);
                        polygonLayer = null;
                    }
                    
                    document.getElementById('point-count').textContent = '0';
                    document.getElementById('area-size').textContent = '0';
                }
                
                function clearMarkers() {
                    pointMarkers.forEach(marker => map.removeLayer(marker));
                    pointMarkers = [];
                }
                
                function updateStatus(status) {
                    document.getElementById('drawing-status').textContent = status;
                }
                
                // Map click handler
                map.on('click', async function(e) {
                    let lat = e.latlng.lat;
                    let lng = e.latlng.lng;
                    
                    if (drawing) {
                        polygonPoints.push([lat, lng]);
                        
                        // Add marker
                        let marker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'point-marker',
                                html: '<div style="background-color: red; width: 8px; height: 8px; border-radius: 50%; border: 2px solid white;"></div>',
                                iconSize: [12, 12]
                            })
                        }).addTo(map);
                        pointMarkers.push(marker);
                        
                        document.getElementById('point-count').textContent = polygonPoints.length;
                        
                        // Draw line between points
                        if (polygonPoints.length > 1) {
                            let line = L.polyline(polygonPoints.slice(-2), {
                                color: 'red',
                                weight: 2,
                                dashArray: '5, 5'
                            }).addTo(map);
                            setTimeout(() => map.removeLayer(line), 2000);
                        }
                    } else {
                        // Always call Python method - it will handle takeoff setting or show popup
                        if (pywebchannel && pywebchannel.receive_map_click) {
                            pywebchannel.receive_map_click(lat, lng);
                        } else {
                            // Fallback: Show coordinate/elevation popup when not drawing (same UX as map.html)
                            const popup = L.popup()
                                .setLatLng([lat, lng])
                                .setContent(createPopupContent(lat, lng, null))
                                .openOn(map);
                            // Fetch elevation and update popup
                            const elevation = await getElevation(lat, lng);
                            if (elevation !== null) {
                                popup.setContent(createPopupContent(lat, lng, elevation));
                            }
                        }
                    }
                });
                
                // Double-click to finish polygon
                map.on('dblclick', function(e) {
                    if (drawing && polygonPoints.length >= 3) {
                        finishPolygon();
                    }
                });
                
                // Initialize status
                updateStatus('Ready');
                
                // Debug: Check if drawing controls exist
                console.log('Drawing controls check:');
                console.log('start-drawing:', document.getElementById('start-drawing'));
                console.log('finish-drawing:', document.getElementById('finish-drawing'));
                console.log('clear-polygon:', document.getElementById('clear-polygon'));
                console.log('drawing-controls div:', document.querySelector('.drawing-controls'));
            </script>
        </body>
        </html>
        """

    def on_route_type_changed(self, route_type):
        """Handle route type changes."""
        if route_type == "Random Route":
            self.waypoints_input.setEnabled(True)
        else:
            self.waypoints_input.setEnabled(False)

    def start_polygon_drawing(self):
        """Start polygon drawing mode."""
        self.status_text.setText("Drawing mode activated. Click on the map to add polygon points.")
        # Trigger JavaScript drawing mode
        self.web_view.page().runJavaScript("startDrawing();")

    def clear_polygon(self):
        """Clear the current polygon."""
        self.polygon_coordinates = []
        self.polygon = None
        self.status_text.setText("Polygon cleared. Ready to draw new area.")
        self.generate_btn.setEnabled(False)
        # Trigger JavaScript clear function
        self.web_view.page().runJavaScript("clearPolygon();")

    def handle_polygon_received(self, coordinates):
        """Handle polygon coordinates received from JavaScript via bridge."""
        print(f"Polygon received with {len(coordinates)} coordinates")
        self.polygon_coordinates = coordinates
        if len(coordinates) >= 3:
            # Create Shapely polygon
            self.polygon = Polygon(coordinates)
            area_km2 = self.polygon.area * 111 * 111
            
            # Format coordinates for display
            coord_display = "\n".join([f"Point {i+1}: {lat:.6f}, {lng:.6f}" for i, (lat, lng) in enumerate(coordinates)])
            
            self.status_text.setText(f"Security area defined with {len(coordinates)} points.\nArea: {area_km2:.2f} km²\n\nCoordinates:\n{coord_display}")
            self.generate_btn.setEnabled(True)
        else:
            self.status_text.setText("Invalid polygon. Need at least 3 points.")
    
    def start_takeoff_setting(self):
        """Start the takeoff location setting mode."""
        self.setting_takeoff = True
        self.set_takeoff_btn.setText("Click on map to set location...")
        self.set_takeoff_btn.setEnabled(False)
        self.status_text.setText("Click on the map to set the takeoff/landing location.")
    
    def handle_takeoff_setting(self, lat, lng):
        """Handle takeoff location setting from map click."""
        if self.setting_takeoff:
            self.takeoff_point = (lat, lng)
            
            # Get terrain elevation
            terrain_elevation = self.terrain_query.get_elevation(lat, lng)
            elevation_feet = terrain_elevation * 3.28084
            
            # Format coordinates
            decimal_coords = f"{lat:.6f}, {lng:.6f}"
            dms_coords = self.format_dms(lat, lng)
            
            # Update display
            self.takeoff_location_label.setText(
                f"Takeoff/Landing Location Set:\n"
                f"Decimal: {decimal_coords}\n"
                f"DMS: {dms_coords}\n"
                f"Elevation: {terrain_elevation:.1f}m ({elevation_feet:.1f}ft)"
            )
            
            # Reset button
            self.set_takeoff_btn.setText("Set Takeoff/Landing Location")
            self.set_takeoff_btn.setEnabled(True)
            self.setting_takeoff = False
            
            self.status_text.setText("Takeoff/landing location set successfully!")
    
    def handle_map_click(self, lat, lng):
        """Handle map click events with enhanced coordinate and elevation display."""
        # If we're setting takeoff location, handle that instead
        if self.setting_takeoff:
            self.handle_takeoff_setting(lat, lng)
            return

        # The standardized popup is now handled by the JavaScript in the embedded HTML
        # This method is called by the JavaScript but doesn't need to show a dialog
        # The popup is displayed directly on the map by the JavaScript code
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
                
                # Find polygon coordinates
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
                        
                        # Calculate area
                        area_km2 = self.polygon.area * 111 * 111
                        
                        # Format coordinates for display
                        coord_display = "\n".join([f"Point {i+1}: {lat:.6f}, {lng:.6f}" for i, (lat, lng) in enumerate(coordinates)])
                        
                        self.status_text.setText(f"KML loaded with {len(coordinates)} points.\nArea: {area_km2:.2f} km²\n\nCoordinates:\n{coord_display}")
                        self.generate_btn.setEnabled(True)
                        
                        # Update map to show the loaded polygon
                        self.update_map_polygon(coordinates)
                    else:
                        QMessageBox.warning(self, "Invalid KML", "KML file must contain at least 3 polygon points.")
                else:
                    QMessageBox.warning(self, "Invalid KML", "No polygon coordinates found in KML file.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading KML file: {str(e)}")

    def update_map_polygon(self, coordinates):
        """Update the map to show the loaded polygon."""
        # This would require JavaScript communication to update the map
        # For now, we'll just store the coordinates
        pass

    def generate_route(self):
        """Generate the security route based on selected options."""
        if not self.polygon:
            QMessageBox.warning(self, "No Area", "Please define a security area first.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        try:
            route_type = self.route_type_combo.currentText()
            altitude = self.altitude_input.value()
            vehicle_type = self.vehicle_type_combo.currentText()
            
            # Check if takeoff point is set
            if not self.takeoff_point:
                QMessageBox.warning(self, "No Takeoff Point", "Please set a takeoff/landing location first.")
                return

            # Generate waypoints
            waypoints = []

            # Add takeoff command
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude, 22, 1
            ))
            
            if route_type == "Perimeter Route":
                self.generate_perimeter_waypoints(waypoints, altitude)
            elif route_type == "Random Route":
                num_waypoints = self.waypoints_input.value()
                self.generate_random_waypoints(waypoints, altitude, num_waypoints)
            elif route_type == "Grid Pattern":
                self.generate_grid_waypoints(waypoints, altitude)
            
            # Add landing command
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude, 21, len(waypoints) + 1
            ))
            
            self.waypoints = waypoints
            self.progress_bar.setValue(100)

            # Check for terrain collisions
            collision_points = self.check_terrain_collisions(waypoints, altitude)
            
            # Get terrain elevation at takeoff point for status display
            takeoff_terrain = self.terrain_query.get_elevation(self.takeoff_point[0], self.takeoff_point[1])
            flight_altitude_meters = altitude * 0.3048
            absolute_altitude = takeoff_terrain + flight_altitude_meters
            
            # Build status message
            status_msg = (
                f"Route generated with {len(waypoints)} waypoints.\n"
                f"Flight altitude: {altitude} ft ({flight_altitude_meters:.1f} m) above terrain\n"
                f"Takeoff terrain elevation: {takeoff_terrain:.1f} m\n"
                f"Absolute flight altitude: {absolute_altitude:.1f} m AMSL"
            )
            
            # Add collision warnings if any
            if collision_points:
                status_msg += f"\n\n⚠️ TERRAIN COLLISION WARNING ⚠️\n"
                status_msg += f"Flight path goes below terrain at {len(collision_points)} point(s):\n"
                for i, (lat, lon, terrain_alt, flight_alt) in enumerate(collision_points[:5]):  # Show first 5
                    status_msg += f"  Point {i+1}: Terrain {terrain_alt:.1f}m, Flight {flight_alt:.1f}m\n"
                if len(collision_points) > 5:
                    status_msg += f"  ... and {len(collision_points) - 5} more points\n"
                status_msg += f"\nConsider increasing flight altitude or adjusting route."
                
                # Show warning dialog
                QMessageBox.warning(self, "Terrain Collision Warning", 
                                  f"Flight path goes below terrain at {len(collision_points)} point(s)!\n\n"
                                  f"Consider increasing flight altitude or adjusting route.")
            
            self.status_text.setText(status_msg)
            self.export_btn.setEnabled(True)
            self.visualize_btn.setEnabled(True)

            # Enable toolbar actions
            self.toolbar.enable_actions(True)
            
            # Automatically prompt user to save the flight plan
            self.auto_save_flight_plan()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating route: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    def generate_perimeter_waypoints(self, waypoints, altitude):
        """Generate waypoints along the perimeter of the polygon with proper buffer inside geofence."""
        if not self.polygon:
            return

        # Calculate buffer distance (in degrees) - approximately 50 meters
        # This ensures the flight path stays well inside the geofence boundary
        buffer_distance = 0.0005  # Approximately 50 meters at mid-latitudes
        
        try:
            # Create a buffered polygon (smaller than the original)
            buffered_polygon = self.polygon.buffer(-buffer_distance)
            
            # If buffering fails or creates invalid geometry, use original with smaller buffer
            if not buffered_polygon.is_valid or buffered_polygon.is_empty:
                # Fallback: use original polygon with very small buffer
                buffered_polygon = self.polygon.buffer(-buffer_distance * 0.5)
                
            # Get perimeter coordinates from buffered polygon
            if hasattr(buffered_polygon, 'exterior'):
                perimeter_coords = list(buffered_polygon.exterior.coords)
            else:
                # If it's a MultiPolygon, use the largest one
                if hasattr(buffered_polygon, 'geoms'):
                    largest_polygon = max(buffered_polygon.geoms, key=lambda p: p.area)
                    perimeter_coords = list(largest_polygon.exterior.coords)
                else:
                    # Fallback to original polygon
                    perimeter_coords = list(self.polygon.exterior.coords)
            
            # Add waypoints along the buffered perimeter
            for i, (lat, lon) in enumerate(perimeter_coords):
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, ((i + 1) / len(perimeter_coords)) * 100)))
                QApplication.processEvents()
                
            self.status_text.setText(f"Perimeter route generated with {len(perimeter_coords)} waypoints (buffered inside geofence).")
            
        except Exception as e:
            # Fallback: use original polygon if buffering fails
            self.status_text.setText(f"Warning: Using original polygon perimeter due to buffering error: {str(e)}")
            perimeter_coords = list(self.polygon.exterior.coords)
            
            for i, (lat, lon) in enumerate(perimeter_coords):
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, ((i + 1) / len(perimeter_coords)) * 100)))
                QApplication.processEvents()

    def generate_random_waypoints(self, waypoints, altitude, num_waypoints):
        """Generate random waypoints within the buffered polygon."""
        if not self.polygon:
            return

        # Use the same buffered polygon as perimeter route for consistency
        buffer_distance = 0.0005  # Approximately 50 meters at mid-latitudes
        
        try:
            # Create a buffered polygon (smaller than the original)
            buffered_polygon = self.polygon.buffer(-buffer_distance)
            
            # If buffering fails or creates invalid geometry, use original with smaller buffer
            if not buffered_polygon.is_valid or buffered_polygon.is_empty:
                buffered_polygon = self.polygon.buffer(-buffer_distance * 0.5)
                
            # Generate random points within the buffered polygon
            for i in range(num_waypoints):
                lat, lon = self.generate_random_point_in_polygon(buffered_polygon)
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, (i + 1) * 100 // num_waypoints)))
                QApplication.processEvents()

            self.status_text.setText(f"Generated {num_waypoints} random waypoints within buffered area.")
            
        except Exception as e:
            # Fallback: use original polygon if buffering fails
            self.status_text.setText(f"Warning: Using original polygon for random waypoints due to buffering error: {str(e)}")
            for i in range(num_waypoints):
                lat, lon = self.generate_random_point_in_polygon()
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, (i + 1) * 100 // num_waypoints)))
                QApplication.processEvents()

    def generate_grid_waypoints(self, waypoints, altitude):
        """Generate grid pattern waypoints within the buffered polygon."""
        if not self.polygon:
            return
        
        # Use the same buffered polygon as other route types for consistency
        buffer_distance = 0.0005  # Approximately 50 meters at mid-latitudes
        
        try:
            # Create a buffered polygon (smaller than the original)
            buffered_polygon = self.polygon.buffer(-buffer_distance)
            
            # If buffering fails or creates invalid geometry, use original with smaller buffer
            if not buffered_polygon.is_valid or buffered_polygon.is_empty:
                buffered_polygon = self.polygon.buffer(-buffer_distance * 0.5)
                
            # Create a grid within the buffered polygon bounds
            minx, miny, maxx, maxy = buffered_polygon.bounds
            grid_spacing = 0.001  # Adjust based on polygon size
            
            grid_points = []
            x = minx
            while x <= maxx:
                y = miny
                while y <= maxy:
                    point = Point(x, y)
                    if buffered_polygon.contains(point):
                        grid_points.append((x, y))
                    y += grid_spacing
                x += grid_spacing
            
            # Add grid waypoints
            for i, (lat, lon) in enumerate(grid_points):
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, (i + 1) * 100 // len(grid_points))))
                QApplication.processEvents()
                
            self.status_text.setText(f"Generated {len(grid_points)} grid waypoints within buffered area.")
            
        except Exception as e:
            # Fallback: use original polygon if buffering fails
            self.status_text.setText(f"Warning: Using original polygon for grid waypoints due to buffering error: {str(e)}")
            minx, miny, maxx, maxy = self.polygon.bounds
            grid_spacing = 0.001
            
            grid_points = []
            x = minx
            while x <= maxx:
                y = miny
                while y <= maxy:
                    point = Point(x, y)
                    if self.polygon.contains(point):
                        grid_points.append((x, y))
                    y += grid_spacing
                x += grid_spacing
            
            for i, (lat, lon) in enumerate(grid_points):
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, len(waypoints) + 1))
                self.progress_bar.setValue(int(min(100, (i + 1) * 100 // len(grid_points))))
                QApplication.processEvents()

    def check_terrain_collisions(self, waypoints, flight_altitude_ft):
        """Check if flight path goes below terrain elevation."""
        collision_points = []
        flight_altitude_m = flight_altitude_ft * 0.3048
        
        for waypoint in waypoints:
            # Extract coordinates from waypoint
            lat = waypoint["params"][4]  # Latitude
            lon = waypoint["params"][5]  # Longitude
            
            # Get terrain elevation at this point
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            
            # Calculate flight altitude above sea level
            flight_altitude_amsl = terrain_elevation + flight_altitude_m
            
            # Check if flight altitude is below terrain (with small buffer)
            if flight_altitude_amsl < terrain_elevation + 5:  # 5m buffer
                collision_points.append((lat, lon, terrain_elevation, flight_altitude_amsl))
        
        return collision_points

    def show_terrain_visualization(self):
        """Show terrain elevation profile visualization."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return
        
        # Call the visualization method
        self.visualize_altitude_profile()

    def generate_random_point_in_polygon(self, polygon=None):
        """Generate a random point within the polygon."""
        if polygon is None:
            polygon = self.polygon
            
        minx, miny, maxx, maxy = polygon.bounds
        while True:
            random_lat = random.uniform(minx, maxx)
            random_lon = random.uniform(miny, maxy)
            if polygon.contains(Point(random_lat, random_lon)):
                return random_lat, random_lon

    def create_waypoint(self, lat, lon, altitude, command, index):
        """Create a waypoint dictionary with altitude above terrain."""
        # Get terrain elevation at this point
        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
        
        # Calculate altitude above sea level (terrain + flight altitude)
        altitude_feet = altitude  # This is the desired altitude above terrain
        altitude_meters = altitude_feet * 0.3048  # Convert to meters
        absolute_altitude_meters = terrain_elevation + altitude_meters  # Add to terrain elevation
        
        return {
            "AMSLAltAboveTerrain": altitude_meters,  # Altitude above terrain
            "Altitude": absolute_altitude_meters,  # Absolute altitude above sea level
            "AltitudeMode": 3,  # AMSL (Above Mean Sea Level)
            "autoContinue": True,
            "command": command,
            "doJumpId": index,
            "frame": 3,
            "params": [0, 0, 0, None, lat, lon, absolute_altitude_meters],
            "type": "SimpleItem"
        }

    def auto_save_flight_plan(self):
        """Automatically prompt user to save the flight plan after generation."""
        if not self.waypoints:
            return
        
        # Show a message box asking if user wants to save
        reply = QMessageBox.question(
            self, 
            "Save Flight Plan", 
            "Flight plan generated successfully!\n\nWould you like to save it to a file?\n\n(You will be able to choose the save location)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            self.export_flight_plan()

    def export_flight_plan(self):
        """Export the flight plan to a .plan file."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for export.")
            return
        
        try:
            vehicle_type = self.vehicle_type_combo.currentText()
            
            # Get aircraft-specific parameters using new system
            aircraft_info = self.get_aircraft_info_for_export()
            
            # Fallback to vehicle-specific parameters if no aircraft parameters
            if not self.is_parameters_enabled():
                if vehicle_type == "Multicopter":
                    aircraft_info["cruiseSpeed"] = 15
                    aircraft_info["hoverSpeed"] = 5
                    aircraft_info["vehicleType"] = "multicopter"
                elif vehicle_type == "Fixed-Wing":
                    aircraft_info["cruiseSpeed"] = 25
                    aircraft_info["hoverSpeed"] = 0
                    aircraft_info["vehicleType"] = "fixedwing"
                elif vehicle_type == "VTOL":
                    aircraft_info["cruiseSpeed"] = 20
                    aircraft_info["hoverSpeed"] = 5
                    aircraft_info["vehicleType"] = "vtol"

            # Create geofence polygon
            geo_fence_polygon = [{
                "polygon": self.polygon_coordinates,
                "inclusion": True,
                "version": 1
            }]
            
            # Create flight plan
            flight_plan = {
                "fileType": "Plan",
                "version": 1,
                "groundStation": "QGroundControl",
                "mission": {
                    "items": self.waypoints,
                    "plannedHomePosition": [
                        self.takeoff_point[0],
                        self.takeoff_point[1],
                        self.terrain_query.get_elevation(self.takeoff_point[0], self.takeoff_point[1]) + (self.altitude_input.value() * 0.3048)
                    ],
                    "cruiseSpeed": aircraft_info["cruiseSpeed"],
                    "hoverSpeed": aircraft_info["hoverSpeed"],
                    "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                    "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2 if aircraft_info["vehicleType"] == "multicopter" else 3,
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
            saved_file = self.save_mission_file(flight_plan, "security_route")
            if saved_file:
                self.status_text.setText(f"Flight plan saved to:\n{saved_file}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving flight plan: {str(e)}")

    # Aircraft Configuration Methods

    def apply_delivery_theme(self):
        """Apply delivery route dark theme for consistency."""
        # Import the dark theme from utils (same as delivery route)
        from utils import get_dark_theme
        self.setStyleSheet(get_dark_theme())
        
        # Additional styling for this specific tool (matching delivery route)
        additional_style = """
        QLabel {
            color: white;
            font-size: 13px;
            font-weight: bold;
            margin: 2px;
        }
        QLineEdit, QComboBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            font-size: 13px;
        }
        QLineEdit:focus, QComboBox:focus {
            border-color: #FFD700;
        }
        QPushButton {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 13px;
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
            background-color: #2C2C2C;
            border-radius: 4px;
            text-align: center;
            color: white;
            margin: 4px 0px;
        }
        QProgressBar::chunk {
            background-color: #FFD700;
            border-radius: 3px;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: white;
        }
        QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
        }
        QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border-color: #FFD700;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left-width: 1px;
            border-left-color: #555555;
            border-left-style: solid;
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
        }
        QComboBox QAbstractItemView {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            selection-background-color: #FFD700;
        }
        QTextEdit {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
        }
        """
        self.setStyleSheet(self.styleSheet() + additional_style)

    def visualize_altitude_profile(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        if not MATPLOTLIB_AVAILABLE:
            QMessageBox.warning(self, "Matplotlib Not Available", 
                              "Matplotlib is not available. Terrain visualization is disabled.")
            return

        try:
            # Get altitude in meters
            altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters
            
            # Extract waypoint data
            waypoint_coords = []
            for waypoint in self.waypoints:
                lat = waypoint["params"][4]
                lon = waypoint["params"][5]
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
            plt.figure(figsize=(12, 10))
            
            # Plot altitude profile with terrain
            waypoint_indices = list(range(len(waypoint_coords)))
            
            plt.subplot(2, 1, 1)
            plt.plot(distances_ft, amsl_altitudes_ft, 'b-', linewidth=2, label='AMSL Altitude (feet)')
            plt.plot(distances_ft, terrain_elevations_ft, 'g-', linewidth=2, label='Terrain Elevation (feet)')
            plt.plot(distances_ft, agl_altitudes_ft, 'r--', linewidth=2, label='AGL Altitude (feet)')
            plt.xlabel('Distance (feet)')
            plt.ylabel('Altitude (feet)')
            plt.title('Security Route Flight Altitude Profile with Terrain')
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
            
            stats_text = f"""Security Route Altitude Profile Summary
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
        
        except Exception as e:
            QMessageBox.warning(self, "Visualization Error", f"Error creating altitude profile: {str(e)}")

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


def main():
    app = QApplication(sys.argv)
    window = SecurityRoute()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()