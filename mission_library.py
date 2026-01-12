#!/usr/bin/env python3
"""
Mission Library System for saving and loading mission plans
"""

import sys
import json
import os
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                             QDialog, QMessageBox, QFileDialog, QTextEdit,
                             QComboBox, QSpinBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

class MissionLibrary(QWidget):
    """Mission library widget for managing saved missions"""
    
    mission_selected = pyqtSignal(dict)  # Emitted when a mission is selected
    mission_deleted = pyqtSignal(str)    # Emitted when a mission is deleted
    
    def __init__(self, library_file="mission_library.json", parent=None):
        super().__init__(parent)
        self.library_file = library_file
        self.missions = {}
        self.setup_ui()
        self.load_library()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Mission Library")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #FFD700;")
        header_layout.addWidget(title_label)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search missions...")
        self.search_box.textChanged.connect(self.filter_missions)
        header_layout.addWidget(self.search_box)
        
        layout.addLayout(header_layout)
        
        # Mission list
        self.mission_list = QListWidget()
        self.mission_list.setStyleSheet("""
            QListWidget {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #3C3C3C;
            }
            QListWidget::item:selected {
                background-color: #FFD700;
                color: #1E1E1E;
            }
            QListWidget::item:hover {
                background-color: #3C3C3C;
            }
        """)
        self.mission_list.itemClicked.connect(self.on_mission_selected)
        layout.addWidget(self.mission_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load Mission")
        self.load_btn.clicked.connect(self.load_selected_mission)
        self.load_btn.setEnabled(False)
        button_layout.addWidget(self.load_btn)
        
        self.delete_btn = QPushButton("Delete Mission")
        self.delete_btn.clicked.connect(self.delete_selected_mission)
        self.delete_btn.setEnabled(False)
        button_layout.addWidget(self.delete_btn)
        
        self.export_btn = QPushButton("Export Mission")
        self.export_btn.clicked.connect(self.export_selected_mission)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
        # Connect list selection to button states
        self.mission_list.itemSelectionChanged.connect(self.update_button_states)
        
    def load_library(self):
        """Load mission library from file"""
        if os.path.exists(self.library_file):
            try:
                with open(self.library_file, 'r') as f:
                    self.missions = json.load(f)
                self.refresh_mission_list()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load mission library: {e}")
                
    def save_library(self):
        """Save mission library to file"""
        try:
            with open(self.library_file, 'w') as f:
                json.dump(self.missions, f, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save mission library: {e}")
            
    def add_mission(self, mission_data):
        """Add a new mission to the library"""
        mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create mission entry
        mission_entry = {
            'id': mission_id,
            'name': mission_data.get('name', 'Unnamed Mission'),
            'type': mission_data.get('type', 'Unknown'),
            'created': datetime.now().isoformat(),
            'data': mission_data
        }
        
        self.missions[mission_id] = mission_entry
        self.save_library()
        self.refresh_mission_list()
        
        return mission_id
        
    def refresh_mission_list(self):
        """Refresh the mission list display"""
        self.mission_list.clear()
        
        for mission_id, mission in self.missions.items():
            item = QListWidgetItem()
            item.setData(Qt.UserRole, mission_id)
            
            # Create mission display widget
            widget = MissionListItem(mission)
            item.setSizeHint(widget.sizeHint())
            
            self.mission_list.addItem(item)
            self.mission_list.setItemWidget(item, widget)
            
    def filter_missions(self, search_text):
        """Filter missions based on search text"""
        for i in range(self.mission_list.count()):
            item = self.mission_list.item(i)
            widget = self.mission_list.itemWidget(item)
            
            if search_text.lower() in widget.mission['name'].lower():
                item.setHidden(False)
            else:
                item.setHidden(True)
                
    def on_mission_selected(self, item):
        """Handle mission selection"""
        mission_id = item.data(Qt.UserRole)
        if mission_id in self.missions:
            self.mission_selected.emit(self.missions[mission_id])
            
    def load_selected_mission(self):
        """Load the selected mission"""
        current_item = self.mission_list.currentItem()
        if current_item:
            mission_id = current_item.data(Qt.UserRole)
            if mission_id in self.missions:
                self.mission_selected.emit(self.missions[mission_id])
                
    def delete_selected_mission(self):
        """Delete the selected mission"""
        current_item = self.mission_list.currentItem()
        if current_item:
            mission_id = current_item.data(Qt.UserRole)
            if mission_id in self.missions:
                mission_name = self.missions[mission_id]['name']
                
                reply = QMessageBox.question(
                    self, "Delete Mission",
                    f"Are you sure you want to delete '{mission_name}'?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    del self.missions[mission_id]
                    self.save_library()
                    self.refresh_mission_list()
                    self.mission_deleted.emit(mission_id)
                    
    def export_selected_mission(self):
        """Export the selected mission to a file"""
        current_item = self.mission_list.currentItem()
        if current_item:
            mission_id = current_item.data(Qt.UserRole)
            if mission_id in self.missions:
                mission = self.missions[mission_id]
                
                filename, _ = QFileDialog.getSaveFileName(
                    self, "Export Mission",
                    f"{mission['name']}.json",
                    "JSON Files (*.json)"
                )
                
                if filename:
                    try:
                        with open(filename, 'w') as f:
                            json.dump(mission, f, indent=2)
                        QMessageBox.information(self, "Success", "Mission exported successfully!")
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to export mission: {e}")
                        
    def update_button_states(self):
        """Update button enabled states based on selection"""
        has_selection = self.mission_list.currentItem() is not None
        self.load_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        self.export_btn.setEnabled(has_selection)

class MissionListItem(QWidget):
    """Individual mission item widget for the library list"""
    
    def __init__(self, mission, parent=None):
        super().__init__(parent)
        self.mission = mission
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Mission name
        name_label = QLabel(self.mission['name'])
        name_label.setFont(QFont("Arial", 12, QFont.Bold))
        name_label.setStyleSheet("color: white;")
        layout.addWidget(name_label)
        
        # Mission details
        details_layout = QHBoxLayout()
        
        # Type
        type_label = QLabel(f"Type: {self.mission['type']}")
        type_label.setStyleSheet("color: #CCCCCC; font-size: 10px;")
        details_layout.addWidget(type_label)
        
        # Created date
        created_date = datetime.fromisoformat(self.mission['created']).strftime("%Y-%m-%d %H:%M")
        date_label = QLabel(f"Created: {created_date}")
        date_label.setStyleSheet("color: #888888; font-size: 10px;")
        details_layout.addWidget(date_label)
        
        layout.addLayout(details_layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

class MissionImportDialog(QDialog):
    """Dialog for importing missions from files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Mission")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path = QLineEdit()
        self.file_path.setPlaceholderText("Select mission file...")
        file_layout.addWidget(self.file_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # Mission preview
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(200)
        self.preview_text.setPlaceholderText("Mission preview will appear here...")
        layout.addWidget(QLabel("Mission Preview:"))
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.accept)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def browse_file(self):
        """Browse for mission file"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select Mission File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            self.file_path.setText(filename)
            self.load_preview(filename)
            
    def load_preview(self, filename):
        """Load and display mission preview"""
        try:
            with open(filename, 'r') as f:
                mission_data = json.load(f)
                
            # Format preview
            preview = f"""
Mission Name: {mission_data.get('name', 'Unknown')}
Mission Type: {mission_data.get('type', 'Unknown')}
Created: {mission_data.get('created', 'Unknown')}

Mission Data:
{json.dumps(mission_data.get('data', {}), indent=2)}
            """
            
            self.preview_text.setPlainText(preview)
            self.import_btn.setEnabled(True)
            
        except Exception as e:
            self.preview_text.setPlainText(f"Error loading file: {e}")
            self.import_btn.setEnabled(False)
            
    def get_mission_data(self):
        """Get the loaded mission data"""
        try:
            with open(self.file_path.text(), 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load mission: {e}")
            return None 