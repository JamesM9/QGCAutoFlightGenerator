#!/usr/bin/env python3
"""
Enhanced Form Components with validation and better UX
"""

import sys
import json
import os
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                             QPushButton, QFrame, QGroupBox, QCheckBox,
                             QTextEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QProgressBar, QSlider, QTabWidget)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QValidator, QRegExpValidator

class ValidatedLineEdit(QLineEdit):
    """Line edit with validation and visual feedback"""
    
    def __init__(self, placeholder="", validator=None, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.validator = validator
        self.is_valid = True
        self.setup_validation()
        
    def setup_validation(self):
        if self.validator:
            self.setValidator(self.validator)
        
        self.textChanged.connect(self.validate_input)
        
    def validate_input(self):
        """Validate input and update visual state"""
        if self.validator:
            state = self.validator.validate(self.text(), 0)[0]
            self.is_valid = (state == QValidator.Acceptable)
        else:
            self.is_valid = True
            
        self.update_visual_state()
        
    def update_visual_state(self):
        """Update visual appearance based on validation state"""
        if self.is_valid:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #3C3C3C;
                    color: white;
                    border: 1px solid #555555;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #FFD700;
                }
            """)
        else:
            self.setStyleSheet("""
                QLineEdit {
                    background-color: #3C3C3C;
                    color: white;
                    border: 2px solid #F44336;
                    border-radius: 4px;
                    padding: 8px;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #F44336;
                }
            """)
            
    def isValid(self):
        """Return validation state"""
        return self.is_valid

class CoordinateInput(ValidatedLineEdit):
    """Specialized input for coordinate pairs"""
    
    def __init__(self, parent=None):
        # Coordinate regex: -90 to 90 for lat, -180 to 180 for lng
        regex = r"^-?\d{1,2}(\.\d+)?,\s*-?\d{1,3}(\.\d+)?$"
        validator = QRegExpValidator(QRegExp(regex))
        super().__init__("lat, lng", validator, parent)
        
    def getCoordinates(self):
        """Parse and return coordinates as tuple"""
        if not self.is_valid:
            return None
            
        try:
            coords = self.text().split(',')
            lat = float(coords[0].strip())
            lng = float(coords[1].strip())
            
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        except (ValueError, IndexError):
            pass
            
        return None

class AutoSaveForm(QWidget):
    """Form with auto-save functionality"""
    
    def __init__(self, save_file="autosave.json", parent=None):
        super().__init__(parent)
        self.save_file = save_file
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
        
        self.setup_ui()
        self.load_autosave()
        
    def setup_ui(self):
        """Setup the form UI - to be overridden"""
        pass
        
    def auto_save(self):
        """Auto-save form data"""
        data = self.get_form_data()
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Auto-save failed: {e}")
            
    def load_autosave(self):
        """Load auto-saved data"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    data = json.load(f)
                self.set_form_data(data)
            except Exception as e:
                print(f"Failed to load auto-save: {e}")
                
    def get_form_data(self):
        """Get form data for saving - to be overridden"""
        return {}
        
    def set_form_data(self, data):
        """Set form data from saved data - to be overridden"""
        pass

class CollapsibleGroupBox(QGroupBox):
    """Collapsible group box for organizing form sections"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.is_collapsed = False
        self.setup_ui()
        
    def setup_ui(self):
        # Create toggle button
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFD700;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
            }
        """)
        
        # Add button to layout
        layout = self.layout()
        if layout:
            header_layout = QHBoxLayout()
            header_layout.addWidget(self.toggle_btn)
            header_layout.addStretch()
            layout.insertLayout(0, header_layout)
            
    def toggle_collapse(self):
        """Toggle collapse state"""
        self.is_collapsed = not self.is_collapsed
        
        # Update button text
        self.toggle_btn.setText("▲" if self.is_collapsed else "▼")
        
        # Show/hide content
        layout = self.layout()
        if layout:
            for i in range(1, layout.count()):  # Skip header layout
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().setVisible(not self.is_collapsed)

class MissionTemplateSelector(QWidget):
    """Widget for selecting mission templates"""
    
    template_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.templates = self.load_templates()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Template selector
        self.template_combo = QComboBox()
        self.template_combo.addItem("Select Template...")
        for template in self.templates:
            self.template_combo.addItem(template['name'])
        self.template_combo.currentTextChanged.connect(self.on_template_selected)
        
        layout.addWidget(QLabel("Mission Template:"))
        layout.addWidget(self.template_combo)
        
        # Template description
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #CCCCCC; font-size: 11px;")
        layout.addWidget(self.description_label)
        
    def load_templates(self):
        """Load mission templates"""
        return [
            {
                'name': 'Quick Delivery',
                'description': 'Simple A-to-B delivery with standard settings',
                'data': {
                    'altitude': 100,
                    'altitude_units': 'Meters',
                    'aircraft_type': 'Multicopter/Helicopter'
                }
            },
            {
                'name': 'Security Patrol',
                'description': 'Perimeter security patrol with geofencing',
                'data': {
                    'altitude': 150,
                    'altitude_units': 'Meters',
                    'aircraft_type': 'Multicopter/Helicopter',
                    'geofence_enabled': True
                }
            },
            {
                'name': 'Tower Inspection',
                'description': 'Close-range tower inspection mission',
                'data': {
                    'altitude': 50,
                    'altitude_units': 'Meters',
                    'aircraft_type': 'Multicopter/Helicopter',
                    'waypoint_interval': 10
                }
            }
        ]
        
    def on_template_selected(self, template_name):
        """Handle template selection"""
        if template_name == "Select Template...":
            self.description_label.setText("")
            return
            
        for template in self.templates:
            if template['name'] == template_name:
                self.description_label.setText(template['description'])
                self.template_selected.emit(template['data'])
                break

class EnhancedFormWidget(QWidget):
    """Enhanced form widget with validation and better UX"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Mission details section
        mission_group = CollapsibleGroupBox("Mission Details")
        mission_layout = QVBoxLayout(mission_group)
        
        # Mission name
        self.mission_name = ValidatedLineEdit("Enter mission name")
        mission_layout.addWidget(QLabel("Mission Name:"))
        mission_layout.addWidget(self.mission_name)
        
        # Template selector
        self.template_selector = MissionTemplateSelector()
        self.template_selector.template_selected.connect(self.apply_template)
        mission_layout.addWidget(self.template_selector)
        
        layout.addWidget(mission_group)
        
        # Coordinates section
        coords_group = CollapsibleGroupBox("Coordinates")
        coords_layout = QVBoxLayout(coords_group)
        
        # Start coordinates
        self.start_coords = CoordinateInput()
        coords_layout.addWidget(QLabel("Start Coordinates (lat, lng):"))
        coords_layout.addWidget(self.start_coords)
        
        # End coordinates
        self.end_coords = CoordinateInput()
        coords_layout.addWidget(QLabel("End Coordinates (lat, lng):"))
        coords_layout.addWidget(self.end_coords)
        
        layout.addWidget(coords_group)
        
        # Flight settings section
        settings_group = CollapsibleGroupBox("Flight Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        # Aircraft type
        self.aircraft_type = QComboBox()
        self.aircraft_type.addItems([
            "Multicopter/Helicopter",
            "Fixed Wing", 
            "VTOL/Fixed Wing Hybrid"
        ])
        settings_layout.addWidget(QLabel("Aircraft Type:"))
        settings_layout.addWidget(self.aircraft_type)
        
        # Altitude
        altitude_layout = QHBoxLayout()
        self.altitude = QSpinBox()
        self.altitude.setRange(10, 1000)
        self.altitude.setValue(100)
        self.altitude_units = QComboBox()
        self.altitude_units.addItems(["Meters", "Feet"])
        
        altitude_layout.addWidget(QLabel("Altitude:"))
        altitude_layout.addWidget(self.altitude)
        altitude_layout.addWidget(self.altitude_units)
        settings_layout.addLayout(altitude_layout)
        
        # Waypoint interval
        self.waypoint_interval = QSpinBox()
        self.waypoint_interval.setRange(5, 100)
        self.waypoint_interval.setValue(20)
        settings_layout.addWidget(QLabel("Waypoint Interval (meters):"))
        settings_layout.addWidget(self.waypoint_interval)
        
        layout.addWidget(settings_group)
        
        # Advanced settings section
        advanced_group = CollapsibleGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Geofence
        self.geofence_enabled = QCheckBox("Enable Geofence")
        advanced_layout.addWidget(self.geofence_enabled)
        
        # Geofence buffer
        self.geofence_buffer = QSpinBox()
        self.geofence_buffer.setRange(10, 500)
        self.geofence_buffer.setValue(50)
        advanced_layout.addWidget(QLabel("Geofence Buffer (meters):"))
        advanced_layout.addWidget(self.geofence_buffer)
        
        layout.addWidget(advanced_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("Validate Form")
        self.validate_btn.clicked.connect(self.validate_form)
        button_layout.addWidget(self.validate_btn)
        
        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.clicked.connect(self.clear_form)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        layout.addWidget(self.status_label)
        
    def apply_template(self, template_data):
        """Apply selected template data"""
        for key, value in template_data.items():
            if hasattr(self, key):
                widget = getattr(self, key)
                if isinstance(widget, QSpinBox):
                    widget.setValue(value)
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(value)
                    
    def validate_form(self):
        """Validate the entire form"""
        errors = []
        
        # Check mission name
        if not self.mission_name.text().strip():
            errors.append("Mission name is required")
            
        # Check coordinates
        if not self.start_coords.getCoordinates():
            errors.append("Invalid start coordinates")
            
        if not self.end_coords.getCoordinates():
            errors.append("Invalid end coordinates")
            
        # Check altitude
        if self.altitude.value() <= 0:
            errors.append("Altitude must be greater than 0")
            
        if errors:
            error_msg = "Validation errors:\n" + "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Validation Errors", error_msg)
            self.status_label.setText("Validation failed")
            self.status_label.setStyleSheet("color: #F44336; font-size: 11px;")
        else:
            self.status_label.setText("Form is valid")
            self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
            QMessageBox.information(self, "Success", "Form validation passed!")
            
    def clear_form(self):
        """Clear all form fields"""
        self.mission_name.clear()
        self.start_coords.clear()
        self.end_coords.clear()
        self.aircraft_type.setCurrentIndex(0)
        self.altitude.setValue(100)
        self.altitude_units.setCurrentIndex(0)
        self.waypoint_interval.setValue(20)
        self.geofence_enabled.setChecked(False)
        self.geofence_buffer.setValue(50)
        self.template_selector.template_combo.setCurrentIndex(0)
        
        self.status_label.setText("Form cleared")
        self.status_label.setStyleSheet("color: #FF9800; font-size: 11px;")
        
    def get_form_data(self):
        """Get all form data as dictionary"""
        return {
            'mission_name': self.mission_name.text(),
            'start_coords': self.start_coords.getCoordinates(),
            'end_coords': self.end_coords.getCoordinates(),
            'aircraft_type': self.aircraft_type.currentText(),
            'altitude': self.altitude.value(),
            'altitude_units': self.altitude_units.currentText(),
            'waypoint_interval': self.waypoint_interval.value(),
            'geofence_enabled': self.geofence_enabled.isChecked(),
            'geofence_buffer': self.geofence_buffer.value()
        } 