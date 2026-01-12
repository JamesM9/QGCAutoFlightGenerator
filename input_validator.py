#!/usr/bin/env python3
"""
Input Validation System
Provides real-time validation feedback for mission planning inputs
"""

import re
import math
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QVBoxLayout, 
                              QHBoxLayout, QFrame, QTimer)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter

class ValidationState:
    """Validation states for input fields"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    LOADING = "loading"
    EMPTY = "empty"

class InputValidator:
    """Main input validation system"""
    
    def __init__(self):
        self.validation_rules = {
            'latitude': self.validate_latitude,
            'longitude': self.validate_longitude,
            'altitude': self.validate_altitude,
            'waypoint_interval': self.validate_waypoint_interval,
            'filename': self.validate_filename,
            'email': self.validate_email,
            'coordinate_pair': self.validate_coordinate_pair
        }
        
    def validate_latitude(self, value):
        """Validate latitude coordinate"""
        try:
            lat = float(value)
            if -90 <= lat <= 90:
                return ValidationState.VALID, "Valid latitude"
            else:
                return ValidationState.INVALID, "Latitude must be between -90 and 90 degrees"
        except ValueError:
            if not value.strip():
                return ValidationState.EMPTY, "Latitude is required"
            return ValidationState.INVALID, "Invalid latitude format"
    
    def validate_longitude(self, value):
        """Validate longitude coordinate"""
        try:
            lon = float(value)
            if -180 <= lon <= 180:
                return ValidationState.VALID, "Valid longitude"
            else:
                return ValidationState.INVALID, "Longitude must be between -180 and 180 degrees"
        except ValueError:
            if not value.strip():
                return ValidationState.EMPTY, "Longitude is required"
            return ValidationState.INVALID, "Invalid longitude format"
    
    def validate_altitude(self, value):
        """Validate altitude value"""
        try:
            alt = float(value)
            if alt < 0:
                return ValidationState.INVALID, "Altitude cannot be negative"
            elif alt > 5000:
                return ValidationState.WARNING, "Altitude above 5000m may require special permissions"
            elif alt > 10000:
                return ValidationState.INVALID, "Altitude above 10,000m is not allowed"
            else:
                return ValidationState.VALID, "Valid altitude"
        except ValueError:
            if not value.strip():
                return ValidationState.EMPTY, "Altitude is required"
            return ValidationState.INVALID, "Invalid altitude format"
    
    def validate_waypoint_interval(self, value):
        """Validate waypoint interval"""
        try:
            interval = float(value)
            if interval < 5:
                return ValidationState.INVALID, "Interval must be at least 5 meters"
            elif interval > 1000:
                return ValidationState.WARNING, "Large intervals may reduce mission precision"
            else:
                return ValidationState.VALID, "Valid interval"
        except ValueError:
            if not value.strip():
                return ValidationState.EMPTY, "Interval is required"
            return ValidationState.INVALID, "Invalid interval format"
    
    def validate_filename(self, value):
        """Validate filename"""
        if not value.strip():
            return ValidationState.EMPTY, "Filename is required"
        
        # Check for invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, value):
            return ValidationState.INVALID, "Filename contains invalid characters"
        
        if len(value) > 255:
            return ValidationState.INVALID, "Filename too long (max 255 characters)"
        
        return ValidationState.VALID, "Valid filename"
    
    def validate_email(self, value):
        """Validate email address"""
        if not value.strip():
            return ValidationState.EMPTY, "Email is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, value):
            return ValidationState.VALID, "Valid email address"
        else:
            return ValidationState.INVALID, "Invalid email format"
    
    def validate_coordinate_pair(self, lat_value, lon_value):
        """Validate coordinate pair"""
        lat_state, lat_msg = self.validate_latitude(lat_value)
        lon_state, lon_msg = self.validate_longitude(lon_value)
        
        if lat_state == ValidationState.VALID and lon_state == ValidationState.VALID:
            return ValidationState.VALID, "Valid coordinates"
        elif lat_state == ValidationState.EMPTY or lon_state == ValidationState.EMPTY:
            return ValidationState.EMPTY, "Both coordinates are required"
        else:
            return ValidationState.INVALID, f"Coordinate error: {lat_msg if lat_state != ValidationState.VALID else lon_msg}"

class ValidatedInput(QWidget):
    """Input field with real-time validation"""
    
    validation_changed = pyqtSignal(str, str)  # state, message
    
    def __init__(self, label_text, input_type="text", placeholder="", parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.input_type = input_type
        self.placeholder = placeholder
        self.validator = InputValidator()
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.perform_validation)
        
        self.setup_ui()
        self.current_state = ValidationState.EMPTY
        
    def setup_ui(self):
        """Setup the validated input UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        self.label = QLabel(self.label_text)
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.label)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.placeholder)
        self.input_field.setMinimumHeight(35)
        self.input_field.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.input_field)
        
        # Validation feedback
        self.feedback_label = QLabel()
        self.feedback_label.setFont(QFont("Arial", 9))
        self.feedback_label.setMinimumHeight(20)
        self.feedback_label.setVisible(False)
        layout.addWidget(self.feedback_label)
        
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet("""
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #00d4aa;
                background-color: #374151;
            }
            QLineEdit:hover {
                border-color: #666666;
            }
        """)
        
    def on_text_changed(self):
        """Handle text changes with debouncing"""
        self.debounce_timer.start(300)  # 300ms debounce
        
    def perform_validation(self):
        """Perform validation on the input"""
        value = self.input_field.text()
        
        if self.input_type in self.validator.validation_rules:
            state, message = self.validator.validation_rules[self.input_type](value)
        else:
            state, message = ValidationState.VALID, "Valid input"
        
        self.update_validation_state(state, message)
        
    def update_validation_state(self, state, message):
        """Update the validation state and visual feedback"""
        if state == self.current_state and message == self.feedback_label.text():
            return  # No change
            
        self.current_state = state
        
        # Update visual styling
        if state == ValidationState.VALID:
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    color: white;
                    border: 2px solid #00d4aa;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #00d4aa;
                    background-color: #374151;
                }
            """)
            self.feedback_label.setStyleSheet("color: #00d4aa;")
            self.feedback_label.setText("✓ " + message)
            
        elif state == ValidationState.INVALID:
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    color: white;
                    border: 2px solid #ef4444;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #ef4444;
                    background-color: #374151;
                }
            """)
            self.feedback_label.setStyleSheet("color: #ef4444;")
            self.feedback_label.setText("✗ " + message)
            
        elif state == ValidationState.WARNING:
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    color: white;
                    border: 2px solid #f59e0b;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #f59e0b;
                    background-color: #374151;
                }
            """)
            self.feedback_label.setStyleSheet("color: #f59e0b;")
            self.feedback_label.setText("⚠ " + message)
            
        elif state == ValidationState.LOADING:
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    color: white;
                    border: 2px solid #3b82f6;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
            """)
            self.feedback_label.setStyleSheet("color: #3b82f6;")
            self.feedback_label.setText("⏳ " + message)
            
        else:  # EMPTY
            self.input_field.setStyleSheet("""
                QLineEdit {
                    background-color: #2d3748;
                    color: white;
                    border: 2px solid #4a5568;
                    border-radius: 5px;
                    padding: 8px 12px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #00d4aa;
                    background-color: #374151;
                }
            """)
            self.feedback_label.setText("")
        
        # Show/hide feedback label
        self.feedback_label.setVisible(state != ValidationState.EMPTY)
        
        # Emit signal
        self.validation_changed.emit(state, message)
        
    def get_value(self):
        """Get the current input value"""
        return self.input_field.text()
        
    def set_value(self, value):
        """Set the input value"""
        self.input_field.setText(str(value))
        
    def is_valid(self):
        """Check if the input is valid"""
        return self.current_state == ValidationState.VALID
        
    def get_validation_state(self):
        """Get the current validation state"""
        return self.current_state

class CoordinateInput(QWidget):
    """Specialized input for coordinate pairs"""
    
    coordinates_validated = pyqtSignal(bool, str)  # valid, message
    
    def __init__(self, label_text="Coordinates", parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.validator = InputValidator()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the coordinate input UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        self.label = QLabel(self.label_text)
        self.label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.label)
        
        # Coordinate inputs
        coord_layout = QHBoxLayout()
        coord_layout.setSpacing(10)
        
        # Latitude
        self.lat_input = ValidatedInput("Latitude", "latitude", "e.g., 40.7128")
        self.lat_input.validation_changed.connect(self.on_coordinate_changed)
        coord_layout.addWidget(self.lat_input)
        
        # Longitude
        self.lon_input = ValidatedInput("Longitude", "longitude", "e.g., -74.0060")
        self.lon_input.validation_changed.connect(self.on_coordinate_changed)
        coord_layout.addWidget(self.lon_input)
        
        layout.addLayout(coord_layout)
        
        # Combined validation feedback
        self.feedback_label = QLabel()
        self.feedback_label.setFont(QFont("Arial", 9))
        self.feedback_label.setMinimumHeight(20)
        self.feedback_label.setVisible(False)
        layout.addWidget(self.feedback_label)
        
    def on_coordinate_changed(self):
        """Handle coordinate validation changes"""
        lat_value = self.lat_input.get_value()
        lon_value = self.lon_input.get_value()
        
        state, message = self.validator.validate_coordinate_pair(lat_value, lon_value)
        
        # Update feedback
        if state == ValidationState.VALID:
            self.feedback_label.setStyleSheet("color: #00d4aa;")
            self.feedback_label.setText("✓ " + message)
        elif state == ValidationState.INVALID:
            self.feedback_label.setStyleSheet("color: #ef4444;")
            self.feedback_label.setText("✗ " + message)
        elif state == ValidationState.WARNING:
            self.feedback_label.setStyleSheet("color: #f59e0b;")
            self.feedback_label.setText("⚠ " + message)
        else:
            self.feedback_label.setText("")
            
        self.feedback_label.setVisible(state != ValidationState.EMPTY)
        
        # Emit signal
        is_valid = state == ValidationState.VALID
        self.coordinates_validated.emit(is_valid, message)
        
    def get_coordinates(self):
        """Get the coordinate values as (lat, lon) tuple"""
        try:
            lat = float(self.lat_input.get_value())
            lon = float(self.lon_input.get_value())
            return (lat, lon)
        except ValueError:
            return None
            
    def set_coordinates(self, lat, lon):
        """Set the coordinate values"""
        self.lat_input.set_value(lat)
        self.lon_input.set_value(lon)
        
    def is_valid(self):
        """Check if coordinates are valid"""
        return (self.lat_input.is_valid() and 
                self.lon_input.is_valid() and
                self.get_coordinates() is not None)

# Global validator instance
input_validator = InputValidator()
