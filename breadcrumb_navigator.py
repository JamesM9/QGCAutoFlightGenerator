#!/usr/bin/env python3
"""
Breadcrumb Navigation System
Provides visual navigation trails and clickable navigation history
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                              QFrame, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

class BreadcrumbNavigator(QWidget):
    """Smart breadcrumb navigation with clickable history"""
    
    # Signals
    navigation_requested = pyqtSignal(str)  # Emits screen name to navigate to
    back_requested = pyqtSignal()
    forward_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.navigation_history = []
        self.current_index = -1
        self.max_history = 10
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """Setup the breadcrumb UI"""
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(8)
        
        # Back/Forward buttons
        self.back_btn = QToolButton()
        self.back_btn.setIcon(QIcon("◀"))
        self.back_btn.setToolTip("Go Back (Alt+Left)")
        self.back_btn.clicked.connect(self.go_back)
        self.back_btn.setEnabled(False)
        layout.addWidget(self.back_btn)
        
        self.forward_btn = QToolButton()
        self.forward_btn.setIcon(QIcon("▶"))
        self.forward_btn.setToolTip("Go Forward (Alt+Right)")
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_btn.setEnabled(False)
        layout.addWidget(self.forward_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Breadcrumb container
        self.breadcrumb_container = QWidget()
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self.breadcrumb_layout.setSpacing(5)
        layout.addWidget(self.breadcrumb_container)
        
        # Add stretch to push breadcrumbs to left
        layout.addStretch()
        
        # Current location indicator
        self.location_label = QLabel("Dashboard")
        self.location_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.location_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(self.location_label)
        
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet("""
            BreadcrumbNavigator {
                background-color: #1a2332;
                border-bottom: 1px solid #2d3748;
            }
            QToolButton {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-size: 12px;
                min-width: 25px;
                min-height: 25px;
            }
            QToolButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QToolButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QToolButton:disabled {
                background-color: #1a2332;
                color: #666666;
                border-color: #2d3748;
            }
            QFrame {
                background-color: #4a5568;
            }
        """)
        
    def add_to_history(self, screen_name, screen_data=None):
        """Add a new screen to navigation history"""
        # Remove any forward history if we're not at the end
        if self.current_index < len(self.navigation_history) - 1:
            self.navigation_history = self.navigation_history[:self.current_index + 1]
        
        # Add new entry
        entry = {
            "name": screen_name,
            "data": screen_data or {},
            "timestamp": QTimer().remainingTime()
        }
        
        self.navigation_history.append(entry)
        
        # Limit history size
        if len(self.navigation_history) > self.max_history:
            self.navigation_history.pop(0)
        
        self.current_index = len(self.navigation_history) - 1
        self.update_breadcrumbs()
        self.update_navigation_buttons()
        
    def update_breadcrumbs(self):
        """Update the breadcrumb display"""
        # Clear existing breadcrumbs
        for i in reversed(range(self.breadcrumb_layout.count())):
            child = self.breadcrumb_layout.itemAt(i).widget()
            if child:
                child.deleteLater()
        
        # Add breadcrumbs for current path
        if len(self.navigation_history) <= 1:
            return
            
        for i, entry in enumerate(self.navigation_history[:-1]):  # Exclude current
            # Breadcrumb item
            crumb = QPushButton(entry["name"])
            crumb.setFont(QFont("Arial", 9))
            crumb.setCursor(Qt.PointingHandCursor)
            crumb.clicked.connect(lambda checked, idx=i: self.navigate_to_index(idx))
            self.breadcrumb_layout.addWidget(crumb)
            
            # Separator
            if i < len(self.navigation_history) - 2:
                sep = QLabel(">")
                sep.setFont(QFont("Arial", 9))
                sep.setStyleSheet("color: #666666;")
                self.breadcrumb_layout.addWidget(sep)
        
        # Update location label
        if self.navigation_history:
            current = self.navigation_history[-1]
            self.location_label.setText(current["name"])
            
    def update_navigation_buttons(self):
        """Update back/forward button states"""
        self.back_btn.setEnabled(self.current_index > 0)
        self.forward_btn.setEnabled(self.current_index < len(self.navigation_history) - 1)
        
    def navigate_to_index(self, index):
        """Navigate to a specific history index"""
        if 0 <= index < len(self.navigation_history):
            self.current_index = index
            entry = self.navigation_history[index]
            self.navigation_requested.emit(entry["name"])
            self.update_breadcrumbs()
            self.update_navigation_buttons()
            
    def go_back(self):
        """Navigate back in history"""
        if self.current_index > 0:
            self.current_index -= 1
            entry = self.navigation_history[self.current_index]
            self.navigation_requested.emit(entry["name"])
            self.update_breadcrumbs()
            self.update_navigation_buttons()
            
    def go_forward(self):
        """Navigate forward in history"""
        if self.current_index < len(self.navigation_history) - 1:
            self.current_index += 1
            entry = self.navigation_history[self.current_index]
            self.navigation_requested.emit(entry["name"])
            self.update_breadcrumbs()
            self.update_navigation_buttons()
            
    def get_current_screen(self):
        """Get current screen name"""
        if self.navigation_history:
            return self.navigation_history[-1]["name"]
        return "Dashboard"
        
    def clear_history(self):
        """Clear navigation history"""
        self.navigation_history = []
        self.current_index = -1
        self.update_breadcrumbs()
        self.update_navigation_buttons()
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Left and event.modifiers() == Qt.AltModifier:
            self.go_back()
        elif event.key() == Qt.Key_Right and event.modifiers() == Qt.AltModifier:
            self.go_forward()
        else:
            super().keyPressEvent(event)
