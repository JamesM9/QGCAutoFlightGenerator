#!/usr/bin/env python3
"""
Advanced User Preferences System
Provides profile management, custom themes, and personalized settings
"""

import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QSpinBox, QCheckBox,
                              QTabWidget, QFrame, QLineEdit, QTextEdit,
                              QListWidget, QListWidgetItem, QDialog,
                              QDialogButtonBox, QFormLayout, QGroupBox,
                              QColorDialog, QSlider, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QPalette

class UserProfile:
    """User profile with personalized settings"""
    
    def __init__(self, name="Default", email=""):
        self.name = name
        self.email = email
        self.created_date = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        
        # UI Preferences
        self.theme = "dark_blue_teal"
        self.font_size = 12
        self.animation_speed = "normal"  # slow, normal, fast
        self.show_animations = True
        self.show_tooltips = True
        self.auto_save_interval = 5  # minutes
        
        # Mission Preferences
        self.default_altitude = 100
        self.default_waypoint_interval = 50
        self.default_geofence_buffer = 100
        self.auto_terrain_check = True
        self.show_safety_warnings = True
        self.confirm_dangerous_operations = True
        
        # Performance Preferences
        self.map_quality = "high"  # low, medium, high
        self.cache_size_limit = 500  # MB
        self.auto_cleanup_cache = True
        self.background_processing = True
        
        # Accessibility
        self.high_contrast_mode = False
        self.large_text_mode = False
        self.keyboard_shortcuts_enabled = True
        self.screen_reader_support = False
        
    def to_dict(self):
        """Convert profile to dictionary"""
        return {
            'name': self.name,
            'email': self.email,
            'created_date': self.created_date,
            'last_modified': self.last_modified,
            'theme': self.theme,
            'font_size': self.font_size,
            'animation_speed': self.animation_speed,
            'show_animations': self.show_animations,
            'show_tooltips': self.show_tooltips,
            'auto_save_interval': self.auto_save_interval,
            'default_altitude': self.default_altitude,
            'default_waypoint_interval': self.default_waypoint_interval,
            'default_geofence_buffer': self.default_geofence_buffer,
            'auto_terrain_check': self.auto_terrain_check,
            'show_safety_warnings': self.show_safety_warnings,
            'confirm_dangerous_operations': self.confirm_dangerous_operations,
            'map_quality': self.map_quality,
            'cache_size_limit': self.cache_size_limit,
            'auto_cleanup_cache': self.auto_cleanup_cache,
            'background_processing': self.background_processing,
            'high_contrast_mode': self.high_contrast_mode,
            'large_text_mode': self.large_text_mode,
            'keyboard_shortcuts_enabled': self.keyboard_shortcuts_enabled,
            'screen_reader_support': self.screen_reader_support
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create profile from dictionary"""
        profile = cls(data.get('name', 'Default'), data.get('email', ''))
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        return profile

class CustomTheme:
    """Custom theme definition"""
    
    def __init__(self, name="Custom Theme"):
        self.name = name
        self.primary_color = "#00d4aa"
        self.secondary_color = "#1a2332"
        self.background_color = "#0f1419"
        self.surface_color = "#1a2332"
        self.border_color = "#2d3748"
        self.text_color = "#ffffff"
        self.accent_color = "#00d4aa"
        self.warning_color = "#f59e0b"
        self.error_color = "#ef4444"
        self.success_color = "#10b981"
        
    def to_dict(self):
        """Convert theme to dictionary"""
        return {
            'name': self.name,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'background_color': self.background_color,
            'surface_color': self.surface_color,
            'border_color': self.border_color,
            'text_color': self.text_color,
            'accent_color': self.accent_color,
            'warning_color': self.warning_color,
            'error_color': self.error_color,
            'success_color': self.success_color
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create theme from dictionary"""
        theme = cls(data.get('name', 'Custom Theme'))
        for key, value in data.items():
            if hasattr(theme, key):
                setattr(theme, key, value)
        return theme

class AdvancedPreferencesManager(QObject):
    """Manages advanced user preferences and profiles"""
    
    profile_changed = pyqtSignal(str)  # Emits profile name
    theme_changed = pyqtSignal(str)    # Emits theme name
    preferences_updated = pyqtSignal() # General preferences update
    
    def __init__(self, profiles_file="user_profiles.json", themes_file="custom_themes.json"):
        super().__init__()
        self.profiles_file = profiles_file
        self.themes_file = themes_file
        self.profiles = {}
        self.custom_themes = {}
        self.current_profile = None
        self.current_theme = None
        
        self.load_profiles()
        self.load_themes()
        self.setup_default_profile()
        
    def load_profiles(self):
        """Load user profiles from file"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    for profile_name, profile_data in data.items():
                        self.profiles[profile_name] = UserProfile.from_dict(profile_data)
        except Exception as e:
            print(f"Error loading profiles: {e}")
    
    def save_profiles(self):
        """Save user profiles to file"""
        try:
            data = {}
            for name, profile in self.profiles.items():
                data[name] = profile.to_dict()
            
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def load_themes(self):
        """Load custom themes from file"""
        try:
            if os.path.exists(self.themes_file):
                with open(self.themes_file, 'r') as f:
                    data = json.load(f)
                    for theme_name, theme_data in data.items():
                        self.custom_themes[theme_name] = CustomTheme.from_dict(theme_data)
        except Exception as e:
            print(f"Error loading themes: {e}")
    
    def save_themes(self):
        """Save custom themes to file"""
        try:
            data = {}
            for name, theme in self.custom_themes.items():
                data[name] = theme.to_dict()
            
            with open(self.themes_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving themes: {e}")
    
    def setup_default_profile(self):
        """Setup default profile if none exists"""
        if not self.profiles:
            default_profile = UserProfile("Default", "")
            self.profiles["Default"] = default_profile
            self.current_profile = default_profile
            self.save_profiles()
        else:
            self.current_profile = list(self.profiles.values())[0]
    
    def create_profile(self, name, email=""):
        """Create a new user profile"""
        if name in self.profiles:
            return False  # Profile already exists
        
        profile = UserProfile(name, email)
        self.profiles[name] = profile
        self.save_profiles()
        return True
    
    def delete_profile(self, name):
        """Delete a user profile"""
        if name in self.profiles and len(self.profiles) > 1:
            del self.profiles[name]
            if self.current_profile and self.current_profile.name == name:
                self.current_profile = list(self.profiles.values())[0]
            self.save_profiles()
            return True
        return False
    
    def switch_profile(self, name):
        """Switch to a different profile"""
        if name in self.profiles:
            self.current_profile = self.profiles[name]
            self.profile_changed.emit(name)
            return True
        return False
    
    def update_profile(self, profile_data):
        """Update current profile with new data"""
        if self.current_profile:
            for key, value in profile_data.items():
                if hasattr(self.current_profile, key):
                    setattr(self.current_profile, key, value)
            
            self.current_profile.last_modified = datetime.now().isoformat()
            self.save_profiles()
            self.preferences_updated.emit()
    
    def create_theme(self, name):
        """Create a new custom theme"""
        if name in self.custom_themes:
            return False  # Theme already exists
        
        theme = CustomTheme(name)
        self.custom_themes[name] = theme
        self.save_themes()
        return True
    
    def delete_theme(self, name):
        """Delete a custom theme"""
        if name in self.custom_themes:
            del self.custom_themes[name]
            self.save_themes()
            return True
        return False
    
    def apply_theme(self, theme_name):
        """Apply a theme to the application"""
        if theme_name in self.custom_themes:
            self.current_theme = self.custom_themes[theme_name]
            self.theme_changed.emit(theme_name)
            return True
        return False
    
    def get_current_profile(self):
        """Get current profile"""
        return self.current_profile
    
    def get_profile_names(self):
        """Get list of profile names"""
        return list(self.profiles.keys())
    
    def get_theme_names(self):
        """Get list of theme names"""
        return list(self.custom_themes.keys())

class ColorPickerButton(QPushButton):
    """Button for picking colors"""
    
    color_changed = pyqtSignal(str)  # Emits color hex string
    
    def __init__(self, color="#00d4aa", parent=None):
        super().__init__(parent)
        self.current_color = color
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the color picker button UI"""
        self.setFixedSize(60, 30)
        self.clicked.connect(self.pick_color)
        self.update_color_display()
        
    def update_color_display(self):
        """Update the button's color display"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color};
                border: 2px solid #4a5568;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border-color: #00d4aa;
            }}
        """)
        
    def pick_color(self):
        """Open color picker dialog"""
        color = QColorDialog.getColor(QColor(self.current_color), self, "Pick Color")
        if color.isValid():
            self.current_color = color.name()
            self.update_color_display()
            self.color_changed.emit(self.current_color)

class AdvancedPreferencesDialog(QDialog):
    """Advanced preferences dialog with profile and theme management"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preferences_manager = AdvancedPreferencesManager()
        self.setup_ui()
        self.load_current_settings()
        self.apply_theme()
        
    def setup_ui(self):
        """Setup the advanced preferences UI"""
        self.setWindowTitle("Advanced Preferences")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("Advanced Preferences")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Arial", 12))
        
        # Profile Management Tab
        self.setup_profile_tab()
        
        # Theme Customization Tab
        self.setup_theme_tab()
        
        # UI Preferences Tab
        self.setup_ui_preferences_tab()
        
        # Mission Preferences Tab
        self.setup_mission_preferences_tab()
        
        # Performance Tab
        self.setup_performance_tab()
        
        # Accessibility Tab
        self.setup_accessibility_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_preferences)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def setup_profile_tab(self):
        """Setup profile management tab"""
        profile_widget = QWidget()
        layout = QVBoxLayout(profile_widget)
        
        # Current Profile Section
        current_group = QGroupBox("Current Profile")
        current_layout = QFormLayout(current_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(self.preferences_manager.get_profile_names())
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        current_layout.addRow("Profile:", self.profile_combo)
        
        self.profile_name_edit = QLineEdit()
        current_layout.addRow("Name:", self.profile_name_edit)
        
        self.profile_email_edit = QLineEdit()
        current_layout.addRow("Email:", self.profile_email_edit)
        
        layout.addWidget(current_group)
        
        # Profile Actions
        actions_group = QGroupBox("Profile Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.new_profile_btn = QPushButton("New Profile")
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        actions_layout.addWidget(self.new_profile_btn)
        
        self.delete_profile_btn = QPushButton("Delete Profile")
        self.delete_profile_btn.clicked.connect(self.delete_current_profile)
        actions_layout.addWidget(self.delete_profile_btn)
        
        self.export_profile_btn = QPushButton("Export Profile")
        self.export_profile_btn.clicked.connect(self.export_profile)
        actions_layout.addWidget(self.export_profile_btn)
        
        self.import_profile_btn = QPushButton("Import Profile")
        self.import_profile_btn.clicked.connect(self.import_profile)
        actions_layout.addWidget(self.import_profile_btn)
        
        layout.addWidget(actions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(profile_widget, "Profiles")
        
    def setup_theme_tab(self):
        """Setup theme customization tab"""
        theme_widget = QWidget()
        layout = QVBoxLayout(theme_widget)
        
        # Theme Selection
        theme_group = QGroupBox("Theme Selection")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.preferences_manager.get_theme_names())
        theme_layout.addRow("Theme:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Color Customization
        colors_group = QGroupBox("Color Customization")
        colors_layout = QFormLayout(colors_group)
        
        self.primary_color_btn = ColorPickerButton()
        colors_layout.addRow("Primary Color:", self.primary_color_btn)
        
        self.secondary_color_btn = ColorPickerButton()
        colors_layout.addRow("Secondary Color:", self.secondary_color_btn)
        
        self.background_color_btn = ColorPickerButton()
        colors_layout.addRow("Background Color:", self.background_color_btn)
        
        self.accent_color_btn = ColorPickerButton()
        colors_layout.addRow("Accent Color:", self.accent_color_btn)
        
        layout.addWidget(colors_group)
        
        # Theme Actions
        theme_actions_group = QGroupBox("Theme Actions")
        theme_actions_layout = QHBoxLayout(theme_actions_group)
        
        self.new_theme_btn = QPushButton("New Theme")
        self.new_theme_btn.clicked.connect(self.create_new_theme)
        theme_actions_layout.addWidget(self.new_theme_btn)
        
        self.save_theme_btn = QPushButton("Save Theme")
        self.save_theme_btn.clicked.connect(self.save_current_theme)
        theme_actions_layout.addWidget(self.save_theme_btn)
        
        self.delete_theme_btn = QPushButton("Delete Theme")
        self.delete_theme_btn.clicked.connect(self.delete_current_theme)
        theme_actions_layout.addWidget(self.delete_theme_btn)
        
        layout.addWidget(theme_actions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(theme_widget, "Themes")
        
    def setup_ui_preferences_tab(self):
        """Setup UI preferences tab"""
        ui_widget = QWidget()
        layout = QVBoxLayout(ui_widget)
        
        # Display Settings
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout(display_group)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        display_layout.addRow("Font Size:", self.font_size_spin)
        
        self.animation_speed_combo = QComboBox()
        self.animation_speed_combo.addItems(["slow", "normal", "fast"])
        display_layout.addRow("Animation Speed:", self.animation_speed_combo)
        
        self.show_animations_check = QCheckBox("Show Animations")
        display_layout.addRow("", self.show_animations_check)
        
        self.show_tooltips_check = QCheckBox("Show Tooltips")
        display_layout.addRow("", self.show_tooltips_check)
        
        layout.addWidget(display_group)
        
        # Auto-Save Settings
        autosave_group = QGroupBox("Auto-Save Settings")
        autosave_layout = QFormLayout(autosave_group)
        
        self.auto_save_interval_spin = QSpinBox()
        self.auto_save_interval_spin.setRange(1, 60)
        self.auto_save_interval_spin.setSuffix(" minutes")
        autosave_layout.addRow("Auto-Save Interval:", self.auto_save_interval_spin)
        
        layout.addWidget(autosave_group)
        layout.addStretch()
        
        self.tab_widget.addTab(ui_widget, "UI Preferences")
        
    def setup_mission_preferences_tab(self):
        """Setup mission preferences tab"""
        mission_widget = QWidget()
        layout = QVBoxLayout(mission_widget)
        
        # Default Values
        defaults_group = QGroupBox("Default Mission Values")
        defaults_layout = QFormLayout(defaults_group)
        
        self.default_altitude_spin = QSpinBox()
        self.default_altitude_spin.setRange(10, 5000)
        self.default_altitude_spin.setSuffix(" m")
        defaults_layout.addRow("Default Altitude:", self.default_altitude_spin)
        
        self.default_interval_spin = QSpinBox()
        self.default_interval_spin.setRange(5, 1000)
        self.default_interval_spin.setSuffix(" m")
        defaults_layout.addRow("Default Waypoint Interval:", self.default_interval_spin)
        
        self.default_geofence_spin = QSpinBox()
        self.default_geofence_spin.setRange(10, 1000)
        self.default_geofence_spin.setSuffix(" m")
        defaults_layout.addRow("Default Geofence Buffer:", self.default_geofence_spin)
        
        layout.addWidget(defaults_group)
        
        # Safety Settings
        safety_group = QGroupBox("Safety Settings")
        safety_layout = QFormLayout(safety_group)
        
        self.auto_terrain_check_check = QCheckBox("Auto Terrain Check")
        safety_layout.addRow("", self.auto_terrain_check_check)
        
        self.show_safety_warnings_check = QCheckBox("Show Safety Warnings")
        safety_layout.addRow("", self.show_safety_warnings_check)
        
        self.confirm_dangerous_ops_check = QCheckBox("Confirm Dangerous Operations")
        safety_layout.addRow("", self.confirm_dangerous_ops_check)
        
        layout.addWidget(safety_group)
        layout.addStretch()
        
        self.tab_widget.addTab(mission_widget, "Mission Preferences")
        
    def setup_performance_tab(self):
        """Setup performance preferences tab"""
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # Map Settings
        map_group = QGroupBox("Map Settings")
        map_layout = QFormLayout(map_group)
        
        self.map_quality_combo = QComboBox()
        self.map_quality_combo.addItems(["low", "medium", "high"])
        map_layout.addRow("Map Quality:", self.map_quality_combo)
        
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 2000)
        self.cache_size_spin.setSuffix(" MB")
        map_layout.addRow("Cache Size Limit:", self.cache_size_spin)
        
        self.auto_cleanup_check = QCheckBox("Auto Cleanup Cache")
        map_layout.addRow("", self.auto_cleanup_check)
        
        layout.addWidget(map_group)
        
        # Processing Settings
        processing_group = QGroupBox("Processing Settings")
        processing_layout = QFormLayout(processing_group)
        
        self.background_processing_check = QCheckBox("Background Processing")
        processing_layout.addRow("", self.background_processing_check)
        
        layout.addWidget(processing_group)
        layout.addStretch()
        
        self.tab_widget.addTab(performance_widget, "Performance")
        
    def setup_accessibility_tab(self):
        """Setup accessibility preferences tab"""
        accessibility_widget = QWidget()
        layout = QVBoxLayout(accessibility_widget)
        
        # Visual Accessibility
        visual_group = QGroupBox("Visual Accessibility")
        visual_layout = QFormLayout(visual_group)
        
        self.high_contrast_check = QCheckBox("High Contrast Mode")
        visual_layout.addRow("", self.high_contrast_check)
        
        self.large_text_check = QCheckBox("Large Text Mode")
        visual_layout.addRow("", self.large_text_check)
        
        layout.addWidget(visual_group)
        
        # Input Accessibility
        input_group = QGroupBox("Input Accessibility")
        input_layout = QFormLayout(input_group)
        
        self.keyboard_shortcuts_check = QCheckBox("Enable Keyboard Shortcuts")
        input_layout.addRow("", self.keyboard_shortcuts_check)
        
        self.screen_reader_check = QCheckBox("Screen Reader Support")
        input_layout.addRow("", self.screen_reader_check)
        
        layout.addWidget(input_group)
        layout.addStretch()
        
        self.tab_widget.addTab(accessibility_widget, "Accessibility")
        
    def load_current_settings(self):
        """Load current profile settings into the dialog"""
        profile = self.preferences_manager.get_current_profile()
        if not profile:
            return
            
        # Profile settings
        self.profile_name_edit.setText(profile.name)
        self.profile_email_edit.setText(profile.email)
        
        # UI settings
        self.font_size_spin.setValue(profile.font_size)
        self.animation_speed_combo.setCurrentText(profile.animation_speed)
        self.show_animations_check.setChecked(profile.show_animations)
        self.show_tooltips_check.setChecked(profile.show_tooltips)
        self.auto_save_interval_spin.setValue(profile.auto_save_interval)
        
        # Mission settings
        self.default_altitude_spin.setValue(profile.default_altitude)
        self.default_interval_spin.setValue(profile.default_waypoint_interval)
        self.default_geofence_spin.setValue(profile.default_geofence_buffer)
        self.auto_terrain_check_check.setChecked(profile.auto_terrain_check)
        self.show_safety_warnings_check.setChecked(profile.show_safety_warnings)
        self.confirm_dangerous_ops_check.setChecked(profile.confirm_dangerous_operations)
        
        # Performance settings
        self.map_quality_combo.setCurrentText(profile.map_quality)
        self.cache_size_spin.setValue(profile.cache_size_limit)
        self.auto_cleanup_check.setChecked(profile.auto_cleanup_cache)
        self.background_processing_check.setChecked(profile.background_processing)
        
        # Accessibility settings
        self.high_contrast_check.setChecked(profile.high_contrast_mode)
        self.large_text_check.setChecked(profile.large_text_mode)
        self.keyboard_shortcuts_check.setChecked(profile.keyboard_shortcuts_enabled)
        self.screen_reader_check.setChecked(profile.screen_reader_support)
        
    def apply_theme(self):
        """Apply the dark theme to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a2332;
                color: white;
            }
            QTabWidget::pane {
                border: 1px solid #2d3748;
                background-color: #1a2332;
            }
            QTabBar::tab {
                background-color: #2d3748;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2d3748;
                border-radius: 8px;
                margin-top: 1ex;
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
            QLabel {
                color: white;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #00d4aa;
            }
            QPushButton {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QPushButton:pressed {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QCheckBox {
                color: white;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4a5568;
                background-color: #2d3748;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #00d4aa;
                background-color: #00d4aa;
                border-radius: 3px;
            }
        """)
        
    def on_profile_changed(self, profile_name):
        """Handle profile change"""
        if self.preferences_manager.switch_profile(profile_name):
            self.load_current_settings()
            
    def create_new_profile(self):
        """Create a new profile"""
        # This would typically open a dialog to get profile name and email
        # For now, create a simple default profile
        profile_name = f"Profile {len(self.preferences_manager.profiles) + 1}"
        if self.preferences_manager.create_profile(profile_name):
            self.profile_combo.addItem(profile_name)
            self.profile_combo.setCurrentText(profile_name)
            
    def delete_current_profile(self):
        """Delete the current profile"""
        current_name = self.profile_combo.currentText()
        if self.preferences_manager.delete_profile(current_name):
            self.profile_combo.removeItem(self.profile_combo.currentIndex())
            
    def export_profile(self):
        """Export current profile"""
        # Implementation for profile export
        pass
        
    def import_profile(self):
        """Import a profile"""
        # Implementation for profile import
        pass
        
    def create_new_theme(self):
        """Create a new theme"""
        theme_name = f"Theme {len(self.preferences_manager.custom_themes) + 1}"
        if self.preferences_manager.create_theme(theme_name):
            self.theme_combo.addItem(theme_name)
            self.theme_combo.setCurrentText(theme_name)
            
    def save_current_theme(self):
        """Save the current theme"""
        # Implementation for saving current theme
        pass
        
    def delete_current_theme(self):
        """Delete the current theme"""
        current_name = self.theme_combo.currentText()
        if self.preferences_manager.delete_theme(current_name):
            self.theme_combo.removeItem(self.theme_combo.currentIndex())
            
    def apply_preferences(self):
        """Apply the current preferences"""
        profile_data = {
            'name': self.profile_name_edit.text(),
            'email': self.profile_email_edit.text(),
            'font_size': self.font_size_spin.value(),
            'animation_speed': self.animation_speed_combo.currentText(),
            'show_animations': self.show_animations_check.isChecked(),
            'show_tooltips': self.show_tooltips_check.isChecked(),
            'auto_save_interval': self.auto_save_interval_spin.value(),
            'default_altitude': self.default_altitude_spin.value(),
            'default_waypoint_interval': self.default_interval_spin.value(),
            'default_geofence_buffer': self.default_geofence_spin.value(),
            'auto_terrain_check': self.auto_terrain_check_check.isChecked(),
            'show_safety_warnings': self.show_safety_warnings_check.isChecked(),
            'confirm_dangerous_operations': self.confirm_dangerous_ops_check.isChecked(),
            'map_quality': self.map_quality_combo.currentText(),
            'cache_size_limit': self.cache_size_spin.value(),
            'auto_cleanup_cache': self.auto_cleanup_check.isChecked(),
            'background_processing': self.background_processing_check.isChecked(),
            'high_contrast_mode': self.high_contrast_check.isChecked(),
            'large_text_mode': self.large_text_check.isChecked(),
            'keyboard_shortcuts_enabled': self.keyboard_shortcuts_check.isChecked(),
            'screen_reader_support': self.screen_reader_check.isChecked()
        }
        
        self.preferences_manager.update_profile(profile_data)

# Global preferences manager instance
advanced_preferences_manager = AdvancedPreferencesManager()
