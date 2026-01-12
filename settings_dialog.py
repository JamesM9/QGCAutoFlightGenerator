#!/usr/bin/env python3
"""
Settings Dialog for AutoFlightGenerator
Allows users to configure global settings like units, theme, and defaults.
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QComboBox, QPushButton, QGroupBox, QSpinBox,
                              QCheckBox, QFormLayout, QDialogButtonBox, QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from settings_manager import settings_manager, UnitSystem, GroundControlStation
import PyQt5.QtWidgets as QtWidgets

# Import aircraft parameters tab
from aircraft_parameters import AircraftParametersTab


class SettingsDialog(QDialog):
    """Dialog for configuring application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.setMinimumSize(1200, 900)  # Increased minimum size for better spacing
        self.resize(1300, 1000)  # Increased initial size for comfortable spacing
        
        # Set palette to ensure white text
        from PyQt5.QtGui import QPalette
        palette = QPalette()
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        palette.setColor(QPalette.Text, QColor(255, 255, 255))  # White text
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))  # White button text
        self.setPalette(palette)
        
        self.setup_ui()
        self.load_current_settings()
        self.apply_theme()
        self.force_white_text()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(25)  # Increased spacing for better readability
        layout.setContentsMargins(35, 35, 35, 35)  # Increased margins for breathing room
        
        # Title
        title_label = QLabel("Application Settings")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))  # Increased font size
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(600)  # Ensure adequate height for content
        
        # General settings tab
        general_tab = self.create_general_settings_tab()
        self.tab_widget.addTab(general_tab, "General")
        
        # Aircraft parameters tab
        self.aircraft_params_tab = AircraftParametersTab()
        self.tab_widget.addTab(self.aircraft_params_tab, "Aircraft Parameters")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setFont(QFont("Arial", 12))  # Increased font size
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def create_general_settings_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(25)  # Increased spacing between groups for better readability
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Units Group
        units_group = QGroupBox("Units of Measurement")
        units_group.setFont(QFont("Arial", 14, QFont.Bold))  # Increased font size
        units_layout = QFormLayout(units_group)
        units_layout.setSpacing(20)  # Increased spacing for better readability
        units_layout.setLabelAlignment(Qt.AlignLeft)
        units_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.unit_system_combo = QComboBox()
        self.unit_system_combo.setFont(QFont("Arial", 12))  # Increased font size
        self.unit_system_combo.setMinimumHeight(40)  # Increased height
        self.unit_system_combo.addItems(["Metric (Meters)", "Imperial (Feet)"])
        units_layout.addRow("Unit System:", self.unit_system_combo)
        
        layout.addWidget(units_group)
        
        # Ground Control Station Group
        gcs_group = QGroupBox("Ground Control Station")
        gcs_group.setFont(QFont("Arial", 14, QFont.Bold))  # Increased font size
        gcs_layout = QFormLayout(gcs_group)
        gcs_layout.setSpacing(20)  # Increased spacing for better readability
        gcs_layout.setLabelAlignment(Qt.AlignLeft)
        gcs_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.gcs_combo = QComboBox()
        self.gcs_combo.setFont(QFont("Arial", 12))  # Increased font size
        self.gcs_combo.setMinimumHeight(40)  # Increased height
        self.gcs_combo.addItems([
            "QGroundControl (.plan files)",
            "Mission Planner (.waypoint files)"
        ])
        gcs_layout.addRow("Target GCS:", self.gcs_combo)
        
        layout.addWidget(gcs_group)
        
        # Default Values Group
        defaults_group = QGroupBox("Default Values")
        defaults_group.setFont(QFont("Arial", 14, QFont.Bold))  # Increased font size
        defaults_layout = QFormLayout(defaults_group)
        defaults_layout.setSpacing(20)  # Increased spacing for better readability
        defaults_layout.setLabelAlignment(Qt.AlignLeft)
        defaults_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.default_altitude_spin = QSpinBox()
        self.default_altitude_spin.setFont(QFont("Arial", 12))  # Increased font size
        self.default_altitude_spin.setMinimumHeight(40)  # Increased height
        self.default_altitude_spin.setRange(10, 10000)
        self.default_altitude_spin.setSuffix(" units")
        defaults_layout.addRow("Default Altitude:", self.default_altitude_spin)
        
        self.default_interval_spin = QSpinBox()
        self.default_interval_spin.setFont(QFont("Arial", 12))  # Increased font size
        self.default_interval_spin.setMinimumHeight(40)  # Increased height
        self.default_interval_spin.setRange(5, 1000)
        self.default_interval_spin.setSuffix(" units")
        defaults_layout.addRow("Default Waypoint Interval:", self.default_interval_spin)
        
        self.default_geofence_spin = QSpinBox()
        self.default_geofence_spin.setFont(QFont("Arial", 12))  # Increased font size
        self.default_geofence_spin.setMinimumHeight(40)  # Increased height
        self.default_geofence_spin.setRange(10, 1000)
        self.default_geofence_spin.setSuffix(" units")
        defaults_layout.addRow("Default Geofence Buffer:", self.default_geofence_spin)
        
        layout.addWidget(defaults_group)
        
        # Theme Group
        theme_group = QGroupBox("Appearance")
        theme_group.setFont(QFont("Arial", 14, QFont.Bold))  # Increased font size
        theme_layout = QFormLayout(theme_group)
        theme_layout.setSpacing(20)  # Increased spacing for better readability
        theme_layout.setLabelAlignment(Qt.AlignLeft)
        theme_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        self.theme_combo = QComboBox()
        self.theme_combo.setFont(QFont("Arial", 12))  # Increased font size
        self.theme_combo.setMinimumHeight(40)  # Increased height
        self.theme_combo.addItems(["Dark Theme", "Light Theme"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Connect signals
        self.unit_system_combo.currentTextChanged.connect(self.on_unit_system_changed)
        self.gcs_combo.currentTextChanged.connect(self.on_gcs_changed)
        self.default_altitude_spin.valueChanged.connect(self.on_default_changed)
        self.default_interval_spin.valueChanged.connect(self.on_default_changed)
        self.default_geofence_spin.valueChanged.connect(self.on_default_changed)
        
        return tab
    
    def load_current_settings(self):
        """Load current settings into the dialog"""
        # Unit system
        if settings_manager.is_metric():
            self.unit_system_combo.setCurrentText("Metric (Meters)")
        else:
            self.unit_system_combo.setCurrentText("Imperial (Feet)")
        
        # Ground control station
        if settings_manager.is_qgroundcontrol():
            self.gcs_combo.setCurrentText("QGroundControl (.plan files)")
        else:
            self.gcs_combo.setCurrentText("Mission Planner (.waypoint files)")
        
        # Default values
        self.default_altitude_spin.setValue(settings_manager.get_default_altitude())
        self.default_interval_spin.setValue(settings_manager.get_default_interval())
        self.default_geofence_spin.setValue(settings_manager.get_default_geofence_buffer())
        
        # Theme
        theme = settings_manager.get_theme()
        if theme == "light":
            self.theme_combo.setCurrentText("Light Theme")
        else:
            self.theme_combo.setCurrentText("Dark Theme")
    
    def on_unit_system_changed(self, text):
        """Handle unit system change"""
        # Update suffix for spinboxes based on unit system
        if "Metric" in text:
            suffix = " m"
        else:
            suffix = " ft"
        
        self.default_altitude_spin.setSuffix(suffix)
        self.default_interval_spin.setSuffix(suffix)
        self.default_geofence_spin.setSuffix(suffix)
    
    def on_gcs_changed(self, text):
        """Handle ground control station change"""
        # This will be called when GCS selection changes
        pass
    
    def on_default_changed(self):
        """Handle default value changes"""
        # This will be called when spinbox values change
        pass
    
    def accept(self):
        """Save settings when OK is clicked"""
        # Save unit system
        if "Metric" in self.unit_system_combo.currentText():
            settings_manager.set_unit_system(UnitSystem.METRIC.value)
        else:
            settings_manager.set_unit_system(UnitSystem.IMPERIAL.value)
        
        # Save ground control station
        if "QGroundControl" in self.gcs_combo.currentText():
            settings_manager.set_ground_control_station(GroundControlStation.QGROUNDCONTROL.value)
        else:
            settings_manager.set_ground_control_station(GroundControlStation.MISSION_PLANNER.value)
        
        # Save default values (convert to meters for storage)
        altitude_meters = settings_manager.convert_to_meters(
            self.default_altitude_spin.value(), 
            "feet" if settings_manager.is_imperial() else "meters"
        )
        interval_meters = settings_manager.convert_to_meters(
            self.default_interval_spin.value(),
            "feet" if settings_manager.is_imperial() else "meters"
        )
        geofence_meters = settings_manager.convert_to_meters(
            self.default_geofence_spin.value(),
            "feet" if settings_manager.is_imperial() else "meters"
        )
        
        settings_manager.set_setting("default_altitude", altitude_meters)
        settings_manager.set_setting("default_interval", interval_meters)
        settings_manager.set_setting("default_geofence_buffer", geofence_meters)
        
        # Save theme
        if "Light" in self.theme_combo.currentText():
            settings_manager.set_theme("light")
        else:
            settings_manager.set_theme("dark")
        
        super().accept()
    
    def force_white_text(self):
        """Force all text to be white by setting individual widget palettes"""
        from PyQt5.QtGui import QPalette
        
        # Create white text palette
        white_palette = QPalette()
        white_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        white_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        white_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        
        # Apply to all comboboxes
        for combo in [self.unit_system_combo, self.gcs_combo, self.theme_combo]:
            combo.setPalette(white_palette)
            combo.setStyleSheet("color: white !important;")
        
        # Apply to all spinboxes
        for spinbox in [self.default_altitude_spin, self.default_interval_spin, self.default_geofence_spin]:
            spinbox.setPalette(white_palette)
            spinbox.setStyleSheet("color: white !important;")
        
        # No checkboxes to apply palette to
    
    def apply_theme(self):
        """Apply the dashboard-matching dark theme to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #0f1419;
                color: white;
            }
            QWidget {
                background-color: #0f1419;
                color: white;
            }
            QScrollArea {
                background-color: #0f1419;
                border: none;
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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTabWidget {
                background-color: #0f1419;
                color: white;
            }
            QTabBar {
                background-color: #0f1419;
                min-height: 50px;
            }
            QTabWidget::pane {
                border: 1px solid #2d3748;
                border-radius: 5px;
                background-color: #0f1419;
            }
            QTabBar::tab {
                background-color: #2d3748;
                color: white;
                padding: 15px 30px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                min-width: 120px;
                min-height: 40px;
            }
            QTabBar::tab:selected {
                background-color: #0f1419;
                border-bottom: 2px solid #00d4aa;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #4a5568;
                color: white;
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
                background-color: #0f1419;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00d4aa;
            }
            QLabel {
                color: white !important;
                font-size: 12px;
                font-weight: bold;
                padding: 5px 0px;
                background-color: transparent;
            }
            QComboBox, QSpinBox {
                background-color: #2d3748;
                color: white !important;
                border: 2px solid #4a5568;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                min-height: 40px;
            }
            QComboBox * {
                color: white !important;
            }
            QComboBox:focus, QSpinBox:focus {
                border-color: #00d4aa;
                background-color: #4a5568;
                color: white !important;
            }
            QComboBox:hover, QSpinBox:hover {
                border-color: #00d4aa;
                background-color: #4a5568;
                color: white !important;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d3748;
                color: white !important;
                border: 1px solid #4a5568;
                selection-background-color: #00d4aa;
            }
            QComboBox QAbstractItemView::item {
                color: white !important;
                background-color: #2d3748;
                padding: 5px;
            }
            QComboBox QAbstractItemView::item:hover {
                color: white !important;
                background-color: #4a5568;
            }
            QComboBox QAbstractItemView::item:selected {
                color: white !important;
                background-color: #00d4aa;
            }
            QComboBox QAbstractItemView::item:selected:hover {
                color: white !important;
                background-color: #00d4aa;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #4a5568;
                border: 1px solid #2d3748;
                border-radius: 3px;
                width: 20px;
                height: 15px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #00d4aa;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid white;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid white;
            }
            QCheckBox {
                color: white !important;
                spacing: 12px;
                font-size: 12px;
                padding: 8px 0px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #4a5568;
                background-color: #0f1419;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #00d4aa;
                background-color: #00d4aa;
                border-radius: 4px;
            }
            QCheckBox::indicator:hover {
                border-color: #00d4aa;
            }
            QPushButton {
                background-color: #2d3748;
                color: white !important;
                border: 2px solid #4a5568;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                min-height: 40px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
                color: white !important;
            }
            QPushButton:pressed {
                background-color: #1a2332;
                color: white !important;
            }
            QPushButton:disabled {
                background-color: #1a2332;
                color: #888888;
                border-color: #2d3748;
            }
        """) 