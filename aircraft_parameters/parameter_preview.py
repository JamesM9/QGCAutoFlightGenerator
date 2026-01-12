#!/usr/bin/env python3
"""
Parameter Impact Preview System
Provides real-time preview of how aircraft parameters affect mission planning
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QFrame, QGridLayout, QPushButton, QComboBox, QSpinBox,
    QDoubleSpinBox, QCheckBox, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
from typing import Dict, List, Any, Optional
import json


class ParameterImpactWidget(QWidget):
    """Widget showing how parameters impact mission planning"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_config = None
        self.mission_type = "general"
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Parameter Impact Preview")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Mission type selector
        mission_layout = QHBoxLayout()
        mission_layout.addWidget(QLabel("Mission Type:"))
        self.mission_type_combo = QComboBox()
        self.mission_type_combo.addItems([
            "General", "Delivery Route", "Multi-Delivery", "Security Route",
            "Linear Flight", "Tower Inspection", "A-to-B", "Mapping", "Structure Scan"
        ])
        self.mission_type_combo.currentTextChanged.connect(self.on_mission_type_changed)
        mission_layout.addWidget(self.mission_type_combo)
        layout.addLayout(mission_layout)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Parameter values
        left_panel = self.create_parameter_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Impact analysis
        right_panel = self.create_impact_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
    def create_parameter_panel(self):
        """Create the parameter values panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Parameter values group
        values_group = QGroupBox("Current Parameter Values")
        values_layout = QVBoxLayout(values_group)
        
        # Create parameter table
        self.param_table = QTableWidget()
        self.param_table.setColumnCount(3)
        self.param_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        self.param_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.param_table.setMaximumHeight(300)
        values_layout.addWidget(self.param_table)
        
        layout.addWidget(values_group)
        
        # Flight characteristics group
        characteristics_group = QGroupBox("Flight Characteristics")
        characteristics_layout = QVBoxLayout(characteristics_group)
        
        self.characteristics_text = QTextEdit()
        self.characteristics_text.setMaximumHeight(200)
        self.characteristics_text.setReadOnly(True)
        characteristics_layout.addWidget(self.characteristics_text)
        
        layout.addWidget(characteristics_group)
        
        return panel
        
    def create_impact_panel(self):
        """Create the impact analysis panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Impact analysis group
        impact_group = QGroupBox("Mission Impact Analysis")
        impact_layout = QVBoxLayout(impact_group)
        
        # Impact summary
        self.impact_summary = QTextEdit()
        self.impact_summary.setMaximumHeight(150)
        self.impact_summary.setReadOnly(True)
        impact_layout.addWidget(self.impact_summary)
        
        # Detailed impact table
        self.impact_table = QTableWidget()
        self.impact_table.setColumnCount(4)
        self.impact_table.setHorizontalHeaderLabels([
            "Mission Aspect", "Manual Value", "Aircraft Value", "Impact"
        ])
        self.impact_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        impact_layout.addWidget(self.impact_table)
        
        layout.addWidget(impact_group)
        
        # Recommendations group
        recommendations_group = QGroupBox("Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(150)
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        return panel
        
    def on_mission_type_changed(self, mission_type):
        """Handle mission type change"""
        self.mission_type = mission_type.lower().replace(" ", "_").replace("-", "_")
        if self.current_config:
            self.update_impact_analysis()
            
    def update_configuration(self, config):
        """Update the configuration being previewed"""
        self.current_config = config
        self.update_parameter_display()
        self.update_impact_analysis()
        
    def update_parameter_display(self):
        """Update the parameter values display"""
        if not self.current_config:
            return
            
        # Get key parameters for display
        key_params = self.get_key_parameters()
        
        self.param_table.setRowCount(len(key_params))
        
        for row, (param_name, param_info) in enumerate(key_params.items()):
            # Parameter name
            name_item = QTableWidgetItem(param_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.param_table.setItem(row, 0, name_item)
            
            # Parameter value
            value = self.current_config.parameters.get(param_name, "N/A")
            value_item = QTableWidgetItem(str(value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.param_table.setItem(row, 1, value_item)
            
            # Parameter unit
            unit = param_info.get("unit", "")
            unit_item = QTableWidgetItem(unit)
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            self.param_table.setItem(row, 2, unit_item)
            
        # Update flight characteristics
        self.update_flight_characteristics()
        
    def get_key_parameters(self):
        """Get key parameters for the current mission type"""
        # Define key parameters for different mission types
        param_groups = {
            "general": {
                "WPNAV_SPEED": {"unit": "m/s", "description": "Waypoint navigation speed"},
                "WPNAV_RADIUS": {"unit": "m", "description": "Waypoint acceptance radius"},
                "PILOT_ALT_MAX": {"unit": "m", "description": "Maximum altitude"},
                "RTL_ALT": {"unit": "m", "description": "Return-to-launch altitude"},
            },
            "delivery_route": {
                "WPNAV_SPEED": {"unit": "m/s", "description": "Delivery speed"},
                "WPNAV_RADIUS": {"unit": "m", "description": "Delivery accuracy"},
                "PILOT_ALT_MAX": {"unit": "m", "description": "Delivery altitude"},
                "RTL_ALT": {"unit": "m", "description": "Return altitude"},
            },
            "mapping": {
                "WPNAV_SPEED": {"unit": "m/s", "description": "Mapping speed"},
                "WPNAV_RADIUS": {"unit": "m", "description": "Mapping accuracy"},
                "PILOT_ALT_MAX": {"unit": "m", "description": "Mapping altitude"},
                "RTL_ALT": {"unit": "m", "description": "Return altitude"},
            },
            "structure_scan": {
                "WPNAV_SPEED": {"unit": "m/s", "description": "Scan speed"},
                "WPNAV_RADIUS": {"unit": "m", "description": "Scan accuracy"},
                "PILOT_ALT_MAX": {"unit": "m", "description": "Scan altitude"},
                "RTL_ALT": {"unit": "m", "description": "Return altitude"},
            }
        }
        
        return param_groups.get(self.mission_type, param_groups["general"])
        
    def update_flight_characteristics(self):
        """Update flight characteristics display"""
        if not self.current_config:
            return
            
        characteristics = []
        characteristics.append(f"Firmware: {self.current_config.firmware_type}")
        characteristics.append(f"Vehicle Type: {self.current_config.vehicle_type}")
        characteristics.append(f"Created: {self.current_config.created_at}")
        
        # Add parameter-specific characteristics
        if "WPNAV_SPEED" in self.current_config.parameters:
            speed = self.current_config.parameters["WPNAV_SPEED"]
            characteristics.append(f"Navigation Speed: {speed} m/s")
            
        if "WPNAV_RADIUS" in self.current_config.parameters:
            radius = self.current_config.parameters["WPNAV_RADIUS"]
            characteristics.append(f"Waypoint Radius: {radius} m")
            
        if "PILOT_ALT_MAX" in self.current_config.parameters:
            alt_max = self.current_config.parameters["PILOT_ALT_MAX"]
            characteristics.append(f"Max Altitude: {alt_max} m")
            
        self.characteristics_text.setText("\n".join(characteristics))
        
    def update_impact_analysis(self):
        """Update the impact analysis"""
        if not self.current_config:
            return
            
        # Generate impact analysis
        impact_data = self.generate_impact_analysis()
        
        # Update impact summary
        self.update_impact_summary(impact_data)
        
        # Update impact table
        self.update_impact_table(impact_data)
        
        # Update recommendations
        self.update_recommendations(impact_data)
        
    def generate_impact_analysis(self):
        """Generate impact analysis for the current configuration"""
        if not self.current_config:
            return {}
            
        # Define default values for comparison
        default_values = {
            "altitude": 100,  # meters
            "waypoint_spacing": 50,  # meters
            "cruise_speed": 15,  # m/s
            "hover_speed": 5,  # m/s
            "turn_radius": 10,  # meters
        }
        
        # Calculate aircraft-aware values
        aircraft_values = {}
        
        # Altitude impact
        if "PILOT_ALT_MAX" in self.current_config.parameters:
            max_alt = self.current_config.parameters["PILOT_ALT_MAX"]
            aircraft_values["altitude"] = min(max_alt * 0.8, default_values["altitude"])
        else:
            aircraft_values["altitude"] = default_values["altitude"]
            
        # Waypoint spacing impact
        if "WPNAV_RADIUS" in self.current_config.parameters:
            radius = self.current_config.parameters["WPNAV_RADIUS"]
            aircraft_values["waypoint_spacing"] = max(radius * 2, default_values["waypoint_spacing"])
        else:
            aircraft_values["waypoint_spacing"] = default_values["waypoint_spacing"]
            
        # Speed impact
        if "WPNAV_SPEED" in self.current_config.parameters:
            speed = self.current_config.parameters["WPNAV_SPEED"]
            aircraft_values["cruise_speed"] = speed
            aircraft_values["hover_speed"] = speed * 0.3
        else:
            aircraft_values["cruise_speed"] = default_values["cruise_speed"]
            aircraft_values["hover_speed"] = default_values["hover_speed"]
            
        # Turn radius impact
        if "WPNAV_RADIUS" in self.current_config.parameters:
            radius = self.current_config.parameters["WPNAV_RADIUS"]
            aircraft_values["turn_radius"] = radius
        else:
            aircraft_values["turn_radius"] = default_values["turn_radius"]
            
        return {
            "default": default_values,
            "aircraft": aircraft_values,
            "mission_type": self.mission_type
        }
        
    def update_impact_summary(self, impact_data):
        """Update the impact summary text"""
        if not impact_data:
            return
            
        summary = []
        summary.append("Parameter Impact Summary:")
        summary.append("")
        
        # Calculate overall impact
        total_changes = 0
        significant_changes = 0
        
        for key in impact_data["default"]:
            default_val = impact_data["default"][key]
            aircraft_val = impact_data["aircraft"][key]
            
            if default_val != aircraft_val:
                total_changes += 1
                change_percent = abs((aircraft_val - default_val) / default_val * 100)
                if change_percent > 20:
                    significant_changes += 1
                    
        summary.append(f"Total parameter changes: {total_changes}")
        summary.append(f"Significant changes (>20%): {significant_changes}")
        summary.append("")
        
        if significant_changes > 0:
            summary.append("⚠️ Significant parameter impact detected")
            summary.append("Mission planning will be optimized for this aircraft")
        else:
            summary.append("✅ Minimal parameter impact")
            summary.append("Mission planning will use standard values")
            
        self.impact_summary.setText("\n".join(summary))
        
    def update_impact_table(self, impact_data):
        """Update the impact analysis table"""
        if not impact_data:
            return
            
        # Define mission aspects
        aspects = {
            "altitude": "Mission Altitude",
            "waypoint_spacing": "Waypoint Spacing",
            "cruise_speed": "Cruise Speed",
            "hover_speed": "Hover Speed",
            "turn_radius": "Turn Radius"
        }
        
        self.impact_table.setRowCount(len(aspects))
        
        for row, (key, aspect_name) in enumerate(aspects.items()):
            # Mission aspect
            aspect_item = QTableWidgetItem(aspect_name)
            aspect_item.setFlags(aspect_item.flags() & ~Qt.ItemIsEditable)
            self.impact_table.setItem(row, 0, aspect_item)
            
            # Manual value
            manual_val = impact_data["default"][key]
            manual_item = QTableWidgetItem(f"{manual_val:.1f}")
            manual_item.setFlags(manual_item.flags() & ~Qt.ItemIsEditable)
            self.impact_table.setItem(row, 1, manual_item)
            
            # Aircraft value
            aircraft_val = impact_data["aircraft"][key]
            aircraft_item = QTableWidgetItem(f"{aircraft_val:.1f}")
            aircraft_item.setFlags(aircraft_item.flags() & ~Qt.ItemIsEditable)
            self.impact_table.setItem(row, 2, aircraft_item)
            
            # Impact
            change_percent = (aircraft_val - manual_val) / manual_val * 100
            if abs(change_percent) < 5:
                impact_text = "Minimal"
                impact_color = QColor(76, 175, 80)  # Green
            elif abs(change_percent) < 20:
                impact_text = "Moderate"
                impact_color = QColor(255, 193, 7)  # Yellow
            else:
                impact_text = "Significant"
                impact_color = QColor(244, 67, 54)  # Red
                
            impact_item = QTableWidgetItem(impact_text)
            impact_item.setFlags(impact_item.flags() & ~Qt.ItemIsEditable)
            impact_item.setBackground(impact_color)
            self.impact_table.setItem(row, 3, impact_item)
            
    def update_recommendations(self, impact_data):
        """Update recommendations based on impact analysis"""
        if not impact_data:
            return
            
        recommendations = []
        recommendations.append("Recommendations:")
        recommendations.append("")
        
        # Check for altitude constraints
        if "PILOT_ALT_MAX" in self.current_config.parameters:
            max_alt = self.current_config.parameters["PILOT_ALT_MAX"]
            if max_alt < 150:
                recommendations.append("⚠️ Low altitude limit detected")
                recommendations.append("Consider terrain clearance and obstacles")
                
        # Check for speed constraints
        if "WPNAV_SPEED" in self.current_config.parameters:
            speed = self.current_config.parameters["WPNAV_SPEED"]
            if speed < 10:
                recommendations.append("⚠️ Low speed limit detected")
                recommendations.append("Mission duration may be longer than expected")
                
        # Check for radius constraints
        if "WPNAV_RADIUS" in self.current_config.parameters:
            radius = self.current_config.parameters["WPNAV_RADIUS"]
            if radius > 20:
                recommendations.append("⚠️ Large waypoint radius detected")
                recommendations.append("Mission accuracy may be reduced")
                
        if not recommendations:
            recommendations.append("✅ No specific recommendations")
            recommendations.append("Aircraft parameters are well-suited for this mission type")
            
        self.recommendations_text.setText("\n".join(recommendations))
