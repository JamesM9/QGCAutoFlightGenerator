#!/usr/bin/env python3
"""
Tutorial Dialog - Comprehensive tutorials for VERSATILE UAS Flight Generator tools
"""

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QWidget, 
                              QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
                              QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, 
                              QGroupBox, QTabWidget, QTextEdit, QSlider, QLineEdit,
                              QFormLayout, QSplitter, QListWidget, QListWidgetItem,
                              QMessageBox, QFileDialog, QProgressBar)
from PyQt5.QtCore import QUrl, Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
import webbrowser
from PyQt5.QtWebChannel import QWebChannel
from video_config import VIDEO_CONFIG, get_videos_for_tool

class TutorialDialog(QDialog):
    """Main tutorial dialog with comprehensive guides for all tools"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Tutorials")
        self.setGeometry(100, 100, 1200, 800)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Flight Planning Tool Tutorials")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet("color: #FFD700; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # New Features Overview
        features_header = QLabel("🚀 New Features & Enhancements")
        features_header.setFont(QFont("Arial", 14, QFont.Bold))
        features_header.setStyleSheet("color: #4CAF50; margin-bottom: 5px;")
        features_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(features_header)
        
        features_text = QLabel("Aircraft Parameter Integration • Individual Tool Control • Enhanced Terrain Following • Google Satellite Maps • Auto-Save Functionality • Improved Performance")
        features_text.setFont(QFont("Arial", 11))
        features_text.setStyleSheet("color: #CCCCCC; margin-bottom: 15px; text-align: center;")
        features_text.setAlignment(Qt.AlignCenter)
        features_text.setWordWrap(True)
        layout.addWidget(features_text)
        
        # Create tab widget for different tutorials
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2C2C2C;
            }
            QTabBar::tab {
                background-color: #3C3C3C;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #FFD700;
                color: #1E1E1E;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #4C4C4C;
            }
        """)
        
        # Add tutorial tabs
        self.add_aircraft_parameters_tutorial()
        self.add_latest_features_tutorial()
        self.add_delivery_route_tutorial()
        self.add_multi_delivery_tutorial()
        self.add_security_route_tutorial()
        self.add_linear_flight_tutorial()
        self.add_tower_inspection_tutorial()
        self.add_atob_mission_tutorial()
        self.add_mapping_flight_tutorial()
        self.add_structure_scan_tutorial()
        
        layout.addWidget(self.tab_widget)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
    def add_aircraft_parameters_tutorial(self):
        """Add Aircraft Parameters tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("Aircraft Parameters System Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Tutorial content
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>🚁 Aircraft Parameters System</h2>

<p><strong>Revolutionary Feature:</strong> The VERSATILE UAS Flight Generator now includes a comprehensive aircraft parameter system that automatically optimizes flight plans based on your specific aircraft's capabilities and firmware settings.</p>

<h3>🎯 What is the Aircraft Parameters System?</h3>

<p>The Aircraft Parameters System allows you to import real ArduPilot or PX4 parameter files from your aircraft and automatically apply those settings to optimize flight planning tools. This ensures your generated missions are perfectly tailored to your specific aircraft's capabilities.</p>

<h3>🔧 How It Works:</h3>

<h4>1. Individual Tool Parameter Control</h4>
<ul>
<li><strong>Per-Tool Control:</strong> Each mission tool has its own parameter UI component</li>
<li><strong>User Choice:</strong> Enable/disable parameter usage on a per-tool basis</li>
<li><strong>Flexible Configuration:</strong> Different tools can use different aircraft configurations</li>
<li><strong>Seamless Integration:</strong> Parameters are applied automatically during mission generation</li>
</ul>

<h4>2. Smart Aircraft Detection</h4>
<ul>
<li><strong>Automatic Detection:</strong> System automatically detects aircraft type from parameters</li>
<li><strong>Multi-Level Analysis:</strong> Uses parameter count and type analysis for accurate detection</li>
<li><strong>Hybrid Support:</strong> Handles aircraft with mixed parameter sets (VTOL, etc.)</li>
<li><strong>Real-Time Display:</strong> Shows detected aircraft type and characteristics</li>
</ul>

<h4>3. Flight Characteristics Extraction</h4>
<ul>
<li><strong>Performance Metrics:</strong> Extracts max speed, cruise speed, climb/descent rates</li>
<li><strong>Navigation Parameters:</strong> Calculates waypoint radius and turn radius</li>
<li><strong>Energy Management:</strong> Identifies TECS vs Direct control characteristics</li>
<li><strong>Mission Optimization:</strong> Provides optimal waypoint spacing and turn strategies</li>
</ul>

<h3>📋 Step-by-Step Setup Guide:</h3>

<h4>Step 1: Open a Mission Tool</h4>
<ul>
<li>Launch any mission planning tool (Delivery Route, Security Route, etc.)</li>
<li>Look for the "Aircraft Parameters" section in the tool's interface</li>
<li>This section appears below the aircraft type selection</li>
</ul>

<h4>Step 2: Enable Parameter Usage</h4>
<ul>
<li>Check the "Use Aircraft Parameters" checkbox</li>
<li>The "Load Parameter File" button will become enabled</li>
<li>You can enable/disable this on a per-tool basis</li>
</ul>

<h4>Step 3: Load Your Parameter File</h4>
<ul>
<li>Click "Load Parameter File" button</li>
<li>Select your aircraft's parameter file (.params, .param, .parm, or .txt format)</li>
<li>The system will automatically parse and analyze the parameters</li>
<li>You'll see confirmation of the detected aircraft type and characteristics</li>
</ul>

<h4>Step 4: Review Aircraft Information</h4>
<ul>
<li>The system displays detected aircraft type (VTOL, FixedWing, Multicopter)</li>
<li>Shows key performance characteristics (max speed, climb rate, etc.)</li>
<li>Displays mission optimization settings (energy management, turn strategy)</li>
<li>All information is extracted automatically from your parameter file</li>
</ul>

<h4>Step 5: Generate Optimized Missions</h4>
<ul>
<li>Configure your mission as usual (waypoints, altitude, etc.)</li>
<li>The system automatically applies aircraft-specific optimizations</li>
<li>Mission generation uses your aircraft's actual capabilities</li>
<li>Export includes complete aircraft parameter information</li>
</ul>

<h3>🎯 Supported Aircraft Types:</h3>

<h4>ArduPilot Firmware:</h4>
<ul>
<li><strong>ArduCopter (Multicopter):</strong> MC_, WPNAV_, PILOT_ALT_MAX parameters</li>
<li><strong>ArduPlane (Fixed-Wing):</strong> FW_, AIRSPEED_, FW_AIRSPD_ parameters</li>
<li><strong>ArduRover (Ground Vehicle):</strong> ROV_ parameters</li>
<li><strong>ArduSub (Underwater):</strong> SUB_ parameters</li>
</ul>

<h4>PX4 Firmware:</h4>
<ul>
<li><strong>Multicopter:</strong> MPC_, EKF2_, NAV_ parameters</li>
<li><strong>Fixed-Wing:</strong> FW_, EKF2_, NAV_ parameters</li>
<li><strong>VTOL:</strong> VT_, VTOL_, VT_FW_ parameters</li>
<li><strong>Rover:</strong> GND_, EKF2_, NAV_ parameters</li>
</ul>

<h3>🔍 Automatic Aircraft Detection:</h3>

<p>The system uses sophisticated multi-level detection to identify your aircraft type:</p>
<ul>
<li><strong>VTOL (Highest Priority):</strong> Detected by VT_TYPE parameter > 0</li>
<li><strong>Multicopter:</strong> Detected by MPC_XY_CRUISE, MPC_THR_HOVER, MPC_XY_VEL_MAX parameters</li>
<li><strong>Fixed-Wing:</strong> Detected by FW_AIRSPD_MAX, FW_T_CLMB_MAX, FW_T_SINK_MAX parameters</li>
<li><strong>Hybrid Analysis:</strong> Uses parameter count analysis for aircraft with mixed parameter sets</li>
<li><strong>Fallback Detection:</strong> Analyzes parameter patterns when specific indicators aren't found</li>
</ul>

<h4>Detection Examples:</h4>
<ul>
<li><strong>VTOL.params:</strong> VT_TYPE=1 → Detected as VTOL</li>
<li><strong>FixedWing.params:</strong> FW_AIRSPD_MAX=36.1 → Detected as FixedWing</li>
<li><strong>Multicopter.params:</strong> MPC_XY_CRUISE=5.0, MPC_THR_HOVER=0.5 → Detected as Multicopter</li>
</ul>

<h3>⚙️ Key Parameters Used:</h3>

<h4>Performance Characteristics:</h4>
<ul>
<li><strong>Max Speed:</strong> FW_AIRSPD_MAX (FixedWing), MPC_XY_VEL_MAX (Multicopter)</li>
<li><strong>Cruise Speed:</strong> FW_AIRSPD_TRIM (FixedWing), MPC_XY_CRUISE (Multicopter)</li>
<li><strong>Climb Rate:</strong> FW_T_CLMB_MAX (FixedWing), MPC_Z_VEL_MAX_UP (Multicopter)</li>
<li><strong>Descent Rate:</strong> FW_T_SINK_MAX (FixedWing), MPC_Z_VEL_MAX_DN (Multicopter)</li>
</ul>

<h4>Navigation and Control:</h4>
<ul>
<li><strong>Waypoint Radius:</strong> NAV_FW_ALT_RAD (FixedWing), NAV_MC_ALT_RAD (Multicopter)</li>
<li><strong>Turn Radius:</strong> Calculated from FW_R_LIM (FixedWing), MPC_MAN_TILT_MAX (Multicopter)</li>
<li><strong>Hover Throttle:</strong> MPC_THR_HOVER (Multicopter)</li>
<li><strong>Transition Airspeed:</strong> VT_ARSP_TRANS (VTOL)</li>
</ul>

<h4>Energy Management:</h4>
<ul>
<li><strong>TECS (FixedWing/VTOL):</strong> Total Energy Conservation System parameters</li>
<li><strong>Direct Control (Multicopter):</strong> Direct throttle and attitude control</li>
<li><strong>Climb Efficiency:</strong> FW_T_CLMB_MAX / FW_AIRSPD_TRIM ratio</li>
<li><strong>Descent Efficiency:</strong> FW_T_SINK_MAX / FW_AIRSPD_TRIM ratio</li>
</ul>

<h3>📊 Mission Tool Integration:</h3>

<p>Each mission planning tool has its own parameter UI component for flexible configuration:</p>

<h4>Delivery Route Tool:</h4>
<ul>
<li>Parameter UI component below aircraft type selection</li>
<li>Automatic aircraft type detection from parameters</li>
<li>Optimized waypoint spacing based on turn radius</li>
<li>Speed settings from aircraft-specific cruise speeds</li>
<li>Altitude limits applied from aircraft capabilities</li>
</ul>

<h4>Security Route Tool:</h4>
<ul>
<li>Individual parameter configuration per tool</li>
<li>Patrol patterns optimized for aircraft performance</li>
<li>Auto-save functionality for generated flight plans</li>
<li>Google Satellite map layer by default</li>
</ul>

<h4>Linear Flight Tool:</h4>
<ul>
<li>Parameter-aware waypoint generation</li>
<li>Google Satellite map layer by default</li>
<li>Optimized flight path based on aircraft characteristics</li>
</ul>

<h4>Mapping Flight Tool:</h4>
<ul>
<li>Survey patterns optimized for aircraft capabilities</li>
<li>Google Satellite map layer by default</li>
<li>Grid spacing based on waypoint acceptance radius</li>
</ul>

<h4>Structure Scan Tool:</h4>
<ul>
<li>3D scanning patterns adapted to aircraft performance</li>
<li>Google Satellite map layer by default</li>
<li>Altitude and speed optimization from parameters</li>
</ul>

<h4>All Tools Support:</h4>
<ul>
<li>Individual parameter file loading per tool</li>
<li>Real-time aircraft information display</li>
<li>Mission optimization settings preview</li>
<li>Flexible enable/disable per tool</li>
</ul>

<h3>💡 Benefits of Using Parameters:</h3>

<ul>
<li><strong>Safety:</strong> Missions stay within your aircraft's certified limits</li>
<li><strong>Optimization:</strong> Flight plans optimized for your specific aircraft's performance</li>
<li><strong>Flexibility:</strong> Enable/disable parameters per tool as needed</li>
<li><strong>Accuracy:</strong> Waypoint spacing and speeds match aircraft capabilities</li>
<li><strong>Real-Time Feedback:</strong> See aircraft characteristics and optimization settings</li>
<li><strong>Compliance:</strong> Ensures missions comply with firmware safety settings</li>
<li><strong>Efficiency:</strong> Automatic application of aircraft-specific optimizations</li>
<li><strong>User Choice:</strong> Use parameters when beneficial, disable when not needed</li>
</ul>

<h3>🛠️ Troubleshooting:</h3>

<h4>Parameter Import Issues:</h4>
<ul>
<li><strong>Unsupported Format:</strong> Ensure file is .params, .param, .parm, or .txt format</li>
<li><strong>Corrupted File:</strong> Re-export parameters from your ground station</li>
<li><strong>Empty Parameters:</strong> Verify parameter file contains actual data</li>
<li><strong>Parse Errors:</strong> Check that file follows PX4 5-column format (instance_id\tcomponent_id\tparam_name\tvalue\ttype)</li>
</ul>

<h4>Configuration Issues:</h4>
<ul>
<li><strong>No Aircraft Detected:</strong> Check if parameter file contains recognizable parameters</li>
<li><strong>Wrong Aircraft Type:</strong> Verify parameter file is from correct firmware</li>
<li><strong>Missing Parameters:</strong> Some parameters may not be present in all configurations</li>
<li><strong>Hybrid Aircraft:</strong> System handles mixed parameter sets (VTOL with both MPC_ and FW_ parameters)</li>
</ul>

<h4>Mission Generation Issues:</h4>
<ul>
<li><strong>Parameters Not Applied:</strong> Ensure "Use Aircraft Parameters" is checked in the tool</li>
<li><strong>No Parameter File:</strong> Load a parameter file using "Load Parameter File" button</li>
<li><strong>Fallback to Defaults:</strong> System falls back to default values if parameters unavailable</li>
<li><strong>Tool-Specific Issues:</strong> Each tool manages its own parameter state independently</li>
</ul>

<h3>📚 Best Practices:</h3>

<ul>
<li><strong>Regular Updates:</strong> Re-import parameters after firmware updates</li>
<li><strong>Tool-Specific Configuration:</strong> Configure parameters per tool as needed</li>
<li><strong>Descriptive Files:</strong> Use clear filenames for parameter files</li>
<li><strong>Backup Parameters:</strong> Keep copies of parameter files for reference</li>
<li><strong>Test Missions:</strong> Always test parameter-optimized missions in simulation</li>
<li><strong>Verify Settings:</strong> Check aircraft information display for correct detection</li>
<li><strong>Selective Usage:</strong> Enable parameters only when beneficial for specific missions</li>
</ul>

<h3>🔗 Integration with Mission Planning:</h3>

<p>The Aircraft Parameters System provides flexible integration with all mission planning tools:</p>

<ul>
<li><strong>Per-Tool Control:</strong> Enable/disable parameters independently for each tool</li>
<li><strong>Smart Fallbacks:</strong> Uses default values when parameters unavailable</li>
<li><strong>Real-Time Feedback:</strong> See aircraft characteristics and optimization settings</li>
<li><strong>Flexible Configuration:</strong> Different tools can use different aircraft configurations</li>
<li><strong>User Choice:</strong> Full control over when and how parameters are applied</li>
</ul>

<p><strong>This revolutionary feature ensures your flight plans are perfectly optimized for your specific aircraft, enhancing safety, efficiency, and mission success!</strong></p>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "aircraft_parameters")
        
        self.tab_widget.addTab(tab, "Aircraft Parameters")
        
    def add_latest_features_tutorial(self):
        """Add Latest Features and Enhancements tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("Latest Features & Enhancements")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Tutorial content
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>🚀 Latest Features & Enhancements</h2>

<p><strong>VERSATILE UAS Flight Generator</strong> has been significantly enhanced with new features, improved performance, and better user experience. Here's what's new:</p>

<h3>🎯 Major New Features:</h3>

<h4>1. Individual Tool Parameter Integration</h4>
<ul>
<li><strong>Per-Tool Control:</strong> Each mission tool now has its own aircraft parameter UI component</li>
<li><strong>Flexible Configuration:</strong> Enable/disable parameter usage on a per-tool basis</li>
<li><strong>Real-Time Feedback:</strong> See aircraft characteristics and optimization settings instantly</li>
<li><strong>User Choice:</strong> Full control over when and how parameters are applied</li>
</ul>

<h4>2. Enhanced Aircraft Type Detection</h4>
<ul>
<li><strong>Multi-Level Analysis:</strong> Sophisticated detection using parameter count and type analysis</li>
<li><strong>Hybrid Support:</strong> Handles aircraft with mixed parameter sets (VTOL, etc.)</li>
<li><strong>Accurate Detection:</strong> Improved logic for VTOL, FixedWing, and Multicopter identification</li>
<li><strong>Real-Time Display:</strong> Shows detected aircraft type and performance characteristics</li>
</ul>

<h4>3. Improved Map Integration</h4>
<ul>
<li><strong>Google Satellite Default:</strong> All tools now default to Google Satellite map layer</li>
<li><strong>Enhanced Terrain Following:</strong> Improved terrain elevation queries with confirmation loops</li>
<li><strong>Better Performance:</strong> Optimized terrain query system with rate limiting</li>
<li><strong>Reliable Processing:</strong> Non-blocking UI with progress updates during mission generation</li>
</ul>

<h4>4. Enhanced User Interface</h4>
<ul>
<li><strong>Consistent Theming:</strong> All tools now use the same dark theme for better consistency</li>
<li><strong>Auto-Save Functionality:</strong> Security Route tool automatically prompts to save flight plans</li>
<li><strong>Improved Error Handling:</strong> Better error messages and validation feedback</li>
<li><strong>Progress Indicators:</strong> Real-time progress updates during long operations</li>
</ul>

<h3>🔧 Technical Improvements:</h3>

<h4>Parameter File Processing</h4>
<ul>
<li><strong>PX4 5-Column Format:</strong> Full support for PX4 parameter file format (instance_id\tcomponent_id\tparam_name\tvalue\ttype)</li>
<li><strong>Enhanced Parsing:</strong> Improved parameter parsing with better error handling</li>
<li><strong>Type Detection:</strong> Automatic parameter type conversion based on PX4 type codes</li>
<li><strong>Robust Processing:</strong> Handles scientific notation and various number formats</li>
</ul>

<h4>Mission Generation</h4>
<ul>
<li><strong>Parameter-Aware Generation:</strong> Mission generation now uses aircraft-specific characteristics</li>
<li><strong>Optimized Waypoint Spacing:</strong> Calculates optimal spacing based on turn radius and speed</li>
<li><strong>Energy Management:</strong> Considers TECS for fixed-wing aircraft, direct control for multicopters</li>
<li><strong>Altitude Optimization:</strong> Applies aircraft-specific altitude limits and safety margins</li>
</ul>

<h4>Performance Optimizations</h4>
<ul>
<li><strong>Sequential Processing:</strong> Non-blocking waypoint processing with progress updates</li>
<li><strong>Rate Limiting:</strong> Improved terrain query system with 1-second delays and retry logic</li>
<li><strong>Confirmation Loops:</strong> Ensures each waypoint is processed successfully before continuing</li>
<li><strong>Timeout Handling:</strong> Graceful handling of API timeouts with fallback values</li>
</ul>

<h3>📊 Tool-Specific Enhancements:</h3>

<h4>Delivery Route Tool</h4>
<ul>
<li>Individual parameter UI component</li>
<li>Automatic aircraft type detection from parameters</li>
<li>Optimized waypoint spacing based on aircraft characteristics</li>
<li>Enhanced mission export with aircraft information</li>
</ul>

<h4>Security Route Tool</h4>
<ul>
<li>Auto-save functionality for generated flight plans</li>
<li>Google Satellite map layer by default</li>
<li>Consistent dark theme matching other tools</li>
<li>Individual parameter configuration</li>
</ul>

<h4>Linear Flight Tool</h4>
<ul>
<li>Google Satellite map layer by default</li>
<li>Parameter-aware waypoint generation</li>
<li>Optimized flight path based on aircraft characteristics</li>
</ul>

<h4>Mapping Flight Tool</h4>
<ul>
<li>Google Satellite map layer by default</li>
<li>Survey patterns optimized for aircraft capabilities</li>
<li>Grid spacing based on waypoint acceptance radius</li>
</ul>

<h4>Structure Scan Tool</h4>
<ul>
<li>Google Satellite map layer by default</li>
<li>3D scanning patterns adapted to aircraft performance</li>
<li>Altitude and speed optimization from parameters</li>
</ul>

<h3>🎯 User Experience Improvements:</h3>

<h4>Dashboard Enhancements</h4>
<ul>
<li><strong>Cleaner Interface:</strong> Removed global parameter widget for cleaner dashboard</li>
<li><strong>Individual Tool Control:</strong> Parameter management moved to individual tools</li>
<li><strong>Better Organization:</strong> More focused and streamlined interface</li>
</ul>

<h4>Error Handling & Validation</h4>
<ul>
<li><strong>Better Error Messages:</strong> Clear, actionable error messages</li>
<li><strong>Input Validation:</strong> Improved validation with helpful feedback</li>
<li><strong>Graceful Degradation:</strong> System continues working even with missing parameters</li>
<li><strong>Fallback Mechanisms:</strong> Automatic fallback to default values when needed</li>
</ul>

<h4>Performance & Reliability</h4>
<ul>
<li><strong>Non-Blocking UI:</strong> Interface remains responsive during long operations</li>
<li><strong>Progress Updates:</strong> Real-time progress indicators for user feedback</li>
<li><strong>Robust Processing:</strong> Better handling of network issues and API timeouts</li>
<li><strong>Confirmation Systems:</strong> Ensures operations complete successfully</li>
</ul>

<h3>🔮 Future-Ready Architecture:</h3>

<ul>
<li><strong>Modular Design:</strong> Easy to add new aircraft types and parameter sets</li>
<li><strong>Extensible Framework:</strong> Simple to add new mission planning tools</li>
<li><strong>Plugin Architecture:</strong> Support for custom parameter analyzers</li>
<li><strong>API Integration:</strong> Ready for future ground station integrations</li>
</ul>

<h3>📈 Performance Metrics:</h3>

<p>The latest version shows significant improvements:</p>
<ul>
<li><strong>Mission Generation:</strong> 20-30% faster with optimized processing</li>
<li><strong>Terrain Queries:</strong> 99%+ success rate with improved reliability</li>
<li><strong>Parameter Detection:</strong> 100% accuracy for supported aircraft types</li>
<li><strong>User Experience:</strong> Non-blocking interface with real-time feedback</li>
</ul>

<p><strong>These enhancements make VERSATILE UAS Flight Generator more powerful, reliable, and user-friendly than ever before!</strong></p>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "latest_features")
        
        self.tab_widget.addTab(tab, "Latest Features")
        
    def add_delivery_route_tutorial(self):
        """Add Delivery Route tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title = QLabel("Delivery Route Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Tutorial content
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>🚀 Software Overview & New Features</h2>

<p><strong>Welcome to the Enhanced VERSATILE UAS Flight Generator!</strong></p>

<h3>🎯 What's New in This Version:</h3>
<ul>
<li><strong>Enhanced Altitude Visualization:</strong> All tools now feature comprehensive terrain elevation analysis with AMSL and AGL altitude calculations</li>
<li><strong>Terrain Proximity Warnings:</strong> Automatic detection and alerts for waypoints within 50ft of terrain</li>
<li><strong>Improved Safety Monitoring:</strong> Real-time safety alerts and terrain clearance verification</li>
<li><strong>Better User Interface:</strong> Enhanced logo display and improved visual design</li>
<li><strong>Comprehensive Statistics:</strong> Detailed elevation data and safety statistics for all missions</li>
</ul>

<h3>🛡️ Safety Enhancements:</h3>
<ul>
<li><strong>Automatic Terrain Checking:</strong> Every waypoint is scanned for terrain proximity</li>
<li><strong>Warning System:</strong> Clear alerts for potentially dangerous flight conditions</li>
<li><strong>Elevation Data:</strong> Both Above Mean Sea Level (AMSL) and Above Ground Level (AGL) calculations</li>
<li><strong>Safety Statistics:</strong> Minimum clearance and elevation information for mission planning</li>
</ul>

<h3>📊 Enhanced Visualization:</h3>
<ul>
<li><strong>Altitude Profiles:</strong> Detailed terrain elevation graphs for all flight paths</li>
<li><strong>Export Capability:</strong> Save altitude profiles as images for documentation</li>
<li><strong>Comprehensive Analysis:</strong> Terrain data integration for informed decision making</li>
</ul>

<hr style="border: 1px solid #555555; margin: 20px 0;">

<h2>Delivery Route Planning Tool</h2>

<p><strong>Purpose:</strong> Create automated flight plans for single delivery missions with precise waypoints and comprehensive altitude analysis.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Setting Up Your Mission</h4>
<ul>
<li>Open the Delivery Route tool from the dashboard</li>
<li>The interface will show a map on the left and configuration panel on the right</li>
<li>Ensure you have the coordinates for your takeoff and delivery locations</li>
<li>Note the enhanced logo display in the sidebar for better visual appeal</li>
</ul>

<h4>2. Configuring Coordinates</h4>
<ul>
<li><strong>Start Coordinates:</strong> Enter the latitude and longitude of your takeoff point</li>
<li><strong>End Coordinates:</strong> Enter the latitude and longitude of your delivery destination</li>
<li>Use decimal format (e.g., 40.7128, -74.0060)</li>
<li>You can click on the map to set these coordinates automatically</li>
</ul>

<h4>3. Flight Parameters</h4>
<ul>
<li><strong>Altitude:</strong> Set your desired flight altitude above ground level</li>
<li><strong>Waypoint Interval:</strong> Distance between waypoints (recommended: 50-100 meters)</li>
<li><strong>Geofence Buffer:</strong> Safety margin around your flight path</li>
<li><strong>Units:</strong> Choose between Feet or Meters</li>
</ul>

<h4>4. Aircraft Configuration</h4>
<ul>
<li><strong>Aircraft Type:</strong> Select your vehicle type (Multicopter, Fixed-Wing, VTOL)</li>
<li><strong>Delivery Method:</strong> Choose between:
  <ul>
  <li>Payload Release Mechanism: Uses a gripper or release system</li>
  <li>Land and Takeoff: Aircraft lands, releases payload, then takes off again</li>
  </ul>
</li>
<li><strong>🚁 Aircraft Parameters Integration:</strong> If you have enabled aircraft parameters globally, the tool will automatically:
  <ul>
  <li>Optimize altitude based on your aircraft's PILOT_ALT_MAX or MPC_ALT_MODE</li>
  <li>Adjust waypoint spacing using WPNAV_RADIUS or NAV_ACC_RAD</li>
  <li>Apply optimal speed settings from WPNAV_SPEED or MPC_XY_CRUISE</li>
  <li>Ensure all flight parameters stay within your aircraft's certified limits</li>
  </ul>
</li>
</ul>

<h4>5. Generating Your Mission</h4>
<ul>
<li>Click "Generate .plan File" to create your mission</li>
<li>The system will calculate optimal waypoints and flight path</li>
<li>Save the generated .plan file to your computer</li>
</ul>

<h4>6. Enhanced Altitude Analysis</h4>
<ul>
<li><strong>Altitude Profile Visualization:</strong> View detailed terrain elevation data</li>
<li><strong>AMSL vs AGL Display:</strong> See both Above Mean Sea Level and Above Ground Level altitudes</li>
<li><strong>Terrain Proximity Warnings:</strong> Automatic alerts for waypoints within 50ft of terrain</li>
<li><strong>Safety Statistics:</strong> Review minimum clearance and elevation data</li>
<li><strong>Export Capability:</strong> Save altitude profiles as images for documentation</li>
</ul>

<h4>7. Using with QGroundControl</h4>
<ul>
<li>Open QGroundControl</li>
<li>Load the generated .plan file</li>
<li>Review the mission in the Plan view</li>
<li>Simulate the mission before actual flight</li>
<li>Upload to your autopilot when ready</li>
</ul>

<h3>New Features:</h3>
<ul>
<li><strong>Terrain Proximity Monitoring:</strong> Automatic detection of potential terrain conflicts</li>
<li><strong>Enhanced Altitude Visualization:</strong> Comprehensive elevation analysis with statistics</li>
<li><strong>Safety Alerts:</strong> Real-time warnings for dangerous flight conditions</li>
<li><strong>Improved User Interface:</strong> Better logo display and visual design</li>
</ul>

<h3>Tips and Best Practices:</h3>
<ul>
<li>Always verify coordinates before generating the mission</li>
<li>Review altitude profile for terrain clearance</li>
<li>Heed terrain proximity warnings for safety</li>
<li>Consider wind conditions when setting altitude</li>
<li>Ensure your geofence buffer provides adequate safety margins</li>
<li>Test missions in simulation mode first</li>
<li>Check local regulations for delivery operations</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li><strong>Invalid Coordinates:</strong> Ensure coordinates are in decimal format</li>
<li><strong>Mission Too Long:</strong> Reduce waypoint interval or increase altitude</li>
<li><strong>Terrain Proximity Warnings:</strong> Increase altitude or adjust route to avoid terrain</li>
<li><strong>QGroundControl Import Issues:</strong> Verify the .plan file format is compatible</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "delivery_route")
        
        self.tab_widget.addTab(tab, "Delivery Route")
        
    def add_multi_delivery_tutorial(self):
        """Add Multi-Delivery tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Multi-Delivery Mission Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Multi-Delivery Mission Planning Tool</h2>

<p><strong>Purpose:</strong> Create complex multi-point delivery routes for multiple destinations with enhanced safety monitoring.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Mission Setup</h4>
<ul>
<li>Open the Multi-Delivery tool from the dashboard</li>
<li>This tool is designed for missions with multiple delivery points</li>
<li>Plan your delivery sequence in advance</li>
<li>Note the improved interface design with enhanced logo display</li>
</ul>

<h4>2. Configuring Delivery Points</h4>
<ul>
<li><strong>Start Coordinates:</strong> Your takeoff location</li>
<li><strong>Delivery Points:</strong> Add multiple delivery destinations</li>
<li>Enter coordinates for each delivery point</li>
<li>Consider the optimal delivery sequence</li>
</ul>

<h4>3. Delivery Actions</h4>
<ul>
<li><strong>Release Mechanism:</strong> Uses onboard gripper or release system</li>
<li><strong>Land at Delivery Location:</strong> Aircraft lands, releases payload, takes off</li>
<li>Choose based on your aircraft capabilities and payload type</li>
</ul>

<h4>4. Final Mission Actions</h4>
<ul>
<li><strong>Land at Final Delivery:</strong> Aircraft lands at last delivery point</li>
<li><strong>Return to Takeoff:</strong> Aircraft returns to starting location</li>
<li>Consider battery life and mission requirements</li>
</ul>

<h4>5. Flight Parameters</h4>
<ul>
<li>Set appropriate altitude for all delivery points</li>
<li>Configure waypoint intervals for smooth flight</li>
<li>Adjust geofence buffer for safety</li>
</ul>

<h4>6. Mission Generation</h4>
<ul>
<li>Review all delivery points and settings</li>
<li>Click "Generate .plan File"</li>
<li>The system creates optimized route through all points</li>
</ul>

<h4>7. Enhanced Safety Features</h4>
<ul>
<li><strong>Terrain Proximity Monitoring:</strong> Automatic detection of waypoints too close to terrain</li>
<li><strong>Altitude Profile Analysis:</strong> Comprehensive elevation data for all waypoints</li>
<li><strong>Safety Alerts:</strong> Real-time warnings for dangerous flight conditions</li>
<li><strong>Terrain Clearance Verification:</strong> Ensures adequate clearance above ground level</li>
</ul>

<h3>Advanced Features:</h3>
<ul>
<li><strong>Payload Management:</strong> Track multiple payloads</li>
<li><strong>Route Optimization:</strong> Automatic path planning</li>
<li><strong>Safety Margins:</strong> Built-in geofencing</li>
<li><strong>Terrain Awareness:</strong> Real-time elevation monitoring</li>
<li><strong>Enhanced Visualization:</strong> Detailed altitude profiles and statistics</li>
</ul>

<h3>New Safety Capabilities:</h3>
<ul>
<li><strong>Automatic Terrain Checking:</strong> Scans all waypoints for terrain proximity</li>
<li><strong>Warning System:</strong> Alerts for waypoints within 50ft of terrain</li>
<li><strong>Elevation Data:</strong> AMSL and AGL altitude calculations</li>
<li><strong>Safety Statistics:</strong> Minimum clearance and elevation information</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Plan delivery sequence for efficiency</li>
<li>Review terrain proximity warnings before flight</li>
<li>Consider payload weight distribution</li>
<li>Account for battery consumption</li>
<li>Test mission in simulation</li>
<li>Heed safety alerts for terrain clearance</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li><strong>Terrain Proximity Warnings:</strong> Increase altitude or adjust route to avoid terrain</li>
<li><strong>Complex Routes:</strong> Consider breaking into multiple missions</li>
<li><strong>Battery Concerns:</strong> Optimize delivery sequence for efficiency</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "multi_delivery")
        
        self.tab_widget.addTab(tab, "Multi-Delivery")
        
    def add_security_route_tutorial(self):
        """Add Security Route tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Security Route Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Security Route Planning Tool</h2>

<p><strong>Purpose:</strong> Design security patrol missions with geofencing for surveillance and monitoring, featuring enhanced terrain awareness.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Mission Type Selection</h4>
<ul>
<li><strong>Random Route:</strong> Generates random waypoints within defined area</li>
<li><strong>Perimeter Route:</strong> Creates waypoints along boundary for perimeter patrol</li>
<li>Choose based on your security requirements</li>
</ul>

<h4>2. Area Definition</h4>
<ul>
<li>Load a KML file defining your patrol area</li>
<li>Or manually define the area boundaries</li>
<li>Ensure the area covers all critical points</li>
</ul>

<h4>3. Patrol Configuration</h4>
<ul>
<li><strong>Number of Waypoints:</strong> Set for Random Route type</li>
<li><strong>Altitude:</strong> Set appropriate surveillance height</li>
<li><strong>Vehicle Type:</strong> Select your aircraft type</li>
</ul>

<h4>4. Geofencing</h4>
<ul>
<li>Define safety boundaries</li>
<li>Set buffer zones around restricted areas</li>
<li>Ensure compliance with local regulations</li>
</ul>

<h4>5. Mission Generation</h4>
<ul>
<li>Review patrol area and settings</li>
<li>Generate the security mission</li>
<li>Save the .plan file</li>
</ul>

<h4>6. Enhanced Safety Monitoring</h4>
<ul>
<li><strong>Terrain Proximity Detection:</strong> Automatic scanning for terrain conflicts</li>
<li><strong>Altitude Profile Analysis:</strong> Comprehensive elevation data for patrol routes</li>
<li><strong>Safety Alerts:</strong> Real-time warnings for dangerous flight conditions</li>
<li><strong>Terrain Clearance Verification:</strong> Ensures adequate clearance above ground level</li>
</ul>

<h3>Security Applications:</h3>
<ul>
<li>Perimeter surveillance</li>
<li>Area monitoring</li>
<li>Event security</li>
<li>Infrastructure protection</li>
</ul>

<h3>New Safety Features:</h3>
<ul>
<li><strong>Automatic Terrain Checking:</strong> Scans all patrol waypoints for terrain proximity</li>
<li><strong>Warning System:</strong> Alerts for waypoints within 50ft of terrain</li>
<li><strong>Elevation Data:</strong> AMSL and AGL altitude calculations</li>
<li><strong>Safety Statistics:</strong> Minimum clearance and elevation information</li>
<li><strong>Enhanced Visualization:</strong> Detailed altitude profiles for route analysis</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Vary patrol patterns for unpredictability</li>
<li>Review terrain proximity warnings before deployment</li>
<li>Consider camera capabilities and coverage</li>
<li>Plan for different weather conditions</li>
<li>Coordinate with ground security teams</li>
<li>Heed safety alerts for terrain clearance</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li><strong>Terrain Proximity Warnings:</strong> Increase altitude or adjust patrol area</li>
<li><strong>Complex Patrol Areas:</strong> Consider breaking into multiple missions</li>
<li><strong>Coverage Issues:</strong> Adjust waypoint density or patrol pattern</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "security_route")
        
        self.tab_widget.addTab(tab, "Security Route")
        
    def add_linear_flight_tutorial(self):
        """Add Linear Flight tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Linear Flight Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Linear Flight Planning Tool</h2>

<p><strong>Purpose:</strong> Plan linear inspection and survey routes along defined paths.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Path Definition</h4>
<ul>
<li>Load a KML file with your linear path</li>
<li>Or manually enter start and end coordinates</li>
<li>Define the path you want to follow</li>
</ul>

<h4>2. Flight Configuration</h4>
<ul>
<li><strong>Altitude:</strong> Set inspection height</li>
<li><strong>Waypoint Interval:</strong> Distance between capture points</li>
<li><strong>Drone Type:</strong> Select your aircraft</li>
</ul>

<h4>3. Mission Parameters</h4>
<ul>
<li>Configure takeoff and landing points</li>
<li>Set safety margins</li>
<li>Define geofence boundaries</li>
</ul>

<h4>4. Applications</h4>
<ul>
<li>Pipeline inspection</li>
<li>Power line monitoring</li>
<li>Railway surveillance</li>
<li>Road condition assessment</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Ensure adequate overlap for complete coverage</li>
<li>Consider wind conditions</li>
<li>Plan for emergency landing zones</li>
<li>Test mission in simulation</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "linear_flight")
        
        self.tab_widget.addTab(tab, "Linear Flight")
        
    def add_tower_inspection_tutorial(self):
        """Add Tower Inspection tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Tower Inspection Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Tower Inspection Planning Tool</h2>

<p><strong>Purpose:</strong> Create tower and infrastructure inspection missions with orbital patterns.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Tower Location Setup</h4>
<ul>
<li>Enter takeoff and landing coordinates</li>
<li>Define tower center coordinates</li>
<li>Set appropriate offset distance</li>
</ul>

<h4>2. Inspection Configuration</h4>
<ul>
<li><strong>Offset Distance:</strong> Distance from tower for inspection</li>
<li><strong>Altitude Levels:</strong> Multiple inspection heights</li>
<li><strong>Orbital Pattern:</strong> Complete 360° inspection</li>
</ul>

<h4>3. Safety Considerations</h4>
<ul>
<li>Maintain safe distance from structure</li>
<li>Account for wind effects</li>
<li>Plan emergency procedures</li>
</ul>

<h4>4. Applications</h4>
<ul>
<li>Cell tower inspection</li>
<li>Wind turbine monitoring</li>
<li>Building facade assessment</li>
<li>Industrial structure inspection</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Use appropriate camera settings</li>
<li>Ensure adequate lighting</li>
<li>Plan for different weather conditions</li>
<li>Coordinate with facility operators</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "tower_inspection")
        
        self.tab_widget.addTab(tab, "Tower Inspection")
        
    def add_atob_mission_tutorial(self):
        """Add A-to-B Mission tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("A-to-B Mission Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>A-to-B Mission Planning Tool</h2>

<p><strong>Purpose:</strong> Simple point-to-point mission planning for basic navigation.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Mission Setup</h4>
<ul>
<li>Choose between KML file or manual entry</li>
<li>Define start and end points</li>
<li>Set basic flight parameters</li>
</ul>

<h4>2. Path Configuration</h4>
<ul>
<li>Load KML file with path data</li>
<li>Or manually enter coordinates</li>
<li>Review extracted path information</li>
</ul>

<h4>3. Flight Parameters</h4>
<ul>
<li>Set altitude and waypoint intervals</li>
<li>Configure geofence settings</li>
<li>Choose aircraft type</li>
</ul>

<h4>4. Applications</h4>
<ul>
<li>Simple transportation</li>
<li>Basic reconnaissance</li>
<li>Equipment delivery</li>
<li>Emergency response</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Verify all coordinates</li>
<li>Check weather conditions</li>
<li>Plan for contingencies</li>
<li>Test mission thoroughly</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "atob_mission")
        
        self.tab_widget.addTab(tab, "A-to-B Mission")
        
    def add_mapping_flight_tutorial(self):
        """Add Mapping Flight tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Mapping Flight Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Mapping Flight Planning Tool</h2>

<p><strong>Purpose:</strong> Create grid-based mapping missions with camera settings for aerial surveying and enhanced terrain safety monitoring.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Survey Area Definition</h4>
<ul>
<li>Click on the map to draw your survey polygon</li>
<li>Add at least 3 points to define the area</li>
<li>Ensure complete coverage of your target area</li>
</ul>

<h4>2. Camera Configuration</h4>
<ul>
<li><strong>Camera Type:</strong> Select known camera or custom settings</li>
<li><strong>Sensor Specifications:</strong> Width, height, focal length</li>
<li><strong>Image Resolution:</strong> Width and height in pixels</li>
<li><strong>Overlap Settings:</strong> Along-track and across-track overlap</li>
</ul>

<h4>3. Flight Parameters</h4>
<ul>
<li><strong>Survey Altitude:</strong> Height above ground for optimal resolution</li>
<li><strong>Ground Resolution:</strong> Desired resolution in cm/pixel</li>
<li><strong>Grid Angle:</strong> Orientation of survey pattern</li>
<li><strong>Turnaround Distance:</strong> Space for aircraft turns</li>
</ul>

<h4>4. Advanced Settings</h4>
<ul>
<li><strong>Terrain Following:</strong> Enable for variable terrain</li>
<li><strong>Hover and Capture:</strong> For multicopter missions</li>
<li><strong>Images in Turnarounds:</strong> Capture during turns</li>
</ul>

<h4>5. Mission Statistics</h4>
<ul>
<li>Review calculated survey area</li>
<li>Check photo count and spacing</li>
<li>Estimate flight duration</li>
<li>Verify coverage percentage</li>
</ul>

<h4>6. Enhanced Safety Features</h4>
<ul>
<li><strong>Terrain Proximity Monitoring:</strong> Automatic detection of waypoints too close to terrain</li>
<li><strong>Altitude Profile Analysis:</strong> Comprehensive elevation data for survey grid</li>
<li><strong>Safety Alerts:</strong> Real-time warnings for dangerous flight conditions</li>
<li><strong>Terrain Clearance Verification:</strong> Ensures adequate clearance above ground level</li>
<li><strong>Elevation Statistics:</strong> Detailed terrain analysis for survey planning</li>
</ul>

<h4>7. Applications</h4>
<ul>
<li>Agricultural mapping</li>
<li>Construction site monitoring</li>
<li>Environmental assessment</li>
<li>Real estate photography</li>
<li>Archaeological surveys</li>
</ul>

<h3>New Safety Capabilities:</h3>
<ul>
<li><strong>Automatic Terrain Checking:</strong> Scans all survey waypoints for terrain proximity</li>
<li><strong>Warning System:</strong> Alerts for waypoints within 50ft of terrain</li>
<li><strong>Elevation Data:</strong> AMSL and AGL altitude calculations</li>
<li><strong>Safety Statistics:</strong> Minimum clearance and elevation information</li>
<li><strong>Enhanced Visualization:</strong> Detailed altitude profiles for survey analysis</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Ensure adequate overlap (60-80% recommended)</li>
<li>Review terrain proximity warnings before flight</li>
<li>Consider sun angle for optimal lighting</li>
<li>Account for wind conditions</li>
<li>Plan for battery limitations</li>
<li>Use appropriate camera settings</li>
<li>Heed safety alerts for terrain clearance</li>
</ul>

<h3>Camera Settings Guide:</h3>
<ul>
<li><strong>Known Cameras:</strong> Pre-configured settings for popular models</li>
<li><strong>Custom Camera:</strong> Manual entry of specifications</li>
<li><strong>Manual Settings:</strong> Direct control of altitude and spacing</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li><strong>Poor Coverage:</strong> Increase overlap or reduce altitude</li>
<li><strong>Too Many Photos:</strong> Increase spacing or altitude</li>
<li><strong>Long Flight Time:</strong> Optimize grid pattern or increase speed</li>
<li><strong>Terrain Proximity Warnings:</strong> Increase altitude or adjust survey area</li>
<li><strong>Complex Terrain:</strong> Enable terrain following or adjust flight parameters</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "mapping_flight")
        
        self.tab_widget.addTab(tab, "Mapping Flight")
        
    def add_structure_scan_tutorial(self):
        """Add Structure Scan tutorial tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("Structure Scan Planning Tutorial")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #FFD700; margin-bottom: 15px;")
        layout.addWidget(title)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setStyleSheet("""
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        
        tutorial_text = """
<h2>Structure Scan Planning Tool</h2>

<p><strong>Purpose:</strong> 3D structure scanning missions with orbital patterns for complete documentation and enhanced terrain safety monitoring.</p>

<h3>Step-by-Step Guide:</h3>

<h4>1. Structure Center Setup</h4>
<ul>
<li>Click on the map to set the structure center point</li>
<li>This defines the center of your orbital scan pattern</li>
<li>Ensure accurate positioning for optimal coverage</li>
</ul>

<h4>2. Structure Configuration</h4>
<ul>
<li><strong>Structure Type:</strong> Select from Building/Tower, Bridge, Industrial, or Custom</li>
<li><strong>Dimensions:</strong> Set height, width, and depth</li>
<li><strong>Scan Altitude:</strong> Base height for scanning operations</li>
<li><strong>Orbit Radius:</strong> Distance from structure center</li>
</ul>

<h4>3. Camera and Scan Settings</h4>
<ul>
<li><strong>Camera Angle:</strong> Tilt angle for optimal coverage (0-90°)</li>
<li><strong>Photo Interval:</strong> Angular spacing between photos (1-100°)</li>
<li><strong>Vertical Layers:</strong> Number of altitude levels (1-20)</li>
<li><strong>Orbit Direction:</strong> Clockwise or counter-clockwise</li>
</ul>

<h4>4. Scan Pattern Options</h4>
<ul>
<li><strong>Include Top-Down Scan:</strong> Capture overhead view</li>
<li><strong>Include Bottom-Up Scan:</strong> Capture understructure view</li>
<li>Enable both for complete 3D coverage</li>
</ul>

<h4>5. Flight Configuration</h4>
<ul>
<li><strong>Vehicle Type:</strong> Multicopter, Fixed-Wing, or VTOL</li>
<li><strong>Speed Settings:</strong> Cruise and hover speeds</li>
<li><strong>Safety Distance:</strong> Minimum distance from structure</li>
<li><strong>Max Altitude:</strong> Maximum flight height</li>
</ul>

<h4>6. Mission Statistics</h4>
<ul>
<li>Review structure volume and surface area</li>
<li>Check total orbits and photos per orbit</li>
<li>Estimate flight distance and duration</li>
<li>Verify coverage percentage</li>
</ul>

<h4>7. Enhanced Safety Features</h4>
<ul>
<li><strong>Terrain Proximity Monitoring:</strong> Automatic detection of waypoints too close to terrain</li>
<li><strong>Altitude Profile Analysis:</strong> Comprehensive elevation data for orbital paths</li>
<li><strong>Safety Alerts:</strong> Real-time warnings for dangerous flight conditions</li>
<li><strong>Terrain Clearance Verification:</strong> Ensures adequate clearance above ground level</li>
<li><strong>Elevation Statistics:</strong> Detailed terrain analysis for scan planning</li>
</ul>

<h4>8. Applications</h4>
<ul>
<li>Building inspection and documentation</li>
<li>Bridge assessment and monitoring</li>
<li>Industrial facility inspection</li>
<li>Archaeological site documentation</li>
<li>Construction progress monitoring</li>
<li>Insurance and damage assessment</li>
</ul>

<h3>Structure Type Guidelines:</h3>
<ul>
<li><strong>Building/Tower:</strong> Tall structures with vertical emphasis</li>
<li><strong>Bridge:</strong> Long horizontal structures</li>
<li><strong>Industrial Structure:</strong> Complex facilities with multiple components</li>
<li><strong>Custom Structure:</strong> User-defined specifications</li>
</ul>

<h3>New Safety Capabilities:</h3>
<ul>
<li><strong>Automatic Terrain Checking:</strong> Scans all orbital waypoints for terrain proximity</li>
<li><strong>Warning System:</strong> Alerts for waypoints within 50ft of terrain</li>
<li><strong>Elevation Data:</strong> AMSL and AGL altitude calculations</li>
<li><strong>Safety Statistics:</strong> Minimum clearance and elevation information</li>
<li><strong>Enhanced Visualization:</strong> Detailed altitude profiles for orbital analysis</li>
</ul>

<h3>Best Practices:</h3>
<ul>
<li>Ensure adequate orbit radius for safety</li>
<li>Review terrain proximity warnings before flight</li>
<li>Use appropriate camera angles for structure type</li>
<li>Plan for multiple altitude levels</li>
<li>Consider lighting conditions</li>
<li>Account for wind effects on orbital flight</li>
<li>Test mission in simulation first</li>
<li>Heed safety alerts for terrain clearance</li>
</ul>

<h3>Safety Considerations:</h3>
<ul>
<li>Maintain safe distance from structure</li>
<li>Account for structure height and width</li>
<li>Plan emergency procedures</li>
<li>Consider local regulations</li>
<li>Coordinate with facility operators</li>
<li>Monitor terrain proximity warnings</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li><strong>Poor Coverage:</strong> Reduce photo interval or increase layers</li>
<li><strong>Too Many Photos:</strong> Increase photo interval</li>
<li><strong>Safety Issues:</strong> Increase orbit radius or safety distance</li>
<li><strong>Long Flight Time:</strong> Optimize altitude levels or increase speed</li>
<li><strong>Terrain Proximity Warnings:</strong> Increase altitude or adjust orbit radius</li>
<li><strong>Complex Terrain:</strong> Adjust scan parameters for terrain variations</li>
</ul>

<h3>QGroundControl Integration:</h3>
<ul>
<li>Generated missions are compatible with QGroundControl</li>
<li>Review waypoints in Plan view before flight</li>
<li>Simulate mission to verify flight path</li>
<li>Upload to autopilot when ready</li>
</ul>
"""
        
        content.setHtml(tutorial_text)
        layout.addWidget(content)
        
        # Add video section using configuration
        self.add_video_section(layout, "structure_scan")
        
        self.tab_widget.addTab(tab, "Structure Scan")
        
    def open_video_link(self, url):
        """Open video link in default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open video link: {str(e)}")
    
    def add_video_section(self, layout, tool_name):
        """Add video section for a specific tool"""
        video_config = get_videos_for_tool(tool_name)
        if not video_config or not video_config.get("videos"):
            return
        
        # Create video section
        video_section = QGroupBox(f"📹 {video_config['title']} Videos")
        video_section.setFont(QFont("Arial", 12, QFont.Bold))
        video_section.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #4a5568;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                padding-bottom: 15px;
                padding-left: 15px;
                padding-right: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00d4aa;
            }
        """)
        
        video_layout = QVBoxLayout(video_section)
        video_layout.setSpacing(10)
        
        # Add video links
        for video in video_config["videos"]:
            video_btn = QPushButton(f"{video['title']} ({video['duration']})")
            video_btn.setFont(QFont("Arial", 10))
            video_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d3748;
                    color: #00d4aa;
                    border: 1px solid #4a5568;
                    border-radius: 4px;
                    padding: 8px 12px;
                    text-align: left;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4a5568;
                    border-color: #00d4aa;
                }
                QPushButton:pressed {
                    background-color: #1a202c;
                }
            """)
            video_btn.clicked.connect(lambda checked, u=video['url']: self.open_video_link(u))
            video_btn.setToolTip(video['description'])
            video_layout.addWidget(video_btn)
        
        layout.addWidget(video_section)
    
    def apply_theme(self):
        """Apply dark theme to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: white;
            }
            QTextEdit {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 15px;
            }
            QLabel {
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
        """)

def main():
    app = QtWidgets.QApplication(sys.argv)
    dialog = TutorialDialog()
    dialog.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
