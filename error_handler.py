#!/usr/bin/env python3
"""
Enhanced Error Handling System
Provides user-friendly error messages and helpful suggestions
"""

import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTextEdit, QFrame, QScrollArea,
                              QMessageBox, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor

class ErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self):
        self.error_log = []
        self.user_friendly_messages = {
            'connection_error': {
                'title': 'Connection Error',
                'message': 'Unable to connect to map service. Please check your internet connection.',
                'suggestions': [
                    'Check your internet connection',
                    'Verify firewall settings',
                    'Try again in a few moments'
                ],
                'icon': '🌐'
            },
            'invalid_coordinates': {
                'title': 'Invalid Coordinates',
                'message': 'The coordinates you entered are invalid. Please use decimal format.',
                'suggestions': [
                    'Use decimal format: 40.7128, -74.0060',
                    'Ensure latitude is between -90 and 90',
                    'Ensure longitude is between -180 and 180'
                ],
                'icon': '📍'
            },
            'terrain_data_unavailable': {
                'title': 'Terrain Data Unavailable',
                'message': 'Terrain data is not available for this area. Mission planning may be limited.',
                'suggestions': [
                    'Try a different location',
                    'Use manual altitude settings',
                    'Check if the area is covered by terrain data'
                ],
                'icon': '🏔️'
            },
            'file_corrupted': {
                'title': 'File Corrupted',
                'message': 'The mission file appears to be corrupted. Please try importing a different file.',
                'suggestions': [
                    'Try a different mission file',
                    'Check if the file was properly saved',
                    'Create a new mission from scratch'
                ],
                'icon': '📄'
            },
            'permission_denied': {
                'title': 'Permission Denied',
                'message': 'You don\'t have permission to access this file or location.',
                'suggestions': [
                    'Check file permissions',
                    'Try saving to a different location',
                    'Run the application as administrator'
                ],
                'icon': '🔒'
            },
            'insufficient_memory': {
                'title': 'Insufficient Memory',
                'message': 'Not enough memory available to complete this operation.',
                'suggestions': [
                    'Close other applications',
                    'Reduce the size of your mission area',
                    'Restart the application'
                ],
                'icon': '💾'
            },
            'gps_signal_lost': {
                'title': 'GPS Signal Lost',
                'message': 'Unable to get current GPS location. Please check your GPS settings.',
                'suggestions': [
                    'Check GPS hardware connection',
                    'Move to an area with better GPS signal',
                    'Enter coordinates manually'
                ],
                'icon': '📡'
            },
            'battery_low': {
                'title': 'Low Battery Warning',
                'message': 'Battery level is low. Consider charging before flight.',
                'suggestions': [
                    'Charge the battery fully',
                    'Check battery health',
                    'Plan shorter missions'
                ],
                'icon': '🔋'
            },
            'weather_warning': {
                'title': 'Weather Warning',
                'message': 'Current weather conditions may affect flight safety.',
                'suggestions': [
                    'Check wind speed and direction',
                    'Monitor weather forecasts',
                    'Consider postponing the mission'
                ],
                'icon': '🌤️'
            },
            'no_fly_zone': {
                'title': 'No-Fly Zone Detected',
                'message': 'The planned route enters a restricted airspace.',
                'suggestions': [
                    'Choose a different route',
                    'Check local airspace regulations',
                    'Contact authorities for permission'
                ],
                'icon': '🚫'
            }
        }
        
    def handle_error(self, error_type, details=None, parent=None):
        """Handle errors with user-friendly messages and suggestions"""
        error_info = self.user_friendly_messages.get(error_type, {
            'title': 'Unknown Error',
            'message': 'An unexpected error occurred.',
            'suggestions': ['Try again', 'Check your input', 'Contact support'],
            'icon': '❓'
        })
        
        # Log the error
        self.log_error(error_type, details)
        
        # Create and show error dialog
        error_dialog = ErrorDialog(error_info, details, parent)
        return error_dialog
        
    def log_error(self, error_type, details=None):
        """Log error for debugging purposes"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        error_entry = {
            'timestamp': timestamp,
            'type': error_type,
            'details': details
        }
        
        self.error_log.append(error_entry)
        
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
            
    def get_error_log(self):
        """Get the error log for debugging"""
        return self.error_log
        
    def clear_error_log(self):
        """Clear the error log"""
        self.error_log = []

class ErrorDialog(QDialog):
    """User-friendly error dialog with suggestions"""
    
    def __init__(self, error_info, details=None, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        self.details = details
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the error dialog UI"""
        self.setWindowTitle(self.error_info['title'])
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #1a2332;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QTextEdit {
                background-color: #2d3748;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header with icon and title
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel(self.error_info['icon'])
        icon_label.setFont(QFont("Arial", 32))
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Title and message
        text_layout = QVBoxLayout()
        
        title_label = QLabel(self.error_info['title'])
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa;")
        text_layout.addWidget(title_label)
        
        message_label = QLabel(self.error_info['message'])
        message_label.setWordWrap(True)
        message_label.setFont(QFont("Arial", 12))
        text_layout.addWidget(message_label)
        
        header_layout.addLayout(text_layout)
        layout.addLayout(header_layout)
        
        # Suggestions section
        suggestions_label = QLabel("Suggestions:")
        suggestions_label.setFont(QFont("Arial", 12, QFont.Bold))
        suggestions_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(suggestions_label)
        
        # Suggestions list
        suggestions_frame = QFrame()
        suggestions_frame.setStyleSheet("""
            QFrame {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        suggestions_layout = QVBoxLayout(suggestions_frame)
        suggestions_layout.setSpacing(8)
        
        for i, suggestion in enumerate(self.error_info['suggestions'], 1):
            suggestion_label = QLabel(f"{i}. {suggestion}")
            suggestion_label.setFont(QFont("Arial", 11))
            suggestions_layout.addWidget(suggestion_label)
            
        layout.addWidget(suggestions_frame)
        
        # Technical details (collapsible)
        if self.details:
            self.setup_technical_details(layout)
            
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Retry button
        retry_btn = QPushButton("🔄 Retry")
        retry_btn.clicked.connect(self.retry_operation)
        button_layout.addWidget(retry_btn)
        
        # Help button
        help_btn = QPushButton("❓ Get Help")
        help_btn.clicked.connect(self.show_help)
        button_layout.addWidget(help_btn)
        
        # Close button
        close_btn = QPushButton("✕ Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def setup_technical_details(self, main_layout):
        """Setup collapsible technical details section"""
        # Details button
        details_btn = QPushButton("🔧 Show Technical Details")
        details_btn.setCheckable(True)
        details_btn.clicked.connect(self.toggle_details)
        main_layout.addWidget(details_btn)
        
        # Details text area (initially hidden)
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setPlainText(str(self.details))
        self.details_text.setVisible(False)
        main_layout.addWidget(self.details_text)
        
        self.details_btn = details_btn
        
    def toggle_details(self):
        """Toggle technical details visibility"""
        is_visible = self.details_text.isVisible()
        self.details_text.setVisible(not is_visible)
        
        if is_visible:
            self.details_btn.setText("🔧 Show Technical Details")
            self.adjustSize()
        else:
            self.details_btn.setText("🔧 Hide Technical Details")
            self.adjustSize()
            
    def retry_operation(self):
        """Retry the failed operation"""
        # This would be connected to the actual retry logic
        QMessageBox.information(self, "Retry", "Retry functionality would be implemented here.")
        
    def show_help(self):
        """Show help documentation"""
        help_text = f"""
        Help for: {self.error_info['title']}
        
        {self.error_info['message']}
        
        Common solutions:
        """
        
        for suggestion in self.error_info['suggestions']:
            help_text += f"\n• {suggestion}"
            
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Help")
        help_dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(help_dialog)
        
        help_text_edit = QTextEdit()
        help_text_edit.setPlainText(help_text)
        help_text_edit.setReadOnly(True)
        layout.addWidget(help_text_edit)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.exec_()

# Global error handler instance
error_handler = ErrorHandler()

def handle_error(error_type, details=None, parent=None):
    """Global function to handle errors"""
    return error_handler.handle_error(error_type, details, parent)
