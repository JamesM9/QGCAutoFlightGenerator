#!/usr/bin/env python3
"""
Mapping Flight Tool - Linear Flight Path Mission Planning
"""

import sys
import os
import math
import time
import requests
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
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                              QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
                              QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, 
                              QGroupBox, QTabWidget, QTextEdit, QSlider, QLineEdit,
                              QFormLayout, QSplitter, QListWidget, QListWidgetItem,
                              QMessageBox, QFileDialog, QProgressBar, QProgressDialog)
from PyQt5.QtCore import QUrl, Qt, pyqtSignal, QThread, QTimer, QObject, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from cpu_optimizer import (get_optimized_terrain_query, get_optimized_mission_generator, 
                          get_optimized_waypoint_optimizer, create_optimized_progress_dialog)
from shared_toolbar import SharedToolBar
# Import new aircraft parameter system
from aircraft_parameters import MissionToolBase

# Import existing components
from enhanced_map import EnhancedMapWidget
from enhanced_forms import EnhancedFormWidget
from settings_manager import settings_manager

import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, Point


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


class MappingFlightMapBridge(QObject):
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


class MappingSettings(QGroupBox):
    """QGC-compatible mapping settings"""
    
    def __init__(self, parent=None):
        super().__init__("Survey Settings", parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Camera Settings
        camera_group = QGroupBox("Camera Configuration")
        camera_layout = QFormLayout(camera_group)
        
        # Camera selection
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(["Custom Camera", "Yuneec CGOET", "DJI Mini 2", "GoPro Hero"])
        self.camera_combo.currentTextChanged.connect(self.on_camera_changed)
        camera_layout.addRow("Camera:", self.camera_combo)
        
        # Image overlap
        self.frontal_overlap = QSpinBox()
        self.frontal_overlap.setRange(50, 95)
        self.frontal_overlap.setValue(80)
        self.frontal_overlap.setSuffix(" %")
        camera_layout.addRow("Frontal Overlap:", self.frontal_overlap)
        
        self.side_overlap = QSpinBox()
        self.side_overlap.setRange(50, 95)
        self.side_overlap.setValue(80)
        self.side_overlap.setSuffix(" %")
        camera_layout.addRow("Side Overlap:", self.side_overlap)
        
        # Flight Settings
        flight_group = QGroupBox("Flight Configuration")
        flight_layout = QFormLayout(flight_group)
        
        # Flight altitude
        self.altitude = QDoubleSpinBox()
        self.altitude.setRange(10, 1000)
        self.altitude.setValue(100)
        self.altitude.setSuffix(" m")
        flight_layout.addRow("Flight Altitude:", self.altitude)
        
        # Flight speed
        self.speed = QDoubleSpinBox()
        self.speed.setRange(1, 50)
        self.speed.setValue(10)
        self.speed.setSuffix(" m/s")
        flight_layout.addRow("Flight Speed:", self.speed)
        
        # Transect angle
        self.transect_angle = QDoubleSpinBox()
        self.transect_angle.setRange(0, 359)
        self.transect_angle.setValue(0)
        self.transect_angle.setSuffix(" deg")
        flight_layout.addRow("Transect Angle:", self.transect_angle)
        
        # Turnaround distance
        self.turnaround_distance = QDoubleSpinBox()
        self.turnaround_distance.setRange(5, 100)
        self.turnaround_distance.setValue(10)
        self.turnaround_distance.setSuffix(" m")
        flight_layout.addRow("Turnaround Distance:", self.turnaround_distance)
        
        # Add groups to main layout
        layout.addRow(camera_group)
        layout.addRow(flight_group)
        
        # Initialize camera settings
        self.on_camera_changed("Custom Camera")
    
    def on_camera_changed(self, camera_name):
        """Update camera settings based on selection"""
        if camera_name == "Yuneec CGOET":
            self.sensor_width = 5.6405
            self.sensor_height = 3.1813
            self.focal_length = 3.5
            self.image_width = 1920
            self.image_height = 1080
        elif camera_name == "DJI Mini 2":
            self.sensor_width = 6.17
            self.sensor_height = 4.55
            self.focal_length = 4.49
            self.image_width = 4000
            self.image_height = 3000
        elif camera_name == "GoPro Hero":
            self.sensor_width = 6.17
            self.sensor_height = 4.55
            self.focal_length = 3.0
            self.image_width = 4000
            self.image_height = 3000
        else:  # Custom Camera
            self.sensor_width = 5.6405
            self.sensor_height = 3.1813
            self.focal_length = 3.5
            self.image_width = 1920
            self.image_height = 1080


class MappingStatistics(QGroupBox):
    """Basic mapping statistics"""
    
    def __init__(self, parent=None):
        super().__init__("Flight Statistics", parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Flight distance
        self.flight_distance = QLabel("0.0 km")
        layout.addRow("Flight Distance:", self.flight_distance)
        
        # Number of waypoints
        self.waypoint_count = QLabel("0")
        layout.addRow("Waypoints:", self.waypoint_count)
        
        # Estimated duration
        self.estimated_duration = QLabel("0:00")
        layout.addRow("Estimated Duration:", self.estimated_duration)
    
    def update_statistics(self, distance, waypoints, duration):
        """Update statistics display"""
        self.flight_distance.setText(f"{distance:.1f} km")
        self.waypoint_count.setText(str(waypoints))
        self.estimated_duration.setText(duration)


class MappingFlightWidget(MissionToolBase):
    """Main mapping flight planning widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("mapping_flight")
        self.mission_generator = get_optimized_mission_generator("mapping_flight")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("mapping_flight")
        
        self.flight_path = []
        self.takeoff_point = None
        self.landing_point = None
        self.polygon_coordinates = []
        self.polygon = None
        self.setting_takeoff = False
        self.setting_landing = False
        self.setup_ui()
        
    def setup_ui(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Map
        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)
        
        # Setup web channel for communication
        self.setup_web_channel()
        
        # Load the enhanced map
        self.load_enhanced_map()
        
        # Right panel - Settings
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create scroll area for settings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Settings container
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)
        
        # Title
        title = QLabel("Mapping Flight - Linear Path")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        settings_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "1. Set takeoff and landing points\n"
            "2. Draw polygon area for mapping\n"
            "3. Configure flight settings\n"
            "4. Generate mission"
        )
        instructions.setWordWrap(True)
        settings_layout.addWidget(instructions)
        
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
        
        settings_layout.addWidget(takeoff_landing_group)
        
        
        # Polygon Drawing Group
        polygon_group = QGroupBox("Mapping Area Definition")
        polygon_layout = QVBoxLayout(polygon_group)
        
        # Drawing instructions
        drawing_instructions = QLabel(
            "1. Click 'Start Drawing' to begin\n"
            "2. Click on the map to add polygon points\n"
            "3. Double-click to finish the polygon\n"
            "4. Use 'Clear Polygon' to start over"
        )
        drawing_instructions.setWordWrap(True)
        polygon_layout.addWidget(drawing_instructions)
        
        # Drawing buttons
        drawing_button_layout = QHBoxLayout()
        self.start_drawing_btn = QPushButton("Start Drawing")
        self.start_drawing_btn.clicked.connect(self.start_polygon_drawing)
        drawing_button_layout.addWidget(self.start_drawing_btn)
        
        self.clear_polygon_btn = QPushButton("Clear Polygon")
        self.clear_polygon_btn.clicked.connect(self.clear_polygon)
        drawing_button_layout.addWidget(self.clear_polygon_btn)
        
        polygon_layout.addLayout(drawing_button_layout)
        
        # Load KML button
        self.load_kml_btn = QPushButton("Load KML File")
        self.load_kml_btn.clicked.connect(self.load_kml_file)
        polygon_layout.addWidget(self.load_kml_btn)
        
        settings_layout.addWidget(polygon_group)
        
        # Mapping settings
        self.mapping_settings = MappingSettings()
        settings_layout.addWidget(self.mapping_settings)
        
        # Statistics
        self.statistics = MappingStatistics()
        settings_layout.addWidget(self.statistics)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_btn)
        
        self.generate_btn = QPushButton("Generate Mission")
        self.generate_btn.clicked.connect(self.generate_mission)
        self.generate_btn.setEnabled(False)
        button_layout.addWidget(self.generate_btn)
        
        settings_layout.addLayout(button_layout)
        settings_layout.addStretch()
        
        scroll.setWidget(settings_widget)
        right_layout.addWidget(scroll)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([800, 400])  # Initial split ratio
        
        layout.addWidget(splitter)
        
        # Initialize status
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setText("Ready to define mapping area...")
        settings_layout.addWidget(self.status_text)
        
    # Aircraft Configuration Methods

    def setup_web_channel(self):
        """Setup communication between Python and JavaScript."""
        self.channel = QWebChannel()
        
        # Create bridge object for QWebChannel communication
        self.map_bridge = MappingFlightMapBridge()
        self.map_bridge.parent_widget = self
        
        self.channel.registerObject('pywebchannel', self.map_bridge)
        self.web_view.page().setWebChannel(self.channel)

    def load_enhanced_map(self):
        """Load the enhanced map with polygon drawing capabilities."""
        # Create enhanced map HTML content
        map_html = self.create_enhanced_map_html()
        
        # Create a temporary HTML file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(map_html)
            temp_path = f.name
        
        self.web_view.setUrl(QUrl.fromLocalFile(temp_path))
        
        # Clean up the temporary file after loading (with error handling)
        def cleanup_temp_file():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors
        
        QTimer.singleShot(1000, cleanup_temp_file)

    def create_enhanced_map_html(self):
        """Create enhanced map HTML with polygon drawing capabilities."""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mapping Flight Map</title>
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
                <h4>Mapping Area Drawing</h4>
                <p><strong>Status:</strong> <span id="drawing-status">Ready</span></p>
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
                    updateStatus('Drawing - Click to add points');
                    document.getElementById('start-drawing').disabled = true;
                    document.getElementById('finish-drawing').disabled = false;
                    document.getElementById('start-drawing').classList.add('active');
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function startTakeoffSelection() {
                    drawing = false;
                    takeoffSelectionMode = true;
                    landingSelectionMode = false;
                    updateStatus('Takeoff Selection - Click to set takeoff location');
                    map.getContainer().style.cursor = 'crosshair';
                }
                
                function startLandingSelection() {
                    drawing = false;
                    takeoffSelectionMode = false;
                    landingSelectionMode = true;
                    updateStatus('Landing Selection - Click to set landing location');
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
                    updateStatus('Polygon complete');
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
                    updateStatus('Ready');
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
                
                function updateStatus(status) {
                    document.getElementById('drawing-status').textContent = status;
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
                        updateStatus('Takeoff location set');
                        
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
                        updateStatus('Landing location set');
                        
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
                
                updateStatus('Ready');
            </script>
        </body>
        </html>
        """
        
    def handle_map_click(self, lat, lng):
        """Handle map click events with coordinate display."""
        # The popup is now handled by the JavaScript createPopupContent function
        # No need to show a QMessageBox dialog
        pass

    def start_takeoff_selection(self):
        """Start takeoff location selection mode."""
        self.status_text.setText("Takeoff selection mode activated. Click on the map to set takeoff location.")
        self.web_view.page().runJavaScript("startTakeoffSelection();")

    def start_landing_selection(self):
        """Start landing location selection mode."""
        self.status_text.setText("Landing selection mode activated. Click on the map to set landing location.")
        self.web_view.page().runJavaScript("startLandingSelection();")

    def clear_takeoff_location(self):
        """Clear the takeoff location."""
        self.takeoff_point = None
        self.takeoff_location_label.setText("Not set - Click 'Set Takeoff' and click on map")
        self.takeoff_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.web_view.page().runJavaScript("clearTakeoffMarker();")
        self.status_text.setText("Takeoff location cleared.")

    def clear_landing_location(self):
        """Clear the landing location."""
        self.landing_point = None
        self.landing_location_label.setText("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.web_view.page().runJavaScript("clearLandingMarker();")
        self.status_text.setText("Landing location cleared.")

    def handle_takeoff_location_selected(self, lat, lng):
        """Handle takeoff location selection from map."""
        self.takeoff_point = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.takeoff_location_label.setText(f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.takeoff_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.status_text.setText(f"Takeoff location set to: {lat:.6f}, {lng:.6f}\nElevation: {terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")

    def handle_landing_location_selected(self, lat, lng):
        """Handle landing location selection from map."""
        self.landing_point = {"lat": lat, "lng": lng}
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.landing_location_label.setText(f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.status_text.setText(f"Landing location set to: {lat:.6f}, {lng:.6f}\nElevation: {terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)")

    def start_polygon_drawing(self):
        """Start polygon drawing mode."""
        self.status_text.setText("Drawing mode activated. Click on the map to add polygon points.")
        self.web_view.page().runJavaScript("startDrawing();")

    def clear_polygon(self):
        """Clear the current polygon."""
        self.polygon_coordinates = []
        self.polygon = None
        self.status_text.setText("Polygon cleared. Ready to draw new area.")
        self.generate_btn.setEnabled(False)
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
            
            self.status_text.setText(f"Mapping area defined with {len(coordinates)} points.\nArea: {area_km2:.2f} km²\n\nCoordinates:\n{coord_display}")
            self.generate_btn.setEnabled(True)
        else:
            self.status_text.setText("Invalid polygon. Need at least 3 points.")

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
                    else:
                        QMessageBox.warning(self, "Invalid KML", "KML file must contain at least 3 polygon points.")
                else:
                    QMessageBox.warning(self, "Invalid KML", "No polygon coordinates found in KML file.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading KML file: {str(e)}")

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
        
    def clear_all(self):
        """Clear all current data"""
        self.flight_path = []
        self.takeoff_point = None
        self.landing_point = None
        self.polygon_coordinates = []
        self.polygon = None
        self.generate_btn.setEnabled(False)
        self.status_text.setText("All data cleared. Ready to start over.")
        
        # Clear map markers
        self.web_view.page().runJavaScript("clearPolygon(); clearTakeoffMarker(); clearLandingMarker();")
        
        # Reset labels
        self.takeoff_location_label.setText("Not set - Click 'Set Takeoff' and click on map")
        self.takeoff_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        self.landing_location_label.setText("Not set - Click 'Set Landing' and click on map")
        self.landing_location_label.setStyleSheet("color: #FFA500; font-style: italic;")
        

    
    def generate_mission(self):
        """Generate QGC-compatible mapping mission"""
        if not self.polygon:
            QMessageBox.warning(self, "No Area", "Please define a mapping area first.")
            return
            
        if not self.takeoff_point:
            QMessageBox.warning(self, "No Takeoff Point", "Please set a takeoff location first.")
            return
            
        if not self.landing_point:
            QMessageBox.warning(self, "No Landing Point", "Please set a landing location first.")
            return
        
        # Show progress dialog
        progress = QProgressDialog("Generating mission waypoints...", "Cancel", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(True)
        progress.show()
        
        try:
            # Generate waypoints for the mission
            waypoints = self.generate_mission_waypoints(progress)
            
            if not waypoints:
                QMessageBox.warning(self, "Generation Failed", "Failed to generate waypoints. Please check your settings.")
                return
            
            # Save mission using new file generation system
            mission_data = self.create_qgc_mission_data(waypoints)
            saved_file = self.save_mission_file(mission_data, "mapping_flight")
            if saved_file:
                QMessageBox.information(self, "Mission Generated", 
                                      f"Mission saved to {saved_file}\n\nGenerated {len(waypoints)} waypoints.")
                
                # Check for terrain proximity warnings
                altitude_meters = self.mapping_settings.altitude.value() * 0.3048  # Convert feet to meters
                proximity_warnings = self.check_terrain_proximity(altitude_meters)
                
                if proximity_warnings:
                    self.show_terrain_proximity_warning(proximity_warnings)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating mission: {str(e)}")
        finally:
            progress.close()
    
    def create_qgc_mission_data(self, waypoints):
        """Create QGC-compatible mission data structure."""
        # Calculate camera footprint
        altitude = self.mapping_settings.altitude.value()
        focal_length = self.mapping_settings.focal_length
        sensor_width = self.mapping_settings.sensor_width
        sensor_height = self.mapping_settings.sensor_height
        
        frontal_footprint = (sensor_width * altitude) / focal_length
        side_footprint = (sensor_height * altitude) / focal_length
        
        # Create mission items
        mission_items = []
        
        # Mission start
        mission_items.append({
            "autoContinue": True,
            "command": 530,
            "doJumpId": 1,
            "frame": 2,
            "params": [0, 2, None, None, None, None, None],
            "type": "SimpleItem"
        })
        
        # Takeoff
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": altitude,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 22,
            "doJumpId": 2,
            "frame": 3,
            "params": [0, 0, 0, None, self.takeoff_point["lat"], self.takeoff_point["lng"], altitude],
            "type": "SimpleItem"
        })
        
        # Survey Complex Item
        survey_item = {
            "TransectStyleComplexItem": {
                "CameraCalc": {
                    "AdjustedFootprintFrontal": frontal_footprint,
                    "AdjustedFootprintSide": side_footprint,
                    "CameraName": self.mapping_settings.camera_combo.currentText(),
                    "DistanceMode": 3,
                    "DistanceToSurface": altitude,
                    "FixedOrientation": True,
                    "FocalLength": focal_length,
                    "FrontalOverlap": self.mapping_settings.frontal_overlap.value(),
                    "ImageDensity": 1.0,
                    "ImageHeight": self.mapping_settings.image_height,
                    "ImageWidth": self.mapping_settings.image_width,
                    "Landscape": True,
                    "MinTriggerInterval": 1.0,
                    "SensorHeight": sensor_height,
                    "SensorWidth": sensor_width,
                    "SideOverlap": self.mapping_settings.side_overlap.value(),
                    "ValueSetIsDistance": True,
                    "version": 2
                },
                "CameraShots": len(waypoints),
                "CameraTriggerInTurnAround": True,
                "HoverAndCapture": False,
                "Items": [],
                "Refly90Degrees": False,
                "TerrainAdjustMaxClimbRate": 0,
                "TerrainAdjustMaxDescentRate": 0,
                "TerrainAdjustTolerance": 30.48,
                "TerrainFlightSpeed": self.mapping_settings.speed.value(),
                "TurnAroundDistance": self.mapping_settings.turnaround_distance.value(),
                "VisualTransectPoints": [],
                "version": 2
            },
            "angle": self.mapping_settings.transect_angle.value(),
            "complexItemType": "survey",
            "entryLocation": 0,
            "flyAlternateTransects": False,
            "polygon": self.polygon_coordinates,
            "splitConcavePolygons": False,
            "type": "ComplexItem",
            "version": 5
        }
        
        # Add waypoints to survey item
        for i, waypoint in enumerate(waypoints[1:-1], 3):  # Skip takeoff and landing
            survey_item["TransectStyleComplexItem"]["Items"].append({
                "autoContinue": True,
                "command": 16,  # NAV_WAYPOINT
                "doJumpId": i,
                "frame": 0,
                "params": [0, 0, 0, None, waypoint["lat"], waypoint["lng"], waypoint["alt"]],
                "type": "SimpleItem"
            })
            
            # Add camera trigger command
            survey_item["TransectStyleComplexItem"]["Items"].append({
                "autoContinue": True,
                "command": 206,  # DO_DIGICAM_CONTROL
                "doJumpId": i + 1,
                "frame": 2,
                "params": [frontal_footprint, 0, 1, 0, 0, 0, 0],
                "type": "SimpleItem"
            })
        
        # Add visual transect points for display
        for waypoint in waypoints[1:-1]:
            survey_item["TransectStyleComplexItem"]["VisualTransectPoints"].append([
                waypoint["lat"], waypoint["lng"]
            ])
        
        mission_items.append(survey_item)
        
        # Return to Launch
        mission_items.append({
            "autoContinue": True,
            "command": 20,  # NAV_RETURN_TO_LAUNCH
            "doJumpId": len(waypoints) + 2,
            "frame": 2,
            "params": [0, 0, 0, 0, 0, 0, 0],
            "type": "SimpleItem"
        })
        
        # Get aircraft-specific parameters using new system
        aircraft_info = self.get_aircraft_info_for_export()
        
        # Use aircraft-aware speed if available, otherwise use mapping settings
        if self.is_parameters_enabled():
            cruise_speed = aircraft_info["cruiseSpeed"]
        else:
            cruise_speed = self.mapping_settings.speed.value()

        return {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [],
                "version": 2
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": cruise_speed,
                "firmwareType": 12 if aircraft_info["firmwareType"] == "arducopter" else 11 if aircraft_info["firmwareType"] == "arduplane" else 12,
                "globalPlanAltitudeMode": 0,
                "hoverSpeed": aircraft_info["hoverSpeed"],
                "items": mission_items,
                "plannedHomePosition": [
                    self.takeoff_point["lat"],
                    self.takeoff_point["lng"],
                    5
                ],
                "vehicleType": 1 if aircraft_info["vehicleType"] == "fixedwing" else 2,
                "version": 2,
                "aircraftParameters": aircraft_info["aircraftParameters"]
            },
            "rallyPoints": {
                "points": [],
                "version": 2
            },
            "version": 1
        }
    
    def generate_mission_waypoints(self, progress=None):
        """Generate QGC-compatible survey waypoints"""
        waypoints = []
        
        if progress:
            progress.setValue(10)
            progress.setLabelText("Adding takeoff waypoint...")
        
        # Add takeoff waypoint
        waypoints.append({
            "index": 0,
            "type": "takeoff",
            "lat": self.takeoff_point["lat"],
            "lng": self.takeoff_point["lng"],
            "alt": self.mapping_settings.altitude.value(),
            "action": "takeoff"
        })
        
        if progress:
            progress.setValue(20)
            progress.setLabelText("Generating transect waypoints...")
        
        # Generate transect waypoints within the polygon
        transect_waypoints = self.generate_transect_waypoints(progress)
        
        if not transect_waypoints:
            return []
        
        # Add transect waypoints
        for i, point in enumerate(transect_waypoints, 1):
            waypoints.append({
                "index": i,
                "type": "waypoint",
                "lat": point["lat"],
                "lng": point["lng"],
                "alt": point["alt"],
                "action": "continue"
            })
            
            if progress and i % 10 == 0:
                progress.setValue(20 + int(70 * i / len(transect_waypoints)))
                progress.setLabelText(f"Processing waypoint {i}/{len(transect_waypoints)}...")
        
        if progress:
            progress.setValue(90)
            progress.setLabelText("Adding landing waypoint...")
        
        # Add landing waypoint
        waypoints.append({
            "index": len(waypoints),
            "type": "landing",
            "lat": self.landing_point["lat"],
            "lng": self.landing_point["lng"],
            "alt": 0,  # Land at ground level
            "action": "land"
        })
        
        if progress:
            progress.setValue(100)
        
        return waypoints

    def generate_transect_waypoints(self, progress=None):
        """Generate QGC-style transect waypoints within the polygon."""
        if not self.polygon:
            return []
        
        # Calculate camera footprint based on altitude and camera settings
        altitude = self.mapping_settings.altitude.value()
        focal_length = self.mapping_settings.focal_length
        sensor_width = self.mapping_settings.sensor_width
        sensor_height = self.mapping_settings.sensor_height
        
        # Calculate ground footprint (in meters)
        frontal_footprint = (sensor_width * altitude) / focal_length
        side_footprint = (sensor_height * altitude) / focal_length
        
        # Calculate transect spacing based on side overlap
        side_overlap = self.mapping_settings.side_overlap.value() / 100.0
        transect_spacing = side_footprint * (1 - side_overlap)
        
        # Calculate waypoint spacing based on frontal overlap
        frontal_overlap = self.mapping_settings.frontal_overlap.value() / 100.0
        waypoint_spacing = frontal_footprint * (1 - frontal_overlap)
        
        # Get polygon bounds
        minx, miny, maxx, maxy = self.polygon.bounds
        
        # Convert spacing to degrees (approximate)
        transect_spacing_deg = transect_spacing / 111000
        waypoint_spacing_deg = waypoint_spacing / 111000
        
        # Safety check: limit minimum spacing to prevent too many waypoints
        if transect_spacing_deg < 0.0001:  # About 11 meters
            transect_spacing_deg = 0.0001
        if waypoint_spacing_deg < 0.0001:
            waypoint_spacing_deg = 0.0001
        
        # Generate transects
        transect_angle = math.radians(self.mapping_settings.transect_angle.value())
        turnaround_distance = self.mapping_settings.turnaround_distance.value() / 111000
        
        if progress:
            progress.setLabelText("Calculating transect lines...")
        
        # Calculate transect lines
        transect_lines = self.calculate_transect_lines(
            minx, miny, maxx, maxy, 
            transect_spacing_deg, transect_angle, turnaround_distance
        )
        
        if not transect_lines:
            return []
        
        # Generate waypoints along transects
        waypoints = []
        total_lines = len(transect_lines)
        
        for i, line in enumerate(transect_lines):
            if progress:
                progress.setLabelText(f"Processing transect {i+1}/{total_lines}...")
                progress.setValue(20 + int(30 * i / total_lines))
            
            line_waypoints = self.generate_waypoints_along_line(
                line, waypoint_spacing_deg, altitude, progress
            )
            waypoints.extend(line_waypoints)
            
            # Safety check: limit total waypoints to prevent freezing
            if len(waypoints) > 1000:
                print(f"Warning: Limiting waypoints to 1000 (current: {len(waypoints)})")
                break
        
        return waypoints
    
    def calculate_transect_lines(self, minx, miny, maxx, maxy, spacing, angle, turnaround):
        """Calculate transect lines within the polygon bounds."""
        lines = []
        
        # Calculate the direction vector for transects
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        # Calculate perpendicular direction for spacing
        perp_dx = -dy
        perp_dy = dx
        
        # Start from one corner and move perpendicular to transect direction
        start_x = minx
        start_y = miny
        
        # Calculate how many transects we need
        width = maxx - minx
        height = maxy - miny
        diagonal = math.sqrt(width**2 + height**2)
        num_transects = int(diagonal / spacing) + 2
        
        # Safety check: limit number of transects to prevent freezing
        if num_transects > 100:
            num_transects = 100
            print(f"Warning: Limiting transects to 100 (calculated: {int(diagonal / spacing) + 2})")
        
        for i in range(num_transects):
            # Calculate transect start and end points
            offset_x = i * spacing * perp_dx
            offset_y = i * spacing * perp_dy
            
            # Start point with turnaround distance
            line_start_x = start_x + offset_x - turnaround * dx
            line_start_y = start_y + offset_y - turnaround * dy
            
            # End point with turnaround distance
            line_end_x = start_x + offset_x + diagonal * dx + turnaround * dx
            line_end_y = start_y + offset_y + diagonal * dy + turnaround * dy
            
            # Check if this transect intersects with the polygon
            line = [(line_start_x, line_start_y), (line_end_x, line_end_y)]
            if self.transect_intersects_polygon(line):
                lines.append(line)
        
        return lines
    
    def transect_intersects_polygon(self, line):
        """Check if a transect line intersects with the polygon."""
        from shapely.geometry import LineString
        
        line_geom = LineString(line)
        return self.polygon.intersects(line_geom)
    
    def generate_waypoints_along_line(self, line, spacing, altitude, progress=None):
        """Generate waypoints along a transect line."""
        waypoints = []
        
        start_x, start_y = line[0]
        end_x, end_y = line[1]
        
        # Calculate line length
        length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
        
        # Calculate number of waypoints
        num_waypoints = int(length / spacing) + 1
        
        # Safety check: limit waypoints per line to prevent freezing
        if num_waypoints > 50:
            num_waypoints = 50
            print(f"Warning: Limiting waypoints per line to 50 (calculated: {int(length / spacing) + 1})")
        
        for i in range(num_waypoints):
            # Interpolate position along line
            t = i / (num_waypoints - 1) if num_waypoints > 1 else 0
            lat = start_x + t * (end_x - start_x)
            lng = start_y + t * (end_y - start_y)
            
            # Check if point is within polygon
            point = Point(lat, lng)
            if self.polygon.contains(point):
                # Use terrain elevation if available, otherwise use default
                try:
                    terrain_elevation = self.terrain_query.get_elevation(lat, lng)
                    absolute_altitude = terrain_elevation + altitude
                except:
                    # Fallback to altitude above ground level
                    absolute_altitude = altitude
                
                waypoints.append({
                    "lat": lat,
                    "lng": lng,
                    "alt": absolute_altitude
                })
        
        return waypoints
    
    def get_mapping_settings(self):
        """Get current mapping settings as dictionary"""
        return {
            "camera": self.mapping_settings.camera_combo.currentText(),
            "frontal_overlap": self.mapping_settings.frontal_overlap.value(),
            "side_overlap": self.mapping_settings.side_overlap.value(),
            "altitude": self.mapping_settings.altitude.value(),
            "speed": self.mapping_settings.speed.value(),
            "transect_angle": self.mapping_settings.transect_angle.value(),
            "turnaround_distance": self.mapping_settings.turnaround_distance.value(),
            "sensor_width": self.mapping_settings.sensor_width,
            "sensor_height": self.mapping_settings.sensor_height,
            "focal_length": self.mapping_settings.focal_length,
            "image_width": self.mapping_settings.image_width,
            "image_height": self.mapping_settings.image_height
        }

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not hasattr(self, 'waypoints') or not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters
        altitude_meters = self.mapping_settings.altitude.value()
        
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
        plt.figure(figsize=(12, 10))
        
        # Plot altitude profile with terrain
        waypoint_indices = list(range(len(waypoint_coords)))
        
        plt.subplot(2, 1, 1)
        plt.plot(distances_ft, amsl_altitudes_ft, 'b-', linewidth=2, label='AMSL Altitude (feet)')
        plt.plot(distances_ft, terrain_elevations_ft, 'g-', linewidth=2, label='Terrain Elevation (feet)')
        plt.plot(distances_ft, agl_altitudes_ft, 'r--', linewidth=2, label='AGL Altitude (feet)')
        plt.xlabel('Distance (feet)')
        plt.ylabel('Altitude (feet)')
        plt.title('Mapping Flight Altitude Profile with Terrain')
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
        
        stats_text = f"""Mapping Flight Altitude Profile Summary
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


class MappingFlight(QMainWindow):
    """Main mapping flight application window"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.apply_qgc_theme()
        
    def setup_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Mapping Flight")
        self.setGeometry(100, 100, 1600, 1000)
        self.showMaximized()
        
        # Add shared toolbar
        self.toolbar = SharedToolBar(self)
        self.addToolBar(self.toolbar)
        
        # Create central widget
        central_widget = MappingFlightWidget()
        self.setCentralWidget(central_widget)
        
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
                background-color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: white;
            }
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
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
        """)

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("VERSATILE UAS Flight Generator - Mapping Flight")
    
    window = MappingFlight()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
