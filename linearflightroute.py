import sys
import json
import time
import requests
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from math import tan, radians, cos  # Import cos and radians
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
from PyQt5.QtCore import QUrl, QSettings, pyqtSlot, Qt
from PyQt5.QtWebChannel import QWebChannel
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit,
    QDoubleSpinBox, QLineEdit, QHBoxLayout, QSpinBox, QProgressBar, QComboBox, QMessageBox, QFrame,
    QGroupBox, QScrollArea, QGridLayout, QSplitter
)
from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
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
                elif response.status_code == 429:  # Too many requests
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0





class LinearFlightRouteMapBridge(QObject):
    """Bridge class for communication between JavaScript and Python for linear flight route."""
    
    @pyqtSlot(list)
    def receive_path(self, coordinates):
        """Receive path coordinates from JavaScript drawing."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_path_received(coordinates)
    
    @pyqtSlot(float, float)
    def setStartLocation(self, lat, lng):
        """Set start location from map click."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def setEndLocation(self, lat, lng):
        """Set end location from map click."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_map_click(self, lat, lng):
        """Handle general map click."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_map_click(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_takeoff_location(self, lat, lng):
        """Handle takeoff location selection from map."""
        if hasattr(self, 'parent_widget'):
            self.parent_widget.handle_takeoff_location_selected(lat, lng)
    
    @pyqtSlot(float, float)
    def receive_landing_location(self, lat, lng):
        """Handle landing location selection from map."""
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


class LinearFlightRoute(MissionToolBase):
    def __init__(self):
        super().__init__()
        
        # Use optimized components
        self.terrain_query = get_optimized_terrain_query("linear_flight_route")
        self.mission_generator = get_optimized_mission_generator("linear_flight_route")
        self.waypoint_optimizer = get_optimized_waypoint_optimizer("linear_flight_route")
        
        self.settings = QSettings("FlightPlanner", "LinearFlightRoute")
        self.path_coordinates = []
        self.takeoff_point = None
        self.landing_point = None
        self.drawing_path = False  # Track drawing state
        self.init_ui()
        self.apply_qgc_theme()

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

    def show_location_details(self, lat, lng, location_type):
        """Show detailed location information with coordinates and elevation."""
        # Get terrain elevation
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        # Format coordinates
        decimal_coords = f"{lat:.6f}, {lng:.6f}"
        dms_coords = self.format_dms(lat, lng)
        elevation_info = f"{terrain_elevation:.1f} meters ({elevation_feet:.1f} feet)"
        
        # Create detailed message
        message = f"""{location_type} Location Information:

Decimal Coordinates:
{decimal_coords}

DMS Coordinates:
{dms_coords}

Elevation:
{elevation_info}"""
        
        QMessageBox.information(self, f"{location_type} Location Details", message)

    def init_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Linear Flight Route Planner")
        self.resize(1200, 700)

        # Add shared toolbar
        self.toolbar = SharedToolBar(self)
        self.addToolBar(self.toolbar)

        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QHBoxLayout(self.central_widget)

        # Left-side control panel (30% width) with scrollable area
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        
        # Create scroll area for controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Control container
        control_widget = QWidget()
        self.control_panel = QVBoxLayout(control_widget)
        self.control_panel.setContentsMargins(20, 20, 20, 20)
        self.control_panel.setSpacing(15)
        
        left_panel_layout.addWidget(scroll)
        self.layout.addWidget(left_panel, 3)  # Stretch factor of 3 (30%)

        # Path input section
        path_label = QLabel("Flight Path Input:")
        path_label.setStyleSheet("font-weight: bold; color: #FFD700; margin-top: 10px;")
        self.control_panel.addWidget(path_label)

        self.load_button = QPushButton("Load KML Path File")
        self.control_panel.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_kml_file)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.control_panel.addWidget(separator)
        
        # Drawing controls section
        drawing_label = QLabel("Path Drawing Tools:")
        drawing_label.setStyleSheet("font-weight: bold; color: #FFD700; margin-top: 10px;")
        self.control_panel.addWidget(drawing_label)
        
        # Drawing buttons
        self.start_drawing_btn = QPushButton("Start Drawing Path")
        self.start_drawing_btn.clicked.connect(self.start_path_drawing)
        self.control_panel.addWidget(self.start_drawing_btn)
        
        self.clear_path_btn = QPushButton("Clear Path")
        self.clear_path_btn.clicked.connect(self.clear_path)
        self.control_panel.addWidget(self.clear_path_btn)
        
        # Status text for drawing feedback
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        self.status_text.setText("Ready to draw flight path. Click 'Start Drawing Path' to begin.")
        self.control_panel.addWidget(self.status_text)

        self.altitude_label = QLabel("Set Altitude Above Terrain (Feet):")
        self.control_panel.addWidget(self.altitude_label)
        self.altitude_input = QDoubleSpinBox()
        self.altitude_input.setRange(1, 16404)
        self.altitude_input.setValue(self.settings.value("altitude", 164, type=float))
        self.control_panel.addWidget(self.altitude_input)

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
        
        self.control_panel.addWidget(takeoff_landing_group)
        
        
        # Legacy takeoff input field (hidden by default)
        self.takeoff_input = QLineEdit()
        self.takeoff_input.setPlaceholderText("Enter as: latitude, longitude")
        self.takeoff_input.setText(self.settings.value("takeoff_point", ""))
        self.takeoff_input.setVisible(False)  # Hide legacy input

        # Drone Type Selection (fallback)
        self.drone_type_label = QLabel("Select Drone Type:")
        self.control_panel.addWidget(self.drone_type_label)
        self.drone_type_dropdown = QComboBox()
        self.drone_type_dropdown.addItems(["Multicopter/Helicopter", "Fixed-Wing", "Quadplane/VTOL Hybrid"])
        self.drone_type_dropdown.setCurrentText(self.settings.value("drone_type", "Multicopter/Helicopter"))
        self.control_panel.addWidget(self.drone_type_dropdown)

        # Waypoint Interval
        self.interval_label = QLabel("Waypoint Interval (meters):")
        self.control_panel.addWidget(self.interval_label)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 1000)
        self.interval_input.setValue(self.settings.value("interval", 50, type=int))
        self.control_panel.addWidget(self.interval_input)

        # Legacy landing input field (hidden by default)
        self.landing_input = QLineEdit()
        self.landing_input.setPlaceholderText("Enter as: latitude, longitude")
        self.landing_input.setText(self.settings.value("landing_point", ""))
        self.landing_input.setVisible(False)  # Hide legacy input

        self.generate_flight_button = QPushButton("Generate Flight Plan")
        self.control_panel.addWidget(self.generate_flight_button)
        self.generate_flight_button.clicked.connect(self.generate_flight_plan)
        self.generate_flight_button.setEnabled(False)
        
        # Clear waypoints button
        self.clear_waypoints_button = QPushButton("Clear Waypoints")
        self.control_panel.addWidget(self.clear_waypoints_button)
        self.clear_waypoints_button.clicked.connect(self.clear_waypoints)

        # Button to export flight path as KMZ/KML (initially disabled)
        self.export_btn = QPushButton("Export Flight Path (KMZ/KML)")
        self.control_panel.addWidget(self.export_btn)
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self.export_flight_path)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.control_panel.addWidget(self.progress_bar)

        # Label for file info
        self.file_label = QLabel("No file loaded.")
        self.control_panel.addWidget(self.file_label)

        # Text box for displaying coordinates and generated flight path
        self.coordinates_text = QTextEdit()
        self.coordinates_text.setReadOnly(True)
        self.control_panel.addWidget(self.coordinates_text)

        # Set up scroll area
        scroll.setWidget(control_widget)

        # Right-side map view
        self.map_view = QWebEngineView()
        
        # Set up communication channel for map interactions
        self.channel = QWebChannel()
        
        # Create map bridge and set parent widget
        self.map_bridge = LinearFlightRouteMapBridge()
        self.map_bridge.parent_widget = self
        
        self.channel.registerObject('pywebchannel', self.map_bridge)
        self.map_view.page().setWebChannel(self.channel)
        
        self.layout.addWidget(self.map_view, 7)  # Stretch factor of 7 (70%)
        self.load_google_maps()

    def closeEvent(self, event):
        """Save user preferences when the application is closed."""
        self.settings.setValue("altitude", self.altitude_input.value())
        self.settings.setValue("takeoff_point", self.takeoff_input.text())
        self.settings.setValue("drone_type", self.drone_type_dropdown.currentText())
        self.settings.setValue("interval", self.interval_input.value())
        self.settings.setValue("landing_point", self.landing_input.text())
        event.accept()

    def load_google_maps(self):
        """Load the enhanced map with path drawing capabilities."""
        html_content = self.create_enhanced_map_html()
        
        # Create a temporary HTML file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            temp_path = f.name
        
        self.map_view.setUrl(QUrl.fromLocalFile(temp_path))
        
        # Clean up the temporary file after loading
        QTimer.singleShot(1000, lambda: os.unlink(temp_path) if os.path.exists(temp_path) else None)
    


    def create_enhanced_map_html(self):
        """Create enhanced map HTML with path drawing capabilities."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Linear Flight Route Map</title>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                  crossorigin=""/>
            
            <!-- Leaflet JavaScript -->
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                    crossorigin=""></script>
            
            <!-- QWebChannel JavaScript -->
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                }}
                #map {{
                    width: 100%;
                    height: 100vh;
                }}
                
                /* Path Drawing Controls */
                .path-controls {{
                    position: absolute;
                    bottom: 10px;
                    right: 10px;
                    background: white;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                    z-index: 1000;
                    min-width: 150px;
                }}
                
                .path-controls h4 {{
                    margin: 0 0 10px 0;
                    color: #333;
                    font-size: 14px;
                    text-align: center;
                }}
                
                .path-controls button {{
                    width: 100%;
                    margin-bottom: 8px;
                    padding: 10px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 12px;
                    display: block;
                }}
                
                .path-controls button#start-path-drawing {{
                    background: #007bff;
                    color: white;
                }}
                
                .path-controls button#finish-path {{
                    background: #28a745;
                    color: white;
                }}
                
                .path-controls button#clear-path {{
                    background: #dc3545;
                    color: white;
                }}
                
                /* Address Search Styles */
                .search-container {{
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    z-index: 1000;
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    min-width: 300px;
                }}
                
                .search-container h4 {{
                    margin: 0 0 10px 0;
                    color: #333;
                    font-size: 14px;
                }}
                
                .search-input {{
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    font-size: 14px;
                    box-sizing: border-box;
                }}
                
                .search-button {{
                    margin-top: 5px;
                    padding: 8px 12px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 14px;
                }}
                
                .search-button:hover {{
                    background: #0056b3;
                }}
                
                .search-results {{
                    margin-top: 10px;
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background: white;
                }}
                
                .search-result-item {{
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                    cursor: pointer;
                    font-size: 12px;
                }}
                
                .search-result-item:hover {{
                    background: #f8f9fa;
                }}
                
                .search-result-item:last-child {{
                    border-bottom: none;
                }}
                
                .search-result-title {{
                    font-weight: bold;
                    color: #333;
                }}
                
                .search-result-address {{
                    color: #666;
                    font-size: 11px;
                }}
                
                .search-result-item.selected {{
                    background: #007bff;
                    color: white;
                }}
                
                .search-result-item.selected .search-result-title,
                .search-result-item.selected .search-result-address {{
                    color: white;
                }}
                
                /* Path Status Panel */
                .path-status {{
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    z-index: 1000;
                    max-width: 300px;
                }}
                
                .path-status h4 {{
                    margin: 0 0 5px 0;
                    color: #333;
                    font-size: 14px;
                }}
                
                .path-status p {{
                    margin: 2px 0;
                    font-size: 12px;
                    color: #555;
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            
            <!-- Address Search Container -->
            <div class="search-container">
                <h4>Search Address</h4>
                <input type="text" id="search-input" class="search-input" placeholder="Enter address, city, or landmark...">
                <button id="search-button" class="search-button">Search</button>
                <div id="search-results" class="search-results" style="display: none;"></div>
            </div>
            
            <!-- Path Status Panel -->
            <div class="path-status">
                <h4>Flight Path Drawing</h4>
                <p><strong>Status:</strong> <span id="path-status">Ready</span></p>
                <p><strong>Points:</strong> <span id="point-count">0</span></p>
                <p><strong>Distance:</strong> <span id="path-distance">0</span> km</p>
            </div>
            
            <!-- Path Drawing Controls -->
            <div class="path-controls">
                <h4>Path Tools</h4>
                <button id="start-path-drawing">Start Drawing</button>
                <button id="finish-path" disabled>Finish Path</button>
                <button id="clear-path">Clear Path</button>
            </div>
            
            <script>
                // Initialize QWebChannel
                let pywebchannel;
                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    pywebchannel = channel.objects.pywebchannel;
                    console.log('QWebChannel initialized');
                }});
                
                // Initialize map
                let map = L.map('map').setView([40.7128, -74.0060], 10);
                
                // Add tile layers with updated sources for the most current maps
                // 1. OpenStreetMap - Latest community-driven street data
                let openStreetMapLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    maxZoom: 19
                }});
                
                // 2. CartoDB Positron - Clean, modern street map with latest data
                let cartoPositronLayer = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                }});
                
                // 3. CartoDB Voyager - Enhanced street map with more details and latest updates
                let cartoVoyagerLayer = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                }});
                
                // 4. High-Resolution Satellite (Esri World Imagery) - Latest satellite imagery
                let satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                }});
                
                // 5. Google Satellite - Alternative high-resolution satellite source (DEFAULT LAYER)
                let googleSatelliteLayer = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{
                    attribution: '© Google',
                    maxZoom: 20
                }}).addTo(map);
                
                // 6. Hybrid layer (Satellite + Labels)
                let hybridLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                }});
                
                // 7. Hybrid labels layer
                let hybridLabelsLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
                    maxZoom: 19
                }});
                
                // 8. Terrain layer with contours and elevation data
                let terrainLayer = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
                    maxZoom: 17
                }});
                
                // Create layer groups with updated options
                let baseMaps = {{
                    "OpenStreetMap": openStreetMapLayer,
                    "CartoDB Light": cartoPositronLayer,
                    "CartoDB Voyager": cartoVoyagerLayer,
                    "Satellite (Esri)": satelliteLayer,
                    "Satellite (Google)": googleSatelliteLayer,
                    "Hybrid": L.layerGroup([hybridLayer, hybridLabelsLayer]),
                    "Terrain": terrainLayer
                }};
                
                // Add layer control
                L.control.layers(baseMaps).addTo(map);
                
                // Path drawing variables
                let pathDrawing = false;
                let pathPoints = [];
                let pathMarkers = [];
                let pathLine = null;
                let searchMarker = null;
                let searchTimeout = null;
                let currentSearchResults = [];
                
                // Function to calculate distance between two points
                function calculateDistance(lat1, lon1, lat2, lon2) {{
                    const R = 6371; // Earth's radius in kilometers
                    const dLat = (lat2 - lat1) * Math.PI / 180;
                    const dLon = (lon2 - lon1) * Math.PI / 180;
                    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                             Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                             Math.sin(dLon/2) * Math.sin(dLon/2);
                    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                    return R * c;
                }}
                
                // Function to calculate total path distance
                function calculateTotalDistance(points) {{
                    let totalDistance = 0;
                    for (let i = 1; i < points.length; i++) {{
                        totalDistance += calculateDistance(
                            points[i-1][0], points[i-1][1],
                            points[i][0], points[i][1]
                        );
                    }}
                    return totalDistance;
                }}
                
                // Function to update path status
                function updatePathStatus(status) {{
                    document.getElementById('path-status').textContent = status;
                }}
                
                // Function to clear path markers
                function clearPathMarkers() {{
                    pathMarkers.forEach(marker => map.removeLayer(marker));
                    pathMarkers = [];
                }}
                
                // Function to add path point marker
                function addPathMarker(lat, lon) {{
                    let marker = L.marker([lat, lon], {{
                        icon: L.divIcon({{
                            className: 'path-marker',
                            html: '<div style="background-color: #007bff; width: 8px; height: 8px; border-radius: 50%; border: 2px solid white;"></div>',
                            iconSize: [12, 12]
                        }})
                    }}).addTo(map);
                    pathMarkers.push(marker);
                }}
                
                // Path drawing functions
                function startPathDrawing() {{
                    pathDrawing = true;
                    pathPoints = [];
                    clearPathMarkers();
                    updatePathStatus('Drawing - Click to add path points');
                    document.getElementById('start-path-drawing').disabled = true;
                    document.getElementById('finish-path').disabled = false;
                    document.getElementById('start-path-drawing').classList.add('active');
                    map.getContainer().style.cursor = 'crosshair';
                }}
                
                function startPathDrawing() {{
                    pathDrawing = true;
                    pathPoints = [];
                    clearPathMarkers();
                    updatePathStatus('Drawing - Click to add path points');
                    map.getContainer().style.cursor = 'crosshair';
                }}
                
                function finishPath() {{
                    if (pathPoints.length < 2) {{
                        alert('Need at least 2 points to create a path');
                        return;
                    }}
                    
                    pathDrawing = false;
                    updatePathStatus('Path complete');
                    document.getElementById('start-path-drawing').disabled = false;
                    document.getElementById('finish-path').disabled = true;
                    document.getElementById('start-path-drawing').classList.remove('active');
                    map.getContainer().style.cursor = '';
                    
                    // Send path coordinates to Python
                    if (pywebchannel) {{
                        pywebchannel.receive_path(pathPoints);
                    }}
                    
                    // Calculate and display total distance
                    let totalDistance = calculateTotalDistance(pathPoints);
                    document.getElementById('path-distance').textContent = totalDistance.toFixed(2);
                }}
                
                function clearPath() {{
                    pathDrawing = false;
                    pathPoints = [];
                    clearPathMarkers();
                    updatePathStatus('Ready');
                    document.getElementById('start-path-drawing').disabled = false;
                    document.getElementById('finish-path').disabled = true;
                    document.getElementById('start-path-drawing').classList.remove('active');
                    map.getContainer().style.cursor = '';
                    
                    if (pathLine) {{
                        map.removeLayer(pathLine);
                        pathLine = null;
                    }}
                    
                    document.getElementById('point-count').textContent = '0';
                    document.getElementById('path-distance').textContent = '0';
                }}
                
                function clearPath() {{
                    pathDrawing = false;
                    pathPoints = [];
                    clearPathMarkers();
                    updatePathStatus('Ready');
                    map.getContainer().style.cursor = '';
                    
                    if (pathLine) {{
                        map.removeLayer(pathLine);
                        pathLine = null;
                    }}
                    
                    document.getElementById('point-count').textContent = '0';
                    document.getElementById('path-distance').textContent = '0';
                }}
                
                // Elevation and popup helpers (same as map.html)
                async function getElevation(lat, lng) {{
                    try {{
                        const response = await fetch(`https://api.open-elevation.com/api/v1/lookup?locations=${{lat}},${{lng}}`);
                        const data = await response.json();
                        if (data.results && data.results.length > 0) {{
                            return data.results[0].elevation;
                        }} else {{
                            throw new Error('No elevation data');
                        }}
                    }} catch (e) {{
                        console.error('Elevation fetch error', e);
                        return null;
                    }}
                }}

                function formatCoordinates(lat, lng) {{
                    const latDeg = Math.floor(Math.abs(lat));
                    const latMin = (Math.abs(lat) - latDeg) * 60;
                    const latSec = (latMin - Math.floor(latMin)) * 60;
                    const latDir = lat >= 0 ? 'N' : 'S';
                    const lngDeg = Math.floor(Math.abs(lng));
                    const lngMin = (Math.abs(lng) - lngDeg) * 60;
                    const lngSec = (lngMin - Math.floor(lngMin)) * 60;
                    const lngDir = lng >= 0 ? 'E' : 'W';
                    return {{
                        decimal: `${{lat.toFixed(6)}}, ${{lng.toFixed(6)}}`,
                        dms: `${{latDeg}}°${{Math.floor(latMin)}}'${{latSec.toFixed(2)}}"${{latDir}}, ${{lngDeg}}°${{Math.floor(lngMin)}}'${{lngSec.toFixed(2)}}"${{lngDir}}`
                    }};
                }}

                function createPopupContent(lat, lng, elevation = null) {{
                    const coords = formatCoordinates(lat, lng);
                    let elevationHtml = '';
                    
                    if (elevation !== null) {{
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="label">Elevation:</div>
                                <div class="value">${{elevation.toFixed(1)}} meters (${{(elevation * 3.28084).toFixed(1)}} feet)</div>
                            </div>
                        `;
                    }} else if (elevation === null) {{
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="loading">Loading elevation data...</div>
                            </div>
                        `;
                    }} else {{
                        elevationHtml = `
                            <div class="elevation-info">
                                <div class="error">Elevation data unavailable</div>
                            </div>
                        `;
                    }}
                    
                    return `
                        <div class="coordinate-popup">
                            <div class="label">Decimal Coordinates:</div>
                            <div class="value">${{coords.decimal}}</div>
                            <div class="label">DMS Coordinates:</div>
                            <div class="value">${{coords.dms}}</div>
                            ${{elevationHtml}}
                        </div>
                    `;
                }}

                // Map click handler for path drawing and coordinate display
                map.on('click', async function(e) {{
                    let lat = e.latlng.lat;
                    let lng = e.latlng.lng;
                    
                    if (pathDrawing) {{
                        pathPoints.push([lat, lng]);
                        addPathMarker(lat, lng);
                        document.getElementById('point-count').textContent = pathPoints.length;
                        
                        // Update path line
                        if (pathLine) {{
                            map.removeLayer(pathLine);
                        }}
                        if (pathPoints.length > 1) {{
                            pathLine = L.polyline(pathPoints, {{
                                color: '#007bff',
                                weight: 3,
                                opacity: 0.8
                            }}).addTo(map);
                        }}
                        
                        // Calculate and display current distance
                        let currentDistance = calculateTotalDistance(pathPoints);
                        document.getElementById('path-distance').textContent = currentDistance.toFixed(2);
                        
                        // Send path to Python when we have at least 2 points
                        if (pathPoints.length >= 2 && pywebchannel) {{
                            pywebchannel.receive_path(pathPoints);
                        }}
                    }} else {{
                        // Call Python method for coordinate display when not in drawing mode
                        if (pywebchannel && pywebchannel.receive_map_click) {{
                            pywebchannel.receive_map_click(lat, lng);
                        }} else {{
                            // Fallback: Show coordinate/elevation popup
                            const popup = L.popup()
                                .setLatLng([lat, lng])
                                .setContent(createPopupContent(lat, lng, null))
                                .openOn(map);
                            const elevation = await getElevation(lat, lng);
                            if (elevation !== null) {{
                                popup.setContent(createPopupContent(lat, lng, elevation));
                            }}
                        }}
                    }}
                }});
                
                // Double-click to finish path
                map.on('dblclick', function(e) {{
                    if (pathDrawing && pathPoints.length >= 2) {{
                        finishPath();
                    }}
                }});
                
                // Address Search Functionality
                const searchInput = document.getElementById('search-input');
                const searchButton = document.getElementById('search-button');
                const searchResults = document.getElementById('search-results');
                
                // Function to search for addresses using Nominatim
                async function searchAddress(query) {{
                    try {{
                        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${{encodeURIComponent(query)}}&limit=5`);
                        const data = await response.json();
                        return data;
                    }} catch (error) {{
                        console.error('Error searching address:', error);
                        return [];
                    }}
                }}
                
                // Function to display search results
                function displaySearchResults(results) {{
                    searchResults.innerHTML = '';
                    currentSearchResults = results;
                    
                    if (results.length === 0) {{
                        searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
                        searchResults.style.display = 'block';
                        return;
                    }}
                    
                    results.forEach((result, index) => {{
                        const resultItem = document.createElement('div');
                        resultItem.className = 'search-result-item';
                        resultItem.innerHTML = `
                            <div class="search-result-title">${{result.display_name.split(',')[0]}}</div>
                            <div class="search-result-address">${{result.display_name}}</div>
                        `;
                        
                        resultItem.addEventListener('click', () => {{
                            const lat = parseFloat(result.lat);
                            const lon = parseFloat(result.lon);
                            
                            if (searchMarker) {{
                                map.removeLayer(searchMarker);
                            }}
                            
                            searchMarker = L.marker([lat, lon])
                                .addTo(map)
                                .bindPopup(`<b>Searched Location:</b><br>${{result.display_name}}`)
                                .openPopup();
                            
                            map.setView([lat, lon], 16);
                            searchResults.style.display = 'none';
                            searchInput.value = result.display_name;
                        }});
                        
                        searchResults.appendChild(resultItem);
                    }});
                    
                    searchResults.style.display = 'block';
                }}
                
                // Real-time search as user types
                searchInput.addEventListener('input', (event) => {{
                    const query = event.target.value.trim();
                    
                    if (searchTimeout) {{
                        clearTimeout(searchTimeout);
                    }}
                    
                    if (query.length === 0) {{
                        searchResults.style.display = 'none';
                        return;
                    }}
                    
                    if (query.length < 3) {{
                        searchResults.style.display = 'none';
                        return;
                    }}
                    
                    searchTimeout = setTimeout(async () => {{
                        searchButton.textContent = 'Searching...';
                        searchButton.disabled = true;
                        
                        const results = await searchAddress(query);
                        displaySearchResults(results);
                        
                        searchButton.textContent = 'Search';
                        searchButton.disabled = false;
                    }}, 300);
                }});
                
                // Search button click handler
                searchButton.addEventListener('click', async () => {{
                    const query = searchInput.value.trim();
                    if (query) {{
                        searchButton.textContent = 'Searching...';
                        searchButton.disabled = true;
                        
                        const results = await searchAddress(query);
                        displaySearchResults(results);
                        
                        searchButton.textContent = 'Search';
                        searchButton.disabled = false;
                    }}
                }});
                
                // Click outside search results to hide them
                document.addEventListener('click', (event) => {{
                    if (!event.target.closest('.search-container')) {{
                        searchResults.style.display = 'none';
                    }}
                }});
                
                // Path drawing controls event listeners
                document.addEventListener('DOMContentLoaded', function() {{
                    const startPathBtn = document.getElementById('start-path-drawing');
                    const finishPathBtn = document.getElementById('finish-path');
                    const clearPathBtn = document.getElementById('clear-path');
                    
                    if (startPathBtn) {{
                        startPathBtn.addEventListener('click', startPathDrawing);
                    }}
                    
                    if (finishPathBtn) {{
                        finishPathBtn.addEventListener('click', finishPath);
                    }}
                    
                    if (clearPathBtn) {{
                        clearPathBtn.addEventListener('click', clearPath);
                    }}
                }});
                
                // Fallback event listener attachment
                setTimeout(function() {{
                    const startPathBtn = document.getElementById('start-path-drawing');
                    const finishPathBtn = document.getElementById('finish-path');
                    const clearPathBtn = document.getElementById('clear-path');
                    
                    if (startPathBtn && !startPathBtn.hasAttribute('data-listener-attached')) {{
                        startPathBtn.setAttribute('data-listener-attached', 'true');
                        startPathBtn.addEventListener('click', startPathDrawing);
                    }}
                    
                    if (finishPathBtn && !finishPathBtn.hasAttribute('data-listener-attached')) {{
                        finishPathBtn.setAttribute('data-listener-attached', 'true');
                        finishPathBtn.addEventListener('click', finishPath);
                    }}
                    
                    if (clearPathBtn && !clearPathBtn.hasAttribute('data-listener-attached')) {{
                        clearPathBtn.setAttribute('data-listener-attached', 'true');
                        clearPathBtn.addEventListener('click', clearPath);
                    }}
                }}, 100);
                
                // Initialize status
                updatePathStatus('Ready');
                
                // Make functions globally available for Python bridge
                window.mapFunctions = {{
                    setView: function(lat, lng, zoom) {{
                        map.setView([lat, lng], zoom || 15);
                    }},
                    addPath: function(coordinates) {{
                        if (pathLine) {{
                            map.removeLayer(pathLine);
                        }}
                        pathLine = L.polyline(coordinates, {{
                            color: '#007bff',
                            weight: 3,
                            opacity: 0.8
                        }}).addTo(map);
                        map.fitBounds(pathLine.getBounds());
                        pathPoints = coordinates;
                        document.getElementById('point-count').textContent = pathPoints.length;
                        let totalDistance = calculateTotalDistance(pathPoints);
                        document.getElementById('path-distance').textContent = totalDistance.toFixed(2);
                        updatePathStatus('Path loaded');
                    }},
                    clearPath: clearPath,
                    addMarker: function(lat, lon, popupText) {{
                        let marker = L.marker([lat, lon]).addTo(map);
                        if (popupText) {{
                            marker.bindPopup(popupText).openPopup();
                        }}
                        return marker;
                    }}
                }};
            </script>
        </body>
        </html>
        """

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
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
            margin-bottom: 8px;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
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
        QTextEdit {
            background-color: #2C2C2C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }
        """
        self.setStyleSheet(self.styleSheet() + additional_style)

    def load_kml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open KML Path File", "", "KML Files (*.kml)"
        )
        if not file_path:
            return

        self.file_label.setText(f"Loaded File: {file_path}")

        self.path_coordinates = self.extract_path_coordinates_from_kml(file_path)
        if self.path_coordinates:
            # Clear any existing drawn path on the map
            self.clear_drawn_path()
            
            # Display coordinates in (lat, lon) format in the GUI
            self.coordinates_text.setText("\n".join([f"({lat}, {lon})" for lon, lat, _ in self.path_coordinates]))
            self.generate_flight_button.setEnabled(True)
            self.plot_path_on_map()
        else:
            self.coordinates_text.setText("No valid path found or an error occurred.")
            self.generate_flight_button.setEnabled(False)

    def extract_path_coordinates_from_kml(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            line_elements = root.findall(".//kml:LineString/kml:coordinates", namespace)

            path_coordinates = []
            for element in line_elements:
                raw_coords = element.text.strip()
                for coord in raw_coords.split():
                    lon, lat, alt = map(float, coord.split(","))
                    path_coordinates.append((lon, lat, alt))
            return path_coordinates
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse KML file: {e}")
            return []

    def plot_path_on_map(self):
        """Plots the flight path on the Leaflet map view."""
        if not self.path_coordinates:
            return

        # Generate a JavaScript command to plot the path using Leaflet
        path_coords = [f"[{lat}, {lon}]" for lon, lat, _ in self.path_coordinates]
        js_command = f"""
            if (window.mapFunctions && window.mapFunctions.addPath) {{
                window.mapFunctions.addPath([{", ".join(path_coords)}]);
            }}
        """
        self.map_view.page().runJavaScript(js_command)
    




    def clear_drawn_path(self):
        """Clear any drawn path from the map."""
        js_command = """
            if (window.mapFunctions && window.mapFunctions.clearPath) {
                window.mapFunctions.clearPath();
            }
        """
        self.map_view.page().runJavaScript(js_command)

    def calculate_landing_pattern_offset(self, altitude_meters):
        """Calculates the distance offset for the landing pattern based on altitude and glide slope."""
        glide_slope_angle = 7.4  # Degrees
        return altitude_meters / tan(radians(glide_slope_angle))

    def generate_takeoff_waypoint(self, altitude, terrain_elevation):
        """Generates a takeoff waypoint based on the selected drone type."""
        drone_type = self.drone_type_dropdown.currentText()
        if drone_type == "Quadplane/VTOL Hybrid":
            return {
                "command": 84,  # VTOL_TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }
        elif drone_type == "Fixed-Wing":
            return {
                "command": 22,  # FIXED_WING_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }
        else:
            return {
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }

    def generate_landing_waypoint(self, terrain_elevation):
        """Generates a landing waypoint based on the selected drone type."""
        drone_type = self.drone_type_dropdown.currentText()
        altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters

        if drone_type == "Quadplane/VTOL Hybrid":
            return {
                "command": 85,  # VTOL_LAND
                "doJumpId": 999,
                "frame": 0,
                "params": [0, 0, 0, 0, self.landing_point[0], self.landing_point[1], terrain_elevation],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": 0,
                "AltitudeMode": 3
            }
        elif drone_type == "Fixed-Wing":
            # Calculate the distance offset for the landing pattern
            distance_offset = self.calculate_landing_pattern_offset(altitude_meters)

            # Calculate the approach coordinates based on the distance offset
            approach_lat = self.landing_point[0] + (distance_offset / 111320.0)  # 1 degree ≈ 111,320 meters
            approach_lon = self.landing_point[1] + (distance_offset / (111320.0 * cos(radians(self.landing_point[0]))))

            return {
                "altitudesAreRelative": True,
                "complexItemType": "fwLandingPattern",
                "landCoordinate": [self.landing_point[0], self.landing_point[1], 0],
                "landingApproachCoordinate": [approach_lat, approach_lon, altitude_meters],
                "loiterClockwise": True,
                "loiterRadius": distance_offset,  # Use dynamic distance offset
                "stopTakingPhotos": True,
                "stopVideoPhotos": True,
                "type": "ComplexItem",
                "useLoiterToAlt": True,
                "valueSetIsDistance": False,
                "version": 2
            }
        else:
            return {
                "command": 21,  # LAND
                "doJumpId": 999,
                "frame": 0,
                "params": [0, 0, 0, 0, self.landing_point[0], self.landing_point[1], terrain_elevation],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": 0,
                "AltitudeMode": 3
            }

    def generate_flight_plan(self):
        """Generates the flight plan with waypoints."""
        if not self.path_coordinates:
            self.coordinates_text.setText("No valid path coordinates available.")
            return

        # Get aircraft-aware values
        if self.is_parameters_enabled():
            # Use aircraft parameters for optimized values
            altitude_meters = self.get_aircraft_aware_altitude("linear", 
                self.altitude_input.value() * 0.3048)  # Convert feet to meters
            interval = self.get_aircraft_aware_waypoint_spacing("linear", 50.0)  # Default 50m spacing
        else:
            # Use manual input values
            altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters
            interval = 50.0  # Default spacing

        # Validate and set the takeoff point
        try:
            takeoff_lat, takeoff_lon = map(float, self.takeoff_input.text().split(","))
            self.takeoff_point = (takeoff_lat, takeoff_lon)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid takeoff point coordinates. Please enter as: latitude, longitude.")
            return

        # Validate and set the landing point
        try:
            landing_lat, landing_lon = map(float, self.landing_input.text().split(","))
            self.landing_point = (landing_lat, landing_lon)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid landing point coordinates. Please enter as: latitude, longitude.")
            return

        interpolated_path = self.interpolate_waypoints(self.path_coordinates, interval)

        # Set up progress bar
        total_steps = len(interpolated_path) + 2  # Path points + Takeoff + Landing
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        waypoints = []

        # Takeoff waypoint(s)
        terrain_elevation = self.terrain_query.get_elevation(self.takeoff_point[0], self.takeoff_point[1])
        takeoff_waypoint = self.generate_takeoff_waypoint(altitude_meters, terrain_elevation)
        waypoints.append(takeoff_waypoint)

        self.progress_bar.setValue(1)
        QApplication.processEvents()

        # Intermediate waypoints
        for i, (lon, lat, _) in enumerate(interpolated_path):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            waypoints.append({
                "command": 16,
                "doJumpId": i + 2,
                "frame": 0,
                "params": [0, 0, 0, 0, lat, lon, terrain_elevation + altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude_meters,
                "AltitudeMode": 3
            })
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            QApplication.processEvents()

        # Landing waypoint
        landing_elevation = self.terrain_query.get_elevation(self.landing_point[0], self.landing_point[1])
        landing_waypoint = self.generate_landing_waypoint(landing_elevation)
        waypoints.append(landing_waypoint)
        self.progress_bar.setValue(total_steps)
        QApplication.processEvents()

        # Get aircraft-specific parameters if available
        cruise_speed = 15
        hover_speed = 5
        firmware_type = 12
        vehicle_type = 1 if self.drone_type_dropdown.currentText() == "Fixed-Wing" else 2

        if self.aircraft_param_manager.has_parameters():
            cruise_speed = self.aircraft_param_manager.get_cruise_speed()
            hover_speed = self.aircraft_param_manager.get_hover_speed()
            firmware_type = self.aircraft_param_manager.get_firmware_type()
            vehicle_type = self.aircraft_param_manager.get_vehicle_type()

        flight_plan = {
            "fileType": "Plan",
            "geoFence": {"circles": [], "polygons": [], "version": 2},
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": cruise_speed,
                "hoverSpeed": hover_speed,
                "firmwareType": firmware_type,
                "globalPlanAltitudeMode": 0,
                "items": waypoints,
                "plannedHomePosition": [self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude_meters],
                "vehicleType": vehicle_type,
                "version": 2,
                "aircraftParameters": self.aircraft_param_manager.get_export_parameters()
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

        # Store waypoints for export functionality
        self.waypoints = waypoints
        
        # Enable export button
        self.export_btn.setEnabled(True)

        # Enable toolbar actions
        self.toolbar.enable_actions(True)
        
        # Check for terrain proximity warnings
        proximity_warnings = self.check_terrain_proximity(altitude_meters)
        
        if proximity_warnings:
            self.show_terrain_proximity_warning(proximity_warnings)
        
        self.save_flight_plan(flight_plan)
        self.progress_bar.setVisible(False)

    def save_flight_plan(self, flight_plan):
        # Use new file generation system
        saved_file = self.save_mission_file(flight_plan, "linear_flight")
        if saved_file:
            self.coordinates_text.setText(f"Flight plan generated and saved to:\n{saved_file}")
        else:
            self.coordinates_text.setText("Flight plan generation canceled.")

    def check_terrain_proximity(self, altitude_meters):
        """Check if any waypoint gets too close to terrain (within 50ft/15.24m)"""
        proximity_warnings = []
        warning_threshold = 15.24  # 50 feet in meters
        
        if not hasattr(self, 'waypoints') or not self.waypoints:
            return proximity_warnings
        
        for i, waypoint in enumerate(self.waypoints):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat, lon = waypoint['params'][4], waypoint['params'][5]
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
        if not hasattr(self, 'waypoints') or not self.waypoints:
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
            
            # Get aircraft-aware altitude data
            if self.is_parameters_enabled():
                altitude_meters = self.get_aircraft_aware_altitude("linear", 
                    self.altitude_input.value() * 0.3048)  # Convert feet to meters
            else:
                altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters
            
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
        # Get waypoint data
        waypoint_data = []
        for i, waypoint in enumerate(self.waypoints):
            if 'params' in waypoint and len(waypoint['params']) >= 6:
                lat, lon = waypoint['params'][4], waypoint['params'][5]
                terrain_elevation = self.terrain_query.get_elevation(lat, lon)
                amsl_altitude = terrain_elevation + altitude_meters
                waypoint_data.append({
                    'lat': lat,
                    'lon': lon,
                    'terrain_elevation': terrain_elevation,
                    'amsl_altitude': amsl_altitude,
                    'agl_altitude': altitude_meters,
                    'waypoint_number': i + 1,
                    'command': waypoint.get('command', 'Unknown')
                })
        
        # Generate KML content
        kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Linear Flight Route</name>
    <description>Linear flight route generated by AutoFlightGenerator</description>
    
    <!-- Flight Path Line -->
    <Placemark>
      <name>Flight Path</name>
      <description>Linear flight path with terrain following</description>
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

    def interpolate_waypoints(self, path_coords, interval):
        interpolated_coords = []

        for i in range(len(path_coords) - 1):
            start = (path_coords[i][1], path_coords[i][0])
            end = (path_coords[i + 1][1], path_coords[i + 1][0])
            distance = geodesic(start, end).meters

            interpolated_coords.append(path_coords[i])

            num_intervals = int(distance // interval)
            for j in range(1, num_intervals):
                fraction = j / num_intervals
                interpolated_point = (
                    start[0] + fraction * (end[0] - start[0]),
                    start[1] + fraction * (end[1] - start[1])
                )
                interpolated_coords.append((interpolated_point[1], interpolated_point[0], path_coords[i][2]))

        interpolated_coords.append(path_coords[-1])
        return interpolated_coords

    def start_path_drawing(self):
        """Start path drawing mode."""
        self.drawing_path = True
        self.status_text.setText("Drawing mode activated. Click on the map to add path points.")
        # Trigger JavaScript drawing mode
        self.map_view.page().runJavaScript("startPathDrawing();")

    def clear_path(self):
        """Clear the current path."""
        self.path_coordinates = []
        self.drawing_path = False
        self.status_text.setText("Path cleared. Ready to draw new path.")
        self.generate_flight_button.setEnabled(False)
        self.coordinates_text.setText("")
        self.file_label.setText("No path drawn")
        # Trigger JavaScript clear function
        self.map_view.page().runJavaScript("clearPath();")

    def handle_path_received(self, coordinates):
        """Handle path coordinates received from JavaScript via bridge."""
        print(f"Path received with {len(coordinates)} coordinates")
        # Convert coordinates to the format expected by the existing code
        # JavaScript sends [lat, lng] but existing code expects (lon, lat, alt)
        self.path_coordinates = [(point[1], point[0], 0) for point in coordinates]
        
        if len(coordinates) >= 2:
            # Format coordinates for display
            coord_display = "\n".join([f"Point {i+1}: {lat:.6f}, {lng:.6f}" for i, (lat, lng) in enumerate(coordinates)])
            
            self.status_text.setText(f"Flight path defined with {len(coordinates)} points.\n\nCoordinates:\n{coord_display}")
            self.generate_flight_button.setEnabled(True)
            self.coordinates_text.setText("\n".join([f"({lat}, {lng})" for lat, lng in coordinates]))
            self.file_label.setText(f"Path drawn with {len(coordinates)} waypoints")
        else:
            self.status_text.setText("Invalid path. Need at least 2 points.")

    def handle_map_click(self, lat, lng):
        """Handle map click events with enhanced coordinate and elevation display."""
        # If we're in drawing mode, the JavaScript will handle adding points
        if self.drawing_path:
            return
        
        # The popup is now handled by the JavaScript createPopupContent function
        # No need to show a QMessageBox dialog
        pass

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
        self.takeoff_point = (lat, lng)
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.takeoff_location_label.setText(f"Takeoff: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.takeoff_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Also update the legacy takeoff input field
        self.takeoff_input.setText(f"{lat:.6f},{lng:.6f}")

    def handle_landing_location_selected(self, lat, lng):
        """Handle landing location selection from map."""
        self.landing_point = (lat, lng)
        terrain_elevation = self.terrain_query.get_elevation(lat, lng)
        elevation_feet = terrain_elevation * 3.28084
        
        self.landing_location_label.setText(f"Landing: {lat:.6f}, {lng:.6f} (Elev: {terrain_elevation:.1f}m)")
        self.landing_location_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        # Also update the legacy landing input field
        self.landing_input.setText(f"{lat:.6f},{lng:.6f}")
    
    def clear_waypoints(self):
        """Clear all waypoints and reset the path"""
        self.clear_path()

    def visualize_altitude(self):
        """Displays altitude profile information for the waypoints with AMSL terrain elevation."""
        if not hasattr(self, 'waypoints') or not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        # Get altitude in meters
        altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters
        
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
        plt.title('Linear Flight Route Altitude Profile with Terrain')
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
        
        stats_text = f"""Linear Flight Route Altitude Profile Summary
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    planner = LinearFlightRoute()
    planner.show()
    sys.exit(app.exec())