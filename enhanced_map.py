#!/usr/bin/env python3
"""
Enhanced Map Component with advanced features
"""

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QSlider, QFrame, QToolButton,
                             QButtonGroup, QCheckBox, QSpinBox, QDoubleSpinBox)
from PyQt5.QtCore import QUrl, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWebChannel import QWebChannel

class MapControls(QFrame):
    """Map control panel with zoom, layers, and tools"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Layer selector
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(["OpenStreetMap", "Satellite", "Hybrid", "Terrain"])
        self.layer_combo.setStyleSheet("""
            QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
        """)
        layout.addWidget(QLabel("Layer:"))
        layout.addWidget(self.layer_combo)
        
        # Zoom controls
        zoom_frame = QFrame()
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(0, 0, 0, 0)
        zoom_layout.setSpacing(5)
        
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setFixedSize(30, 30)
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
            }
        """)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(30, 30)
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
            }
        """)
        
        zoom_layout.addWidget(self.zoom_out_btn)
        zoom_layout.addWidget(self.zoom_in_btn)
        layout.addWidget(zoom_frame)
        
        # Fullscreen button
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(30, 30)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
            }
        """)
        layout.addWidget(self.fullscreen_btn)
        
        layout.addStretch()
        
        # Waypoint controls
        self.show_waypoints_cb = QCheckBox("Show Waypoints")
        self.show_waypoints_cb.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #555555;
                background-color: #2C2C2C;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #FFD700;
                background-color: #FFD700;
            }
        """)
        layout.addWidget(self.show_waypoints_cb)
        
        self.show_route_cb = QCheckBox("Show Route")
        self.show_route_cb.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #555555;
                background-color: #2C2C2C;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #FFD700;
                background-color: #FFD700;
            }
        """)
        layout.addWidget(self.show_route_cb)
        
        self.setStyleSheet("""
            QFrame {
                background-color: #2C2C2C;
                border: 1px solid #444444;
                border-radius: 5px;
            }
        """)

class EnhancedMapWidget(QWidget):
    """Enhanced map widget with advanced features"""
    
    # Signals
    waypoint_added = pyqtSignal(float, float, str)  # lat, lng, waypoint_type
    route_updated = pyqtSignal(list)  # list of waypoints
    map_clicked = pyqtSignal(float, float)  # lat, lng
    faa_maps_toggled = pyqtSignal(bool)  # enabled/disabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.waypoints = []
        self.route_polyline = None
        self.setup_ui()
        self.setup_webchannel()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Map controls
        self.controls = MapControls()
        layout.addWidget(self.controls)
        
        # Map view
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        layout.addWidget(self.map_view)
        
        # Connect controls
        self.controls.layer_combo.currentTextChanged.connect(self.change_layer)
        self.controls.zoom_in_btn.clicked.connect(self.zoom_in)
        self.controls.zoom_out_btn.clicked.connect(self.zoom_out)
        self.controls.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.controls.show_waypoints_cb.toggled.connect(self.toggle_waypoints)
        self.controls.show_route_cb.toggled.connect(self.toggle_route)
        
        # Load enhanced map
        self.load_enhanced_map()
        
    def setup_webchannel(self):
        """Setup QWebChannel communication"""
        self.channel = QWebChannel()
        self.map_object = QtCore.QObject()
        
        # Register Python methods
        self.map_object.setStartLocation = self.set_start_location
        self.map_object.setEndLocation = self.set_end_location
        self.map_object.addWaypoint = self.add_waypoint
        self.map_object.removeWaypoint = self.remove_waypoint
        self.map_object.updateRoute = self.update_route
        self.map_object.onMapClick = self.on_map_click
        self.map_object.faaMapsToggled = self.on_faa_maps_toggled
        self.map_object.getFAAMapsSetting = self.get_faa_maps_setting
        self.map_object.getFAAAirspaceInfo = self.get_faa_airspace_info
        self.map_object.checkFlightPathAirspace = self.check_flight_path_airspace
        self.map_object.getElevationData = self.get_elevation_data
        
        
        self.channel.registerObject('mapObject', self.map_object)
        self.map_view.page().setWebChannel(self.channel)
        
    def load_enhanced_map(self):
        """Load the enhanced map HTML"""
        # Try to load the FAA-enabled map first
        faa_map_path = os.path.join(os.path.dirname(__file__), 'enhanced_map_with_faa.html')
        if os.path.exists(faa_map_path):
            map_path = faa_map_path
        else:
            # Fallback to regular enhanced map
            map_path = os.path.join(os.path.dirname(__file__), 'enhanced_map.html')
        self.map_view.setUrl(QUrl.fromLocalFile(map_path))
    
    def load_mapping_map(self):
        """Load the mapping-specific map HTML file"""
        map_file = os.path.join(os.path.dirname(__file__), 'mapping_map.html')
        if os.path.exists(map_file):
            self.map_view.setUrl(QUrl.fromLocalFile(map_file))
        else:
            # Fallback to enhanced map
            self.load_enhanced_map()
    
    def load_structure_scan_map(self):
        """Load the structure scan-specific map HTML file"""
        map_file = os.path.join(os.path.dirname(__file__), 'mapping_map.html')
        if os.path.exists(map_file):
            # Add structure scan parameter to URL
            map_url = QUrl.fromLocalFile(map_file)
            map_url.setQuery("structure_scan=true")
            self.map_view.setUrl(map_url)
        else:
            # Fallback to enhanced map
            self.load_enhanced_map()
        
    def change_layer(self, layer_name):
        """Change map layer"""
        layer_map = {
            "OpenStreetMap": "osm",
            "Satellite": "satellite", 
            "Hybrid": "hybrid",
            "Terrain": "terrain"
        }
        if layer_name in layer_map:
            self.map_view.page().runJavaScript(f"changeLayer('{layer_map[layer_name]}')")
            
    def zoom_in(self):
        """Zoom in on map"""
        self.map_view.page().runJavaScript("map.zoomIn()")
        
    def zoom_out(self):
        """Zoom out on map"""
        self.map_view.page().runJavaScript("map.zoomOut()")
        
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def toggle_waypoints(self, show):
        """Toggle waypoint visibility"""
        self.map_view.page().runJavaScript(f"toggleWaypoints({str(show).lower()})")
        
    def toggle_route(self, show):
        """Toggle route visibility"""
        self.map_view.page().runJavaScript(f"toggleRoute({str(show).lower()})")
        
    def set_start_location(self, lat, lng):
        """Set start location"""
        self.map_view.page().runJavaScript(f"setStartLocation({lat}, {lng})")
        self.waypoint_added.emit(lat, lng, "start")
        
    def set_end_location(self, lat, lng):
        """Set end location"""
        self.map_view.page().runJavaScript(f"setEndLocation({lat}, {lng})")
        self.waypoint_added.emit(lat, lng, "end")
        
    def add_waypoint(self, lat, lng, waypoint_type="waypoint"):
        """Add a waypoint"""
        self.waypoints.append({"lat": lat, "lng": lng, "type": waypoint_type})
        self.map_view.page().runJavaScript(f"addWaypoint({lat}, {lng}, '{waypoint_type}')")
        self.waypoint_added.emit(lat, lng, waypoint_type)
        self.update_route_signal()
        
    def remove_waypoint(self, index):
        """Remove a waypoint"""
        if 0 <= index < len(self.waypoints):
            removed = self.waypoints.pop(index)
            self.map_view.page().runJavaScript(f"removeWaypoint({index})")
            self.update_route_signal()
            
    def update_route(self, waypoints):
        """Update the route with new waypoints"""
        self.waypoints = waypoints
        waypoints_json = str(waypoints).replace("'", '"')
        self.map_view.page().runJavaScript(f"updateRoute({waypoints_json})")
        self.route_updated.emit(waypoints)
        
    def update_route_signal(self):
        """Emit route updated signal"""
        self.route_updated.emit(self.waypoints)
        
    def on_map_click(self, lat, lng):
        """Handle map click"""
        self.map_clicked.emit(lat, lng)
        
    def clear_route(self):
        """Clear all waypoints and route"""
        self.waypoints = []
        self.map_view.page().runJavaScript("clearRoute()")
        self.route_updated.emit([])
        
    def fit_bounds(self):
        """Fit map to show all waypoints"""
        if self.waypoints:
            self.map_view.page().runJavaScript("fitBounds()")
            
    def get_waypoints(self):
        """Get current waypoints"""
        return self.waypoints.copy()
        
    def set_waypoints(self, waypoints):
        """Set waypoints from external source"""
        self.waypoints = waypoints.copy()
        waypoints_json = str(waypoints).replace("'", '"')
        self.map_view.page().runJavaScript(f"setWaypoints({waypoints_json})")
        self.route_updated.emit(waypoints)
    
    def toggle_faa_maps(self, enabled):
        """Toggle FAA UAS Facility Maps"""
        self.map_view.page().runJavaScript(f"toggleFAAMaps({str(enabled).lower()})")
    
    def on_faa_maps_toggled(self, enabled):
        """Handle FAA maps toggle from JavaScript"""
        self.faa_maps_toggled.emit(enabled)
        # Update settings
        from settings_manager import settings_manager
        settings_manager.set_setting("show_faa_maps", enabled)
    
    def get_faa_maps_setting(self):
        """Get current FAA maps setting from settings manager"""
        from settings_manager import settings_manager
        return settings_manager.get_setting("show_faa_maps", False)
    
    def get_faa_airspace_info(self, lat, lng, altitude_ft=400):
        """Get FAA airspace information for given coordinates"""
        try:
            from faa_maps_integration import faa_maps_integration
            return faa_maps_integration.get_faa_airspace_info(lat, lng, altitude_ft)
        except Exception as e:
            print(f"Error getting FAA airspace info: {e}")
            return {
                'airspace_class': 'G',
                'max_altitude_ft': '400 ft',
                'authorization_required': False,
                'restrictions': 'Default airspace rules apply',
                'tfr_active': False,
                'error': str(e)
            }
    
    def check_flight_path_airspace(self, waypoints):
        """Check airspace along flight path"""
        try:
            from faa_maps_integration import faa_maps_integration
            warnings = faa_maps_integration.check_flight_path_airspace(waypoints)
            
            if warnings:
                # Show warnings to user
                warning_text = "Airspace Warnings:\n"
                for warning in warnings:
                    warning_text += f"• {warning['warning']}\n"
                
                # Emit signal with warnings
                self.route_updated.emit(warnings)
                return warnings
            else:
                return []
        except Exception as e:
            print(f"Error checking flight path airspace: {e}")
            return []
    
    def get_elevation_data(self, lat, lng):
        """Get elevation data for given coordinates"""
        try:
            import requests
            url = f"https://api.opentopodata.org/v1/aster30m?locations={lat},{lng}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results') and data['results'][0]:
                elevation = data['results'][0]['elevation']
                return {
                    'elevation_m': round(elevation, 1),
                    'elevation_ft': round(elevation * 3.28084, 1)
                }
            else:
                return {'error': 'No elevation data available'}
        except Exception as e:
            return {'error': f'Elevation data unavailable: {str(e)}'}
    
     