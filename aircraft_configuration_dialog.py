#!/usr/bin/env python3
"""
Aircraft Configuration Dialog for AutoFlightGenerator
Provides user interface for loading, configuring, and managing aircraft parameters and profiles
"""

import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QComboBox, QLineEdit, QTextEdit, QGroupBox, QFormLayout,
                             QFileDialog, QMessageBox, QTabWidget, QWidget, QListWidget,
                             QListWidgetItem, QSplitter, QFrame, QProgressBar, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from aircraft_parameter_manager import AircraftParameterManager
from aircraft_profile_manager import AircraftProfileManager


class AircraftConfigurationDialog(QDialog):
    """Dialog for loading and configuring aircraft parameters"""
    
    # Signals for parameter changes
    parameters_loaded = pyqtSignal(str)  # Emits firmware type
    profile_selected = pyqtSignal(str)   # Emits profile name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.param_manager = AircraftParameterManager()
        self.profile_manager = AircraftProfileManager()
        
        # Connect signals
        self.param_manager.parameters_loaded.connect(self.on_parameters_loaded)
        self.param_manager.validation_warnings.connect(self.on_validation_warnings)
        self.param_manager.validation_errors.connect(self.on_validation_errors)
        self.profile_manager.profile_loaded.connect(self.on_profile_loaded)
        
        self.setup_ui()
        self.load_current_profile()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Aircraft Configuration")
        self.setGeometry(100, 100, 800, 600)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_parameter_loading_tab()
        self.create_profile_management_tab()
        self.create_parameter_viewer_tab()
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Apply Configuration")
        self.apply_btn.clicked.connect(self.apply_configuration)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
    def create_parameter_loading_tab(self):
        """Create the parameter loading tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title_label = QLabel("Load Aircraft Parameters")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Firmware selection
        firmware_group = QGroupBox("Firmware Type")
        firmware_layout = QFormLayout(firmware_group)
        
        self.firmware_combo = QComboBox()
        self.firmware_combo.addItems(["ArduPilot", "PX4"])
        self.firmware_combo.currentTextChanged.connect(self.on_firmware_changed)
        firmware_layout.addRow("Firmware:", self.firmware_combo)
        
        layout.addWidget(firmware_group)
        
        # Parameter file loading
        file_group = QGroupBox("Parameter File")
        file_layout = QFormLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.file_path_edit.setPlaceholderText("Select parameter file...")
        file_layout.addRow("File Path:", self.file_path_edit)
        
        file_button_layout = QHBoxLayout()
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_parameter_file)
        file_button_layout.addWidget(self.browse_btn)
        
        self.load_btn = QPushButton("Load Parameters")
        self.load_btn.clicked.connect(self.load_parameter_file)
        self.load_btn.setEnabled(False)
        file_button_layout.addWidget(self.load_btn)
        
        file_layout.addRow("", file_button_layout)
        layout.addWidget(file_group)
        
        # Aircraft type selection
        aircraft_group = QGroupBox("Aircraft Type")
        aircraft_layout = QFormLayout(aircraft_group)
        
        self.aircraft_type_combo = QComboBox()
        self.aircraft_type_combo.addItems(["Multicopter", "Fixed Wing", "VTOL", "Unknown"])
        aircraft_layout.addRow("Type:", self.aircraft_type_combo)
        
        self.aircraft_description_edit = QLineEdit()
        self.aircraft_description_edit.setPlaceholderText("Enter aircraft description...")
        aircraft_layout.addRow("Description:", self.aircraft_description_edit)
        
        layout.addWidget(aircraft_group)
        
        # Save as profile
        profile_group = QGroupBox("Save as Profile")
        profile_layout = QFormLayout(profile_group)
        
        self.profile_name_edit = QLineEdit()
        self.profile_name_edit.setPlaceholderText("Enter profile name...")
        profile_layout.addRow("Profile Name:", self.profile_name_edit)
        
        self.save_profile_btn = QPushButton("Save Profile")
        self.save_profile_btn.clicked.connect(self.save_as_profile)
        self.save_profile_btn.setEnabled(False)
        profile_layout.addRow("", self.save_profile_btn)
        
        layout.addWidget(profile_group)
        
        self.tab_widget.addTab(tab, "Load Parameters")
        
    def create_profile_management_tab(self):
        """Create the profile management tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title_label = QLabel("Aircraft Profile Management")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Profile selection
        selection_group = QGroupBox("Select Profile")
        selection_layout = QFormLayout(selection_group)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Select a profile...")
        self.refresh_profile_list()
        self.profile_combo.currentTextChanged.connect(self.on_profile_selection_changed)
        selection_layout.addRow("Profile:", self.profile_combo)
        
        self.load_profile_btn = QPushButton("Load Profile")
        self.load_profile_btn.clicked.connect(self.load_selected_profile)
        self.load_profile_btn.setEnabled(False)
        selection_layout.addRow("", self.load_profile_btn)
        
        layout.addWidget(selection_group)
        
        # Profile information
        info_group = QGroupBox("Profile Information")
        info_layout = QFormLayout(info_group)
        
        self.profile_info_label = QLabel("No profile selected")
        self.profile_info_label.setWordWrap(True)
        info_layout.addRow("Info:", self.profile_info_label)
        
        layout.addWidget(info_group)
        
        # Profile actions
        actions_group = QGroupBox("Profile Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.duplicate_profile_btn = QPushButton("Duplicate")
        self.duplicate_profile_btn.clicked.connect(self.duplicate_profile)
        self.duplicate_profile_btn.setEnabled(False)
        actions_layout.addWidget(self.duplicate_profile_btn)
        
        self.delete_profile_btn = QPushButton("Delete")
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.delete_profile_btn.setEnabled(False)
        actions_layout.addWidget(self.delete_profile_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_profile_list)
        actions_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(actions_group)
        
        self.tab_widget.addTab(tab, "Profile Management")
        
    def create_parameter_viewer_tab(self):
        """Create the parameter viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Title
        title_label = QLabel("Parameter Viewer")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Current parameters display
        params_group = QGroupBox("Current Parameters")
        params_layout = QVBoxLayout(params_group)
        
        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setFont(QFont("Courier", 10))
        params_layout.addWidget(self.params_text)
        
        layout.addWidget(params_group)
        
        # Parameter summary
        summary_group = QGroupBox("Parameter Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        self.tab_widget.addTab(tab, "Parameter Viewer")
        
    def on_firmware_changed(self, firmware_text):
        """Handle firmware type change"""
        # Update file extensions and validation
        if firmware_text == "ArduPilot":
            self.file_extensions = "ArduPilot Parameter Files (*.par);;All Files (*)"
        else:
            self.file_extensions = "PX4 Parameter Files (*.params);;All Files (*)"
        
        # Clear current file path
        self.file_path_edit.clear()
        self.load_btn.setEnabled(False)
        
    def browse_parameter_file(self):
        """Browse for parameter file"""
        firmware_text = self.firmware_combo.currentText()
        
        if firmware_text == "ArduPilot":
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select ArduPilot Parameter File", "", 
                "ArduPilot Parameter Files (*.par);;All Files (*)"
            )
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select PX4 Parameter File", "", 
                "PX4 Parameter Files (*.params);;All Files (*)"
            )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.load_btn.setEnabled(True)
            
            # Auto-generate profile name from filename
            filename = os.path.splitext(os.path.basename(file_path))[0]
            self.profile_name_edit.setText(f"{filename} ({firmware_text})")
    
    def load_parameter_file(self):
        """Load parameter file"""
        file_path = self.file_path_edit.text()
        firmware_text = self.firmware_combo.currentText()
        
        if not file_path:
            QMessageBox.warning(self, "Error", "Please select a parameter file")
            return
        
        try:
            self.status_label.setText("Loading parameters...")
            self.setCursor(Qt.WaitCursor)
            
            # Load parameters based on firmware type
            if firmware_text == "ArduPilot":
                success = self.param_manager.load_ardupilot_params(file_path)
            else:
                success = self.param_manager.load_px4_params(file_path)
            
            if success:
                self.status_label.setText("Parameters loaded successfully")
                self.save_profile_btn.setEnabled(True)
                self.update_parameter_display()
                self.tab_widget.setCurrentIndex(2)  # Switch to parameter viewer
            else:
                self.status_label.setText("Failed to load parameters")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading parameters: {str(e)}")
            self.status_label.setText("Error loading parameters")
        finally:
            self.setCursor(Qt.ArrowCursor)
    
    def save_as_profile(self):
        """Save current parameters as a profile"""
        profile_name = self.profile_name_edit.text().strip()
        aircraft_type = self.aircraft_type_combo.currentText()
        description = self.aircraft_description_edit.text().strip()
        
        if not profile_name:
            QMessageBox.warning(self, "Error", "Please enter a profile name")
            return
        
        if not self.param_manager.has_parameters():
            QMessageBox.warning(self, "Error", "No parameters loaded to save")
            return
        
        try:
            # Create profile
            success = self.profile_manager.import_profile_from_parameter_manager(
                self.param_manager, profile_name, aircraft_type, description
            )
            
            if success:
                QMessageBox.information(self, "Success", f"Profile '{profile_name}' saved successfully")
                self.refresh_profile_list()
                self.tab_widget.setCurrentIndex(1)  # Switch to profile management
                self.status_label.setText(f"Profile '{profile_name}' saved")
            else:
                QMessageBox.warning(self, "Error", "Failed to save profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving profile: {str(e)}")
    
    def refresh_profile_list(self):
        """Refresh the profile list"""
        self.profile_combo.clear()
        self.profile_combo.addItem("Select a profile...")
        
        profile_names = self.profile_manager.get_profile_names()
        self.profile_combo.addItems(profile_names)
        
        # Select current profile if available
        current_profile = self.profile_manager.get_current_profile()
        if current_profile:
            index = self.profile_combo.findText(current_profile.name)
            if index >= 0:
                self.profile_combo.setCurrentIndex(index)
    
    def on_profile_selection_changed(self, profile_name):
        """Handle profile selection change"""
        if profile_name == "Select a profile..." or not profile_name:
            self.load_profile_btn.setEnabled(False)
            self.duplicate_profile_btn.setEnabled(False)
            self.delete_profile_btn.setEnabled(False)
            self.profile_info_label.setText("No profile selected")
            return
        
        # Enable buttons
        self.load_profile_btn.setEnabled(True)
        self.duplicate_profile_btn.setEnabled(True)
        
        # Check if profile can be deleted (not default)
        profile = self.profile_manager.get_profile(profile_name)
        if profile and not profile.is_default:
            self.delete_profile_btn.setEnabled(True)
        else:
            self.delete_profile_btn.setEnabled(False)
        
        # Update profile info
        if profile:
            info_text = f"Firmware: {profile.firmware_type.upper()}\n"
            info_text += f"Type: {profile.aircraft_type}\n"
            info_text += f"Description: {profile.description}\n"
            info_text += f"Parameters: {len(profile.parameters)}\n"
            info_text += f"Created: {profile.created_date[:10]}\n"
            info_text += f"Last Used: {profile.last_used[:10]}"
            
            self.profile_info_label.setText(info_text)
    
    def load_selected_profile(self):
        """Load the selected profile"""
        profile_name = self.profile_combo.currentText()
        
        if profile_name == "Select a profile..." or not profile_name:
            return
        
        try:
            self.status_label.setText(f"Loading profile '{profile_name}'...")
            
            # Export profile to parameter manager
            success = self.profile_manager.export_profile_to_parameter_manager(
                profile_name, self.param_manager
            )
            
            if success:
                self.status_label.setText(f"Profile '{profile_name}' loaded successfully")
                self.update_parameter_display()
                self.tab_widget.setCurrentIndex(2)  # Switch to parameter viewer
                
                # Emit signal
                self.profile_selected.emit(profile_name)
            else:
                QMessageBox.warning(self, "Error", "Failed to load profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading profile: {str(e)}")
    
    def duplicate_profile(self):
        """Duplicate the selected profile"""
        profile_name = self.profile_combo.currentText()
        
        if profile_name == "Select a profile..." or not profile_name:
            return
        
        # Get new name from user
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Duplicate Profile", 
            f"Enter new name for '{profile_name}':",
            QtWidgets.QLineEdit.Normal, f"{profile_name} (Copy)"
        )
        
        if ok and new_name.strip():
            try:
                success = self.profile_manager.duplicate_profile(profile_name, new_name.strip())
                
                if success:
                    QMessageBox.information(self, "Success", f"Profile duplicated as '{new_name}'")
                    self.refresh_profile_list()
                else:
                    QMessageBox.warning(self, "Error", "Failed to duplicate profile")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error duplicating profile: {str(e)}")
    
    def delete_profile(self):
        """Delete the selected profile"""
        profile_name = self.profile_combo.currentText()
        
        if profile_name == "Select a profile..." or not profile_name:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion", 
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.profile_manager.delete_profile(profile_name)
                
                if success:
                    QMessageBox.information(self, "Success", f"Profile '{profile_name}' deleted")
                    self.refresh_profile_list()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete profile")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting profile: {str(e)}")
    
    def update_parameter_display(self):
        """Update the parameter display"""
        if not self.param_manager.has_parameters():
            self.params_text.setPlainText("No parameters loaded")
            self.summary_text.setPlainText("No parameters loaded")
            return
        
        # Display parameters
        params = self.param_manager.get_current_parameters()
        param_text = f"Firmware: {self.param_manager.current_firmware.upper()}\n"
        param_text += f"File: {os.path.basename(self.param_manager.param_file_path) if self.param_manager.param_file_path else 'Unknown'}\n"
        param_text += f"Total Parameters: {len(params)}\n\n"
        
        # Sort parameters alphabetically
        for param_name in sorted(params.keys()):
            param_value = params[param_name]
            param_text += f"{param_name:<25} = {param_value}\n"
        
        self.params_text.setPlainText(param_text)
        
        # Update summary
        summary = self.param_manager.get_parameter_summary()
        self.summary_text.setPlainText(summary)
    
    def load_current_profile(self):
        """Load the current profile if available"""
        current_profile = self.profile_manager.get_current_profile()
        if current_profile:
            self.profile_manager.export_profile_to_parameter_manager(
                current_profile.name, self.param_manager
            )
            self.update_parameter_display()
    
    def apply_configuration(self):
        """Apply the current configuration"""
        if not self.param_manager.has_parameters():
            QMessageBox.warning(self, "Error", "No parameters loaded to apply")
            return
        
        # Emit signal that parameters are loaded
        self.parameters_loaded.emit(self.param_manager.current_firmware)
        
        QMessageBox.information(self, "Success", "Configuration applied successfully")
        self.status_label.setText("Configuration applied")
    
    def on_parameters_loaded(self, firmware_type):
        """Handle parameters loaded signal"""
        self.update_parameter_display()
        self.save_profile_btn.setEnabled(True)
    
    def on_validation_warnings(self, warnings):
        """Handle validation warnings"""
        if warnings:
            warning_text = "Validation Warnings:\n" + "\n".join(warnings)
            QMessageBox.warning(self, "Validation Warnings", warning_text)
    
    def on_validation_errors(self, errors):
        """Handle validation errors"""
        if errors:
            error_text = "Validation Errors:\n" + "\n".join(errors)
            QMessageBox.critical(self, "Validation Errors", error_text)
    
    def on_profile_loaded(self, profile_name):
        """Handle profile loaded signal"""
        self.status_label.setText(f"Profile '{profile_name}' loaded")
    
    def get_current_parameter_manager(self):
        """Get the current parameter manager"""
        return self.param_manager
    
    def get_current_profile_manager(self):
        """Get the current profile manager"""
        return self.profile_manager
