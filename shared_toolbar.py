#!/usr/bin/env python3
"""
Shared Toolbar Component for AutoFlightGenerator
Provides consistent toolbar functionality across all mission planning tools
"""

import os
import sys
import json
import tempfile
import subprocess
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (
    QToolBar, QAction, QMenu, QFileDialog, QMessageBox, QDialog, 
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QFrame,
    QScrollArea, QGroupBox, QCheckBox, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QPixmap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# Population density tool removed - not used in main application


class TutorialDialog(QDialog):
    """Dialog for displaying tutorials and help content"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VERSATILE UAS Flight Generator Tutorials")
        self.setGeometry(200, 200, 800, 600)
        self.setup_ui()
        self.load_tutorials()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create tab widget for different tutorial categories
        self.tab_widget = QTabWidget()
        
        # Delivery Route Tutorial Tab
        self.delivery_tab = QWidget()
        self.setup_delivery_tutorial()
        self.tab_widget.addTab(self.delivery_tab, "Delivery Route")
        
        # Security Route Tutorial Tab
        self.security_tab = QWidget()
        self.setup_security_tutorial()
        self.tab_widget.addTab(self.security_tab, "Security Route")
        
        # A-to-B Mission Tutorial Tab
        self.atob_tab = QWidget()
        self.setup_atob_tutorial()
        self.tab_widget.addTab(self.atob_tab, "A-to-B Mission")
        
        # Linear Flight Tutorial Tab
        self.linear_tab = QWidget()
        self.setup_linear_tutorial()
        self.tab_widget.addTab(self.linear_tab, "Linear Flight")
        
        # Tower Inspection Tutorial Tab
        self.tower_tab = QWidget()
        self.setup_tower_tutorial()
        self.tab_widget.addTab(self.tower_tab, "Tower Inspection")
        
        # General Features Tutorial Tab
        self.general_tab = QWidget()
        self.setup_general_tutorial()
        self.tab_widget.addTab(self.general_tab, "General Features")
        
        layout.addWidget(self.tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def setup_delivery_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Delivery Route Planner Tutorial</h2>
        
        <h3>Getting Started</h3>
        <p>The Delivery Route Planner allows you to create flight plans for delivery missions with multiple waypoints.</p>
        
        <h3>Step-by-Step Guide</h3>
        <ol>
            <li><strong>Set Start Location:</strong> Click on the map to set your takeoff point</li>
            <li><strong>Add Delivery Points:</strong> Click "Add Delivery Point" to add delivery locations</li>
            <li><strong>Configure Settings:</strong> Set altitude, speed, and other parameters</li>
            <li><strong>Generate Plan:</strong> Click "Generate Flight Plan" to create your mission</li>
        </ol>
        
        <h3>Key Features</h3>
        <ul>
            <li><strong>Terrain Following:</strong> Automatically adjusts altitude based on terrain elevation</li>
            <li><strong>Safety Warnings:</strong> Alerts you if flight path gets too close to terrain</li>
            <li><strong>Export Options:</strong> Export to KML/KMZ for use in other mapping software</li>
            <li><strong>Altitude Visualization:</strong> View detailed altitude profiles with terrain data</li>
        </ul>
        
        <h3>Tips</h3>
        <ul>
            <li>Use the altitude visualization to ensure safe clearance from terrain</li>
            <li>Export your flight plan to share with team members</li>
            <li>Check terrain proximity warnings before flying</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.delivery_tab.setLayout(layout)
        
    def setup_security_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Security Route Planner Tutorial</h2>
        
        <h3>Getting Started</h3>
        <p>The Security Route Planner creates patrol routes for security and surveillance missions.</p>
        
        <h3>Step-by-Step Guide</h3>
        <ol>
            <li><strong>Load Geofence:</strong> Load a KML file to define your patrol area</li>
            <li><strong>Set Takeoff Point:</strong> Click on the map to set your takeoff location</li>
            <li><strong>Choose Route Type:</strong> Select between Random or Perimeter routes</li>
            <li><strong>Configure Parameters:</strong> Set altitude, number of waypoints, and vehicle type</li>
            <li><strong>Generate Plan:</strong> Create your security patrol mission</li>
        </ol>
        
        <h3>Route Types</h3>
        <ul>
            <li><strong>Random Route:</strong> Creates random waypoints within the geofence for thorough coverage</li>
            <li><strong>Perimeter Route:</strong> Creates waypoints along the boundary for perimeter patrol</li>
        </ul>
        
        <h3>Key Features</h3>
        <ul>
            <li><strong>Geofence Support:</strong> Import KML files to define patrol areas</li>
            <li><strong>Vehicle Types:</strong> Support for Multicopter, Fixed-Wing, and VTOL aircraft</li>
            <li><strong>Terrain Awareness:</strong> Automatic terrain following and safety checks</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.security_tab.setLayout(layout)
        
    def setup_atob_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>A-to-B Mission Planner Tutorial</h2>
        
        <h3>Getting Started</h3>
        <p>The A-to-B Mission Planner creates simple point-to-point flight plans.</p>
        
        <h3>Step-by-Step Guide</h3>
        <ol>
            <li><strong>Choose Input Method:</strong> Select manual entry or KML file</li>
            <li><strong>Set Coordinates:</strong> Enter start and end coordinates</li>
            <li><strong>Configure Aircraft:</strong> Select your aircraft type</li>
            <li><strong>Set Parameters:</strong> Configure altitude, interval, and geofence</li>
            <li><strong>Generate Plan:</strong> Create your A-to-B mission</li>
        </ol>
        
        <h3>Input Methods</h3>
        <ul>
            <li><strong>Manual Entry:</strong> Enter coordinates directly</li>
            <li><strong>KML File:</strong> Load a KML path file for complex routes</li>
        </ul>
        
        <h3>Key Features</h3>
        <ul>
            <li><strong>Multiple Aircraft Support:</strong> Multicopter, Fixed-Wing, and VTOL</li>
            <li><strong>Terrain Following:</strong> Automatic altitude adjustment</li>
            <li><strong>Geofence Generation:</strong> Automatic safety boundary creation</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.atob_tab.setLayout(layout)
        
    def setup_linear_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Linear Flight Route Tutorial</h2>
        
        <h3>Getting Started</h3>
        <p>The Linear Flight Route Planner creates flight plans for linear survey missions.</p>
        
        <h3>Step-by-Step Guide</h3>
        <ol>
            <li><strong>Load Path File:</strong> Load a KML file with your survey path</li>
            <li><strong>Set Takeoff/Landing:</strong> Define takeoff and landing points</li>
            <li><strong>Configure Aircraft:</strong> Select your aircraft type</li>
            <li><strong>Set Parameters:</strong> Configure altitude and waypoint interval</li>
            <li><strong>Generate Plan:</strong> Create your linear survey mission</li>
        </ol>
        
        <h3>Use Cases</h3>
        <ul>
            <li><strong>Pipeline Inspection:</strong> Follow linear infrastructure</li>
            <li><strong>Power Line Survey:</strong> Survey electrical transmission lines</li>
            <li><strong>Road/Railway Inspection:</strong> Linear transportation infrastructure</li>
        </ul>
        
        <h3>Key Features</h3>
        <ul>
            <li><strong>Path Interpolation:</strong> Automatically creates waypoints along your path</li>
            <li><strong>Terrain Following:</strong> Maintains safe altitude above terrain</li>
            <li><strong>Multiple Aircraft Support:</strong> Optimized for different vehicle types</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.linear_tab.setLayout(layout)
        
    def setup_tower_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>Tower Inspection Tutorial</h2>
        
        <h3>Getting Started</h3>
        <p>The Tower Inspection Planner creates specialized flight plans for tower inspection missions.</p>
        
        <h3>Step-by-Step Guide</h3>
        <ol>
            <li><strong>Set Takeoff Point:</strong> Click on the map to set your takeoff location</li>
            <li><strong>Set Tower Location:</strong> Click on the map to set the tower position</li>
            <li><strong>Configure Offset:</strong> Set the inspection distance from the tower</li>
            <li><strong>Generate Plan:</strong> Create your tower inspection mission</li>
        </ol>
        
        <h3>Inspection Pattern</h3>
        <p>The planner creates a systematic inspection pattern around the tower:</p>
        <ul>
            <li>Approach the tower at a safe distance</li>
            <li>Circle the tower at multiple altitudes</li>
            <li>Return to takeoff point for landing</li>
        </ul>
        
        <h3>Key Features</h3>
        <ul>
            <li><strong>Safety Distance:</strong> Maintains safe distance from tower</li>
            <li><strong>Multiple Altitudes:</strong> Inspects tower at different heights</li>
            <li><strong>Automatic Pattern:</strong> Creates optimal inspection route</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.tower_tab.setLayout(layout)
        
    def setup_general_tutorial(self):
        layout = QVBoxLayout()
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setHtml("""
        <h2>General Features Tutorial</h2>
        
        <h3>Toolbar Features</h3>
        
        <h4>Altitude Visualizer</h4>
        <p>Click the altitude visualization button to see a detailed profile of your flight path:</p>
        <ul>
            <li><strong>Terrain Elevation:</strong> Green line showing ground elevation</li>
            <li><strong>AMSL Altitude:</strong> Blue line showing absolute altitude above sea level</li>
            <li><strong>AGL Altitude:</strong> Red dashed line showing height above ground</li>
            <li><strong>Flight Corridor:</strong> Blue shaded area showing safe flight zone</li>
        </ul>
        
        <h4>KML/KMZ Export</h4>
        <p>Export your flight plan for use in other mapping software:</p>
        <ul>
            <li><strong>Complete Flight Path:</strong> Full route with all waypoints</li>
            <li><strong>Waypoint Markers:</strong> Individual markers for each waypoint</li>
            <li><strong>Takeoff/Landing Points:</strong> Special markers for mission start/end</li>
            <li><strong>Terrain Data:</strong> Includes elevation information</li>
        </ul>
        
        <h4>Safety Features</h4>
        <ul>
            <li><strong>Terrain Proximity Warnings:</strong> Alerts when flight path gets within 50ft of terrain</li>
            <li><strong>Automatic Safety Checks:</strong> Validates flight plan for safety</li>
            <li><strong>Real-time Monitoring:</strong> Continuous safety assessment</li>
        </ul>
        
        <h3>Tips for Best Results</h3>
        <ul>
            <li>Always check the altitude visualization before flying</li>
            <li>Export your flight plan to share with team members</li>
            <li>Pay attention to terrain proximity warnings</li>
            <li>Use the settings to customize your experience</li>
        </ul>
        """)
        
        layout.addWidget(content)
        self.general_tab.setLayout(layout)
        
    def load_tutorials(self):
        """Load tutorial content from files if available"""
        # This could be extended to load tutorials from external files
        pass


class FilesDialog(QDialog):
    """Dialog for managing saved flight plan files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Flight Plan Files")
        self.setGeometry(200, 200, 600, 400)
        self.setup_ui()
        self.load_files()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # File list
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.open_file)
        layout.addWidget(QLabel("Saved Flight Plans:"))
        layout.addWidget(self.file_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_btn = QPushButton("Open Selected")
        open_btn.clicked.connect(self.open_selected_file)
        button_layout.addWidget(open_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_files)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def load_files(self):
        """Load saved flight plan files"""
        self.file_list.clear()
        
        # Look for .plan files in common directories
        search_dirs = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            os.getcwd()
        ]
        
        for directory in search_dirs:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith('.plan'):
                        item = QListWidgetItem(f"{file} - {directory}")
                        item.setData(Qt.UserRole, os.path.join(directory, file))
                        self.file_list.addItem(item)
                        
    def open_selected_file(self):
        """Open the selected file"""
        current_item = self.file_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            self.open_file_path(file_path)
            
    def open_file(self, item):
        """Open file when double-clicked"""
        file_path = item.data(Qt.UserRole)
        self.open_file_path(file_path)
        
    def open_file_path(self, file_path):
        """Open a specific file path"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")


class SettingsDialog(QDialog):
    """Dialog for application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 500, 400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create tabs for different settings categories
        tab_widget = QTabWidget()
        
        # General Settings Tab
        general_tab = QWidget()
        general_layout = QVBoxLayout()
        
        # Unit System
        unit_group = QGroupBox("Unit System")
        unit_layout = QVBoxLayout()
        
        self.metric_checkbox = QCheckBox("Use Metric Units (Meters)")
        self.imperial_checkbox = QCheckBox("Use Imperial Units (Feet)")
        self.metric_checkbox.setChecked(True)
        
        unit_layout.addWidget(self.metric_checkbox)
        unit_layout.addWidget(self.imperial_checkbox)
        unit_group.setLayout(unit_layout)
        general_layout.addWidget(unit_group)
        
        # Default Values
        defaults_group = QGroupBox("Default Values")
        defaults_layout = QVBoxLayout()
        
        defaults_layout.addWidget(QLabel("Default Altitude:"))
        self.default_altitude = QSpinBox()
        self.default_altitude.setRange(1, 10000)
        self.default_altitude.setValue(100)
        defaults_layout.addWidget(self.default_altitude)
        
        defaults_layout.addWidget(QLabel("Default Waypoint Interval:"))
        self.default_interval = QSpinBox()
        self.default_interval.setRange(1, 1000)
        self.default_interval.setValue(50)
        defaults_layout.addWidget(self.default_interval)
        
        defaults_group.setLayout(defaults_layout)
        general_layout.addWidget(defaults_group)
        
        general_tab.setLayout(general_layout)
        tab_widget.addTab(general_tab, "General")
        
        # Safety Settings Tab
        safety_tab = QWidget()
        safety_layout = QVBoxLayout()
        
        safety_group = QGroupBox("Safety Settings")
        safety_group_layout = QVBoxLayout()
        
        safety_group_layout.addWidget(QLabel("Terrain Proximity Warning Threshold:"))
        self.warning_threshold = QSpinBox()
        self.warning_threshold.setRange(1, 100)
        self.warning_threshold.setValue(50)
        self.warning_threshold.setSuffix(" feet")
        safety_group_layout.addWidget(self.warning_threshold)
        
        self.enable_warnings = QCheckBox("Enable Terrain Proximity Warnings")
        self.enable_warnings.setChecked(True)
        safety_group_layout.addWidget(self.enable_warnings)
        
        safety_group.setLayout(safety_group_layout)
        safety_layout.addWidget(safety_group)
        
        safety_tab.setLayout(safety_layout)
        tab_widget.addTab(safety_tab, "Safety")
        
        # Export Settings Tab
        export_tab = QWidget()
        export_layout = QVBoxLayout()
        
        export_group = QGroupBox("Export Settings")
        export_group_layout = QVBoxLayout()
        
        self.include_terrain = QCheckBox("Include Terrain Data in Exports")
        self.include_terrain.setChecked(True)
        export_group_layout.addWidget(self.include_terrain)
        
        self.include_waypoints = QCheckBox("Include Waypoint Markers")
        self.include_waypoints.setChecked(True)
        export_group_layout.addWidget(self.include_waypoints)
        
        self.include_takeoff_landing = QCheckBox("Include Takeoff/Landing Points")
        self.include_takeoff_landing.setChecked(True)
        export_group_layout.addWidget(self.include_takeoff_landing)
        
        export_group.setLayout(export_group_layout)
        export_layout.addWidget(export_group)
        
        export_tab.setLayout(export_layout)
        tab_widget.addTab(export_tab, "Export")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def save_settings(self):
        """Save the current settings"""
        # This would save to a settings file
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.close()


class SharedToolBar(QToolBar):
    """Shared toolbar component for all mission planning tools"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_toolbar()
        self.apply_toolbar_theme()
        
    def apply_toolbar_theme(self):
        """Apply dark theme styling to the toolbar"""
        self.setStyleSheet("""
            QToolBar {
                background-color: #3C3C3C;
                border: 1px solid #555555;
                spacing: 5px;
                padding: 5px;
            }
            QToolBar QToolButton {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QToolBar QToolButton:hover {
                background-color: #4C4C4C;
                border-color: #666666;
            }
            QToolBar QToolButton:pressed {
                background-color: #2C2C2C;
            }
            QToolBar QToolButton:disabled {
                background-color: #2C2C2C;
                color: #888888;
                border-color: #444444;
            }
            QToolBar::separator {
                background-color: #555555;
                width: 1px;
                margin: 5px 2px;
            }
        """)
        
    def setup_toolbar(self):
        """Setup the toolbar with all actions"""
        
        # Altitude Visualizer Action
        self.altitude_action = QAction("📊 Altitude Visualizer", self)
        self.altitude_action.setToolTip("View altitude profile with terrain data")
        self.altitude_action.triggered.connect(self.show_altitude_visualizer)
        self.addAction(self.altitude_action)
        
        # KML/KMZ Export Action
        self.export_action = QAction("📁 Export KML/KMZ", self)
        self.export_action.setToolTip("Export flight path to KML/KMZ format")
        self.export_action.triggered.connect(self.export_flight_path)
        self.addAction(self.export_action)
        
        self.addSeparator()
        
        # Tutorials Action
        self.tutorials_action = QAction("📚 Tutorials", self)
        self.tutorials_action.setToolTip("View tutorials and help")
        self.tutorials_action.triggered.connect(self.show_tutorials)
        self.addAction(self.tutorials_action)
        
        # Files Action
        self.files_action = QAction("📂 Files", self)
        self.files_action.setToolTip("Manage saved flight plan files")
        self.files_action.triggered.connect(self.show_files)
        self.addAction(self.files_action)
        
        # Settings Action
        self.settings_action = QAction("⚙️ Settings", self)
        self.settings_action.setToolTip("Application settings")
        self.settings_action.triggered.connect(self.show_settings)
        self.addAction(self.settings_action)
        
        # Population density functionality removed - not used in main application
        
    def show_altitude_visualizer(self):
        """Show altitude visualizer if parent has the method"""
        if hasattr(self.parent, 'visualize_altitude'):
            self.parent.visualize_altitude()
        else:
            QMessageBox.information(self, "Info", "Altitude visualizer not available for this tool.")
            
    def export_flight_path(self):
        """Export flight path if parent has the method"""
        if hasattr(self.parent, 'export_flight_path'):
            self.parent.export_flight_path()
        else:
            QMessageBox.information(self, "Info", "Export functionality not available for this tool.")
            
    def show_tutorials(self):
        """Show tutorials dialog"""
        dialog = TutorialDialog(self)
        dialog.exec_()
        
    def show_files(self):
        """Show files dialog"""
        dialog = FilesDialog(self)
        dialog.exec_()
        
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec_()
        
    # Population density method removed - not used in main application
            
    def enable_actions(self, has_waypoints=False):
        """Enable/disable actions based on available data"""
        self.altitude_action.setEnabled(has_waypoints)
        self.export_action.setEnabled(has_waypoints)
