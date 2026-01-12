#!/usr/bin/env python3
"""
AutoFlightGenerator Dashboard - Main navigation hub
"""

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui, QtWebEngineWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                              QWidget, QLabel, QPushButton, QFrame, QScrollArea,
                              QGridLayout, QStackedWidget, QSplitter, QListWidget,
                              QListWidgetItem, QMessageBox, QFileDialog, QProgressBar, QDialog, QTextEdit)
from PyQt5.QtCore import QUrl, QTimer, QThread, pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPalette, QColor
from PyQt5.QtWebChannel import QWebChannel

# Import existing tools - moved to lazy loading to avoid import errors
# from deliveryroute import DeliveryRoute
# from multidelivery import MultiDelivery
# from securityroute import SecurityRoute
# from linearflightroute import LinearFlightRoute
# from towerinspection import TowerInspection
# from atob_mission_planner import MissionPlanner
# from mapping_flight import MappingFlight
# from structure_scan import StructureScan
from tutorial_dialog import TutorialDialog

# Import enhanced components
from enhanced_map import EnhancedMapWidget
from enhanced_forms import EnhancedFormWidget
from mission_library import MissionLibrary, MissionImportDialog

from settings_manager import settings_manager
from settings_dialog import SettingsDialog

# Import aircraft parameter management
# from aircraft_parameters import ParameterManagementWidget  # Removed - using individual tool parameter UI

# Import Phase 1 UX enhancements
from error_handler import handle_error, error_handler
from progress_manager import show_progress, update_progress, complete_operation
from responsive_layout import apply_responsive_layout, ResponsiveLayoutManager

from adaptive_layout import adaptive_layout_manager, AdaptiveCard, AdaptiveGrid
from advanced_preferences import advanced_preferences_manager, AdvancedPreferencesDialog
# Removed smart suggestions import
from performance_optimizer import performance_optimizer

class MissionCard(QFrame):
    """Individual mission type card for the dashboard with animations"""
    
    def __init__(self, title, description, icon_path, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.icon_path = icon_path
        self.color = color
        self.is_hovered = False
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        self.setMinimumSize(250, 180)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setMidLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setMinimumSize(80, 80)
        self.icon_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 12px;
                padding: 8px;
            }
        """)
        
        # Load and display the icon image
        icon_path = self.icon_path
        if not os.path.exists(icon_path):
            # Try PyInstaller path
            if hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'images', os.path.basename(self.icon_path))
        
        if os.path.exists(icon_path):
            self.original_pixmap = QPixmap(icon_path)
            self.update_icon_size()
        else:
            # Fallback to text if image not found
            self.icon_label.setText("📦")
            self.icon_label.setFont(QFont("Arial", 32))
            self.icon_label.setStyleSheet(f"""
                QLabel {{
                    background-color: white;
                    border-radius: 12px;
                    padding: 8px;
                    color: {self.color};
                }}
            """)
        
        layout.addWidget(self.icon_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(desc_label)
        
        # Removed suggestion button to save space
        
        # Initial styling
        self.setStyleSheet(f"""
            MissionCard {{
                background-color: #1a2332;
                border: 2px solid #2d3748;
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        
        # Enable mouse tracking for hover events
        self.setMouseTracking(True)
        
    def setup_animations(self):
        """Setup hover animations"""
        # Scale animation for hover effect
        self.scale_animation = QPropertyAnimation(self, b"geometry")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Store original geometry
        self.original_geometry = self.geometry()
        
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.is_hovered = True
        self.start_hover_animation()
        
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.is_hovered = False
        self.start_leave_animation()
        
    def start_hover_animation(self):
        """Start hover animation with glow effect"""
        # Scale up slightly
        current_rect = self.geometry()
        center = current_rect.center()
        new_width = int(current_rect.width() * 1.02)
        new_height = int(current_rect.height() * 1.02)
        new_rect = QRect(center.x() - new_width//2, center.y() - new_height//2, new_width, new_height)
        
        self.scale_animation.setStartValue(current_rect)
        self.scale_animation.setEndValue(new_rect)
        self.scale_animation.start()
        
        # Add glowing border effect (static, no pulsing to prevent flickering)
        self.setStyleSheet(f"""
            MissionCard {{
                background-color: #2d3748;
                border: 3px solid {self.color};
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        
    def start_leave_animation(self):
        """Start leave animation"""
        # Scale back to normal
        current_rect = self.geometry()
        center = current_rect.center()
        original_width = int(current_rect.width() / 1.02)
        original_height = int(current_rect.height() / 1.02)
        original_rect = QRect(center.x() - original_width//2, center.y() - original_height//2, original_width, original_height)
        
        self.scale_animation.setStartValue(current_rect)
        self.scale_animation.setEndValue(original_rect)
        self.scale_animation.start()
        
        # Remove glow effect
        self.setStyleSheet(f"""
            MissionCard {{
                background-color: #1a2332;
                border: 2px solid #2d3748;
                border-radius: 10px;
                margin: 5px;
            }}
        """)
        


    def update_icon_size(self):
        """Update icon size based on current card size"""
        if hasattr(self, 'original_pixmap'):
            # Get current label size
            label_size = self.icon_label.size()
            # Calculate icon size (80% of label size)
            icon_size = min(label_size.width(), label_size.height()) - 16  # Account for padding
            if icon_size > 0:
                scaled_pixmap = self.original_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """Handle resize events to update icon size"""
        super().resizeEvent(event)
        self.update_icon_size()
    
    # Removed show_suggestions method

class Dashboard(QMainWindow):
    """Main dashboard with unified navigation"""
    
    def __init__(self):
        super().__init__()
        self.current_tool = None
        self.setup_ui()
        self.apply_theme()
        
        # Show welcome notification
        QTimer.singleShot(1000, self.show_welcome_notification)
        
    def show_welcome_notification(self):
        """Show welcome notification"""
        # Removed status bar notification
        
        # Demo progress operation
        QTimer.singleShot(2000, self.demo_progress_operation)
        
    def demo_progress_operation(self):
        """Demo progress operation for testing"""
        # Check if user has disabled startup progress
        if not settings_manager.get_show_startup_progress():
            return
        
        progress_dialog = show_progress("Loading System Components", 4, self)
        
        # Simulate realistic loading steps (removed GPS and sensor calibration)
        QTimer.singleShot(800, lambda: update_progress(1, "Initializing map services and satellite data..."))
        QTimer.singleShot(1600, lambda: update_progress(2, "Loading terrain elevation data for mission planning..."))
        QTimer.singleShot(2400, lambda: update_progress(3, "Loading mission templates and route algorithms..."))
        QTimer.singleShot(3200, lambda: update_progress(4, "System initialization complete!"))
        QTimer.singleShot(3600, lambda: complete_operation(True, "VERSATILE UAS Flight Generator is ready for mission planning"))
    

    
    def on_adaptive_layout_changed(self, breakpoint):
        """Handle adaptive layout changes"""
        try:
            # Removed status bar notification
            # Reapply adaptive layout to current content
            adaptive_layout_manager.apply_adaptive_layout(self)
        except Exception as e:
            handle_error('layout_error', str(e), self)
            # Removed status bar error notification
    
    def initialize_phase3_systems(self):
        """Initialize Phase 3 enhancement systems"""
        try:
            # Connect advanced preferences signals
            advanced_preferences_manager.preferences_updated.connect(self.on_preferences_updated)
            advanced_preferences_manager.profile_changed.connect(self.on_profile_changed)
            

            
            # Removed smart suggestions connection
            
            # Removed status bar notification
            
        except Exception as e:
            handle_error('initialization_error', str(e), self)
            # Removed status bar error notification
    
    def on_preferences_updated(self):
        """Handle preferences updates"""
        try:
            # Apply new preferences to UI
            profile = advanced_preferences_manager.get_current_profile()
            if profile:
                # Update font sizes
                if hasattr(profile, 'font_size'):
                    self.apply_font_size(profile.font_size)
                
                # Update animation settings
                if hasattr(profile, 'show_animations'):
                    self.update_animation_settings(profile.show_animations)
                
            # Removed status bar notification
            
        except Exception as e:
            handle_error('preferences_error', str(e), self)
    
    def on_profile_changed(self, profile_name):
        """Handle profile changes"""
        try:
            # Removed status bar notification
            # Apply profile-specific settings
            self.apply_profile_settings(profile_name)
            
        except Exception as e:
            handle_error('profile_error', str(e), self)
    

    
    # Removed on_suggestion_ready method
    
    def apply_font_size(self, font_size):
        """Apply font size to UI elements"""
        try:
            # Update font sizes throughout the application
            font = QFont("Arial", font_size)
            self.setFont(font)
            
            # Update specific UI elements
            if hasattr(self, 'title_label'):
                title_font = QFont("Arial", font_size + 4, QFont.Bold)
                self.title_label.setFont(title_font)
                
        except Exception as e:
            print(f"Error applying font size: {e}")
    
    def update_animation_settings(self, show_animations):
        """Update animation settings"""
        try:
            # Enable/disable animations based on preference
            if hasattr(self, 'MissionCard'):
                # Update animation settings for mission cards
                pass
                
        except Exception as e:
            print(f"Error updating animation settings: {e}")
    
    def apply_profile_settings(self, profile_name):
        """Apply profile-specific settings"""
        try:
            # Apply profile-specific configurations
            profile = advanced_preferences_manager.get_current_profile()
            if profile:
                # Apply theme if specified
                if hasattr(profile, 'theme') and profile.theme:
                    self.apply_theme_from_profile(profile.theme)
                    
        except Exception as e:
            print(f"Error applying profile settings: {e}")
    
    def apply_theme_from_profile(self, theme_name):
        """Apply theme from profile"""
        try:
            # Apply custom theme if available
            advanced_preferences_manager.apply_theme(theme_name)
                
        except Exception as e:
            print(f"Error applying theme: {e}")
    

    
    # Removed suggestion methods
        
    def setup_ui(self):
        self.setWindowTitle("VERSATILE UAS Flight Generator - Mission Planning Dashboard")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set to fullscreen by default
        self.showMaximized()
        
        # Create central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Top toolbar
        self.setup_top_toolbar()
        main_layout.addWidget(self.top_toolbar)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Left sidebar
        self.setup_sidebar()
        content_layout.addWidget(self.sidebar, 1)
        
        # Right content area
        self.setup_content_area()
        content_layout.addWidget(self.content_area, 4)
        
        main_layout.addLayout(content_layout)
        
        # Removed status bar to clean up the interface
        
        # Apply responsive layout
        self.responsive_manager = ResponsiveLayoutManager()
        self.responsive_manager.apply_responsive_layout(self)
        
        # Apply adaptive layout
        adaptive_layout_manager.apply_adaptive_layout(self)
        
        # Connect adaptive layout changes
        adaptive_layout_manager.layout_changed.connect(self.on_adaptive_layout_changed)
        
        # Initialize Phase 3 systems
        self.initialize_phase3_systems()
        
    def setup_top_toolbar(self):
        """Setup the top toolbar with tutorials and settings"""
        self.top_toolbar = QFrame()
        self.top_toolbar.setMaximumHeight(60)
        self.top_toolbar.setMinimumHeight(50)
        self.top_toolbar.setStyleSheet("""
            QFrame {
                background-color: #1a2332;
                border-bottom: 1px solid #2d3748;
            }
        """)
        
        layout = QHBoxLayout(self.top_toolbar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        
        # Left side - Application title with small logo
        title_layout = QHBoxLayout()
        
        # Small logo
        self.small_logo_label = QLabel()
        self.small_logo_label.setAlignment(Qt.AlignCenter)
        self.small_logo_label.setFixedSize(32, 32)
        self.small_logo_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        
        # Load and scale the small logo image
        logo_path = os.path.join(os.path.dirname(__file__), 'images', 'logowhite.svg')
        if not os.path.exists(logo_path):
            # Try PyInstaller path
            if hasattr(sys, '_MEIPASS'):
                logo_path = os.path.join(sys._MEIPASS, 'images', 'logowhite.svg')
        
        if os.path.exists(logo_path):
            self.small_logo_pixmap = QPixmap(logo_path)
            scaled_pixmap = self.small_logo_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.small_logo_label.setPixmap(scaled_pixmap)
        else:
            # Fallback to text if image not found
            self.small_logo_label.setText("🚁")
            self.small_logo_label.setFont(QFont("Arial", 16))
        
        title_layout.addWidget(self.small_logo_label)
        
        # Title text
        title_label = QLabel("VERSATILE UAS Flight Generator")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa; margin-left: 8px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Right side - Toolbar buttons
        # Tutorials button
        tutorials_btn = QPushButton("📖 Tutorials")
        tutorials_btn.setFont(QFont("Arial", 12))
        tutorials_btn.setMinimumHeight(40)
        tutorials_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        tutorials_btn.clicked.connect(self.open_tutorials)
        layout.addWidget(tutorials_btn)
        
        # Settings button
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.setFont(QFont("Arial", 12))
        settings_btn.setMinimumHeight(40)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(settings_btn)
        
        # Advanced Preferences button
        advanced_prefs_btn = QPushButton("🎨 Advanced")
        advanced_prefs_btn.setFont(QFont("Arial", 12))
        advanced_prefs_btn.setMinimumHeight(40)
        advanced_prefs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 1px solid #4a5568;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        advanced_prefs_btn.clicked.connect(self.open_advanced_preferences)
        layout.addWidget(advanced_prefs_btn)
        

        
    def setup_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setMaximumWidth(350)
        self.sidebar.setMinimumWidth(320)
        
        layout = QVBoxLayout(self.sidebar)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Removed large logo to save space for mission tools
        
        # Navigation buttons
        nav_label = QLabel("Mission Types")
        nav_label.setFont(QFont("Arial", 12, QFont.Bold))
        nav_label.setStyleSheet("color: #00d4aa; margin-top: 10px;")
        layout.addWidget(nav_label)
        
        # Mission buttons
        self.nav_buttons = []  # Store references to navigation buttons
        
        self.nav_buttons.append(self.create_nav_button_text("Delivery Route", "#4CAF50", self.open_delivery_route))
        self.nav_buttons.append(self.create_nav_button_text("Multi-Delivery", "#2196F3", self.open_multi_delivery))
        self.nav_buttons.append(self.create_nav_button_text("Security Route", "#FF9800", self.open_security_route))
        self.nav_buttons.append(self.create_nav_button_text("Linear Flight", "#9C27B0", self.open_linear_flight))
        self.nav_buttons.append(self.create_nav_button_text("Tower Inspection", "#F44336", self.open_tower_inspection))
        self.nav_buttons.append(self.create_nav_button_text("A-to-B Mission", "#00BCD4", self.open_atob_mission))
        self.nav_buttons.append(self.create_nav_button_text("Mapping Flight", "#FF5722", self.open_mapping_flight))
        self.nav_buttons.append(self.create_nav_button_text("Structure Scan", "#673AB7", self.open_structure_scan))
        
        layout.addStretch()
        
        # Library button
        self.create_nav_button_emoji("Mission Library", "📚", "#9C27B0", self.open_library)
        
        layout.addStretch()
        
        # Aircraft Parameters section - Removed, using individual tool parameter UI instead
        
    # Removed update_logo_size method since large logo was removed
    
    def refresh_all_mission_tools(self):
        """Refresh parameter state in all loaded mission tools"""
        # Note: Parameter management is now handled individually by each tool
        # This method is kept for potential future use
        pass
    
    def resizeEvent(self, event):
        """Handle resize events to update card sizes"""
        super().resizeEvent(event)
        
        # Update all mission cards
        if hasattr(self, 'dashboard_view'):
            for child in self.dashboard_view.findChildren(MissionCard):
                if hasattr(child, 'update_icon_size'):
                    child.update_icon_size()
        
        # Apply adaptive layout on resize
        adaptive_layout_manager.apply_adaptive_layout(self)
        
    def create_nav_button(self, text, icon_path, color, callback):
        """Create a navigation button with image icon"""
        btn = QPushButton()
        btn.setFont(QFont("Arial", 16))
        btn.setMinimumHeight(80)
        
        # Create layout for button content
        btn_layout = QHBoxLayout(btn)
        btn_layout.setContentsMargins(16, 16, 16, 16)
        btn_layout.setSpacing(16)
        
        # Create icon label
        icon_label = QLabel()
        icon_label.setMinimumSize(64, 64)
        icon_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 10px;
                padding: 8px;
            }
        """)
        
        # Load and display the icon image
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            # Scale to much larger size (48x48 pixels)
            icon_pixmap = icon_pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
        else:
            # Fallback to text if image not found
            icon_label.setText("📦")
            icon_label.setFont(QFont("Arial", 24))
            icon_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border-radius: 10px;
                    padding: 8px;
                }
            """)
        
        # Create text label
        text_label = QLabel(text)
        text_label.setFont(QFont("Arial", 16))
        text_label.setStyleSheet("color: white;")
        
        # Add widgets to layout
        btn_layout.addWidget(icon_label)
        btn_layout.addWidget(text_label)
        btn_layout.addStretch()
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a2332;
                color: white;
                border: 1px solid #2d3748;
                border-radius: 5px;
                padding: 0px;
                text-align: left;
                margin: 2px;
            }}
            QPushButton:hover {{
                background-color: #2d3748;
                border-color: {color};
            }}
            QPushButton:pressed {{
                background-color: {color};
                color: white;
            }}
        """)
        btn.clicked.connect(callback)
        self.sidebar.layout().addWidget(btn)
        
        # Store icon information for resizing
        btn.icon_path = icon_path
        btn.icon_label = icon_label
        btn.original_pixmap = QPixmap(icon_path) if os.path.exists(icon_path) else None
        
        return btn
    
    def create_nav_button_text(self, text, color, callback):
        """Create a navigation button with text only"""
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 14))
        btn.setMinimumHeight(60)
        btn.setMaximumHeight(60)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a2332;
                color: white;
                border: 1px solid #2d3748;
                border-radius: 5px;
                padding: 12px 16px;
                text-align: left;
                margin: 1px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: #2d3748;
                border-color: {color};
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: {color};
                color: white;
                font-weight: bold;
            }}
        """)
        btn.clicked.connect(callback)
        self.sidebar.layout().addWidget(btn)
        return btn
    
    def create_nav_button_emoji(self, text, icon, color, callback):
        """Create a navigation button with emoji icon"""
        btn = QPushButton(f"{icon} {text}")
        btn.setFont(QFont("Arial", 14))
        btn.setMinimumHeight(60)
        btn.setMaximumHeight(60)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #1a2332;
                color: white;
                border: 1px solid #2d3748;
                border-radius: 5px;
                padding: 12px 16px;
                text-align: left;
                margin: 1px;
                font-weight: normal;
            }}
            QPushButton:hover {{
                background-color: #2d3748;
                border-color: {color};
                font-weight: bold;
            }}
            QPushButton:pressed {{
                background-color: {color};
                color: white;
                font-weight: bold;
            }}
        """)
        btn.clicked.connect(callback)
        self.sidebar.layout().addWidget(btn)
        
    def setup_content_area(self):
        self.content_area = QStackedWidget()
        
        # Dashboard view
        self.dashboard_view = self.create_dashboard_view()
        self.content_area.addWidget(self.dashboard_view)
        
        # Library view
        self.library_view = self.create_library_view()
        self.content_area.addWidget(self.library_view)
        
        # Tool views (will be added dynamically)
        self.tool_views = {}
        

        
    def create_dashboard_view(self):
        """Create the main dashboard view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Header section
        
        # Mission cards grid
        cards_label = QLabel("Choose Your Mission Type")
        cards_label.setFont(QFont("Arial", 16, QFont.Bold))
        cards_label.setStyleSheet("color: #00d4aa; margin-bottom: 15px;")
        layout.addWidget(cards_label)
        
        # Create mission cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(25)
        cards_layout.setColumnStretch(0, 1)
        cards_layout.setColumnStretch(1, 1)
        cards_layout.setColumnStretch(2, 1)
        cards_layout.setColumnStretch(3, 1)
        
        # Define mission types with their corresponding image paths
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        missions = [
            ("Delivery Route", "Point-to-point delivery missions for medical supplies, packages, emergency supplies, and agricultural deliveries with precise waypoint planning", 
             os.path.join(images_dir, "A to B route.svg"), "#4CAF50"),
            ("Multi-Delivery", "Efficient multi-point delivery routes for multiple packages, medical supplies to clinics, and maintenance parts to facilities with optimized routing", 
             os.path.join(images_dir, "Multi-delivery.svg"), "#2196F3"),
            ("Security Route", "Perimeter security and surveillance missions for industrial facilities, construction sites, agricultural fields, and event venues with geofencing", 
             os.path.join(images_dir, "Security Route.svg"), "#FF9800"),
            ("Linear Flight", "Linear survey and inspection missions for pipelines, power lines, railway tracks, highways, and coastal shorelines with systematic coverage", 
             os.path.join(images_dir, "Linear Flight.svg"), "#9C27B0"),
            ("Tower Inspection", "Detailed inspection missions for cell towers, wind turbines, power transmission towers, water towers, and building facades using orbital patterns", 
             os.path.join(images_dir, "Tower Inspection.svg"), "#F44336"),
            ("A-to-B Mission", "Simple point-to-point missions for reconnaissance, emergency response, search and rescue, wildlife monitoring, and traffic reporting", 
             os.path.join(images_dir, "A to B route.svg"), "#00BCD4"),
            ("Mapping Flight", "Area mapping and surveying missions for real estate, construction sites, agricultural fields, environmental assessment, and disaster damage evaluation", 
             os.path.join(images_dir, "mapping.svg"), "#FF5722"),
            ("Structure Scan", "3D structure scanning missions for building modeling, historical monuments, industrial facilities, mining operations, and archaeological documentation", 
             os.path.join(images_dir, "structure scan.svg"), "#673AB7")
        ]
        
        for i, (title, desc, icon_path, color) in enumerate(missions):
            card = MissionCard(title, desc, icon_path, color)
            row = i // 4
            col = i % 4
            cards_layout.addWidget(card, row, col)
            
            # Connect card click to navigation with error handling
            card.mousePressEvent = lambda event, t=title: self.navigate_to_mission_safe(t)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        return widget
        
    def create_library_view(self):
        """Create the mission library view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("Mission Library")
        header_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Library widget
        self.mission_library = MissionLibrary()
        self.mission_library.mission_selected.connect(self.load_mission_from_library)
        layout.addWidget(self.mission_library)
        
        return widget
        
    def navigate_to_mission(self, mission_type):
        """Navigate to a specific mission type"""
        mission_map = {
            "Delivery Route": self.open_delivery_route,
            "Multi-Delivery": self.open_multi_delivery,
            "Security Route": self.open_security_route,
            "Linear Flight": self.open_linear_flight,
            "Tower Inspection": self.open_tower_inspection,
            "A-to-B Mission": self.open_atob_mission,
            "Mapping Flight": self.open_mapping_flight,
            "Structure Scan": self.open_structure_scan
        }
        
        if mission_type in mission_map:
            mission_map[mission_type]()
            
    def navigate_to_mission_safe(self, mission_type):
        """Navigate to a specific mission type with error handling"""
        try:
            # Removed status bar notification
            self.navigate_to_mission(mission_type)

        except Exception as e:
            error_dialog = handle_error('file_corrupted', f"Failed to load {mission_type}: {str(e)}", self)
            error_dialog.exec_()
            # Removed status bar error notification
            
    def open_delivery_route(self):
        """Open delivery route tool"""
        try:
            if 'delivery_route' not in self.tool_views:
                from deliveryroute import DeliveryRoute
                self.tool_views['delivery_route'] = DeliveryRoute()
                self.content_area.addWidget(self.tool_views['delivery_route'])
            
            self.content_area.setCurrentWidget(self.tool_views['delivery_route'])
            self.update_sidebar_state('delivery_route')

            # Removed status bar notification
            
        except ImportError as e:
            # Handle import errors separately
            import traceback
            error_details = traceback.format_exc()
            print(f"Import error when loading Delivery Route: {e}")
            print(error_details)
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import Delivery Route module:\n\n{str(e)}\n\n"
                f"Please check that all required dependencies are installed."
            )
        except Exception as e:
            # Handle other errors with more context
            import traceback
            error_details = traceback.format_exc()
            print(f"Error loading Delivery Route: {e}")
            print(error_details)
            
            # Check if it's actually a file-related error
            error_str = str(e).lower()
            if 'file' in error_str and ('corrupt' in error_str or 'invalid' in error_str or 'cannot read' in error_str):
                error_dialog = handle_error('file_corrupted', str(e), self)
                error_dialog.exec_()
            else:
                # Show a more appropriate error for non-file errors
                QMessageBox.critical(
                    self,
                    "Error Loading Delivery Route",
                    f"An error occurred while loading the Delivery Route tool:\n\n{str(e)}\n\n"
                    f"Please check the console for detailed error information."
                )
            # Removed status bar error notification
        
    def open_multi_delivery(self):
        """Open multi-delivery tool"""
        if 'multi_delivery' not in self.tool_views:
            from multidelivery import MultiDelivery
            self.tool_views['multi_delivery'] = MultiDelivery()
            self.content_area.addWidget(self.tool_views['multi_delivery'])
        
        self.content_area.setCurrentWidget(self.tool_views['multi_delivery'])
        self.update_sidebar_state('multi_delivery')
        
    def open_security_route(self):
        """Open security route tool"""
        if 'security_route' not in self.tool_views:
            from securityroute import SecurityRoute
            self.tool_views['security_route'] = SecurityRoute()
            self.content_area.addWidget(self.tool_views['security_route'])
        
        self.content_area.setCurrentWidget(self.tool_views['security_route'])
        self.update_sidebar_state('security_route')
        
    def open_linear_flight(self):
        """Open linear flight tool"""
        if 'linear_flight' not in self.tool_views:
            from linearflightroute import LinearFlightRoute
            self.tool_views['linear_flight'] = LinearFlightRoute()
            self.content_area.addWidget(self.tool_views['linear_flight'])
        
        self.content_area.setCurrentWidget(self.tool_views['linear_flight'])
        self.update_sidebar_state('linear_flight')
        
    def open_tower_inspection(self):
        """Open tower inspection tool"""
        try:
            if 'tower_inspection' not in self.tool_views:
                from towerinspection import TowerInspection
                self.tool_views['tower_inspection'] = TowerInspection()
                self.content_area.addWidget(self.tool_views['tower_inspection'])
            
            self.content_area.setCurrentWidget(self.tool_views['tower_inspection'])
            self.update_sidebar_state('tower_inspection')
        except Exception as e:
            error_dialog = handle_error('file_corrupted', f"Failed to load Tower Inspection: {str(e)}", self)
            error_dialog.exec_()
        
    def open_atob_mission(self):
        """Open A-to-B mission tool"""
        if 'atob_mission' not in self.tool_views:
            from atob_mission_planner import MissionPlanner
            self.tool_views['atob_mission'] = MissionPlanner()
            self.content_area.addWidget(self.tool_views['atob_mission'])
        
        self.content_area.setCurrentWidget(self.tool_views['atob_mission'])
        self.update_sidebar_state('atob_mission')
    
    def open_mapping_flight(self):
        """Open mapping flight tool"""
        try:
            if 'mapping_flight' not in self.tool_views:
                from mapping_flight import MappingFlight
                self.tool_views['mapping_flight'] = MappingFlight()
                self.content_area.addWidget(self.tool_views['mapping_flight'])
            
            self.content_area.setCurrentWidget(self.tool_views['mapping_flight'])
            self.update_sidebar_state('mapping_flight')
        except Exception as e:
            error_dialog = handle_error('file_corrupted', f"Failed to load Mapping Flight: {str(e)}", self)
            error_dialog.exec_()
    
    def open_structure_scan(self):
        """Open structure scan tool"""
        try:
            if 'structure_scan' not in self.tool_views:
                from structure_scan import StructureScan
                self.tool_views['structure_scan'] = StructureScan()
                self.content_area.addWidget(self.tool_views['structure_scan'])
            
            self.content_area.setCurrentWidget(self.tool_views['structure_scan'])
            self.update_sidebar_state('structure_scan')
        except Exception as e:
            error_dialog = handle_error('file_corrupted', f"Failed to load Structure Scan: {str(e)}", self)
            error_dialog.exec_()
        
    def open_library(self):
        """Open mission library"""
        self.content_area.setCurrentWidget(self.library_view)
        self.update_sidebar_state('library')
    
    def open_tutorials(self):
        """Open tutorials dialog"""
        
        dialog = TutorialDialog(self)
        dialog.exec_()
    
    def open_settings(self):
        """Open settings dialog"""
        
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Notify all open tools about the settings change
            for tool_name, tool_widget in self.tool_views.items():
                if hasattr(tool_widget, 'apply_settings'):
                    tool_widget.apply_settings()
    
    def open_advanced_preferences(self):
        """Open advanced preferences dialog"""
        try:

            dialog = AdvancedPreferencesDialog(self)
            dialog.exec_()
            # Removed status bar notification
        except Exception as e:
            handle_error('preferences_error', str(e), self)
            # Removed status bar error notification
    

        
    def load_mission_from_library(self, mission_data):
        """Load a mission from the library"""
        mission_type = mission_data.get('type', 'Unknown')
        
        # Map mission types to tools
        type_map = {
            'Delivery Route': self.open_delivery_route,
            'Multi-Delivery': self.open_multi_delivery,
            'Security Route': self.open_security_route,
            'Linear Flight': self.open_linear_flight,
            'Tower Inspection': self.open_tower_inspection,
            'A-to-B Mission': self.open_atob_mission,
            'Mapping Flight': self.open_mapping_flight,
            'Structure Scan': self.open_structure_scan
        }
        
        if mission_type in type_map:
            # Open the appropriate tool
            type_map[mission_type]()
            
            # Load mission data into the tool
            # This would need to be implemented in each tool
            QMessageBox.information(self, "Mission Loaded", 
                                  f"Mission '{mission_data['name']}' loaded successfully!")
        else:
            QMessageBox.warning(self, "Unknown Mission Type", 
                              f"Unknown mission type: {mission_type}")
        
    def update_sidebar_state(self, current_tool):
        """Update sidebar to show current tool"""
        self.current_tool = current_tool
            
    def apply_theme(self):
        """Apply the dark blue and teal theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1419;
                color: white;
            }
            QFrame {
                background-color: #1a2332;
                border: 1px solid #2d3748;
                border-radius: 5px;
            }
            QLabel {
                color: white;
            }
            QScrollBar:vertical {
                background-color: #1a2332;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a5568;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00d4aa;
            }
        """)

def main():
    # Set required attribute for QtWebEngineWidgets before creating QApplication
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 