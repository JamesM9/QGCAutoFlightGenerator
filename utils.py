#!/usr/bin/env python3
"""
Utility functions for VERSATILE UAS Flight Generator
"""

import sys
import os

def get_map_html_path():
    """
    Returns the path to map.html file, whether running from development or installed location.
    """
    # Check if running as PyInstaller executable
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = os.path.dirname(sys.executable)
    else:
        # Running from development
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Look for map.html in the base path
    map_path = os.path.join(base_path, 'map.html')
    if os.path.exists(map_path):
        return map_path
    
    # Fallback to enhanced_map.html
    enhanced_map_path = os.path.join(base_path, 'enhanced_map.html')
    if os.path.exists(enhanced_map_path):
        return enhanced_map_path
    
    # Final fallback
    return os.path.join(base_path, 'map.html')

def get_dark_theme():
    """Get the dark theme stylesheet"""
    return """
        QMainWindow {
            background-color: #1E1E1E;
            color: white;
        }
        QWidget {
            background-color: #1E1E1E;
            color: white;
        }
        QListWidget {
            background-color: #2C2C2C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
        }
        QListWidget::item {
            padding: 8px 12px;
            font-size: 13px;
            border-bottom: 1px solid #3C3C3C;
        }
        QListWidget::item:selected {
            background-color: #FFD700;
            color: #1E1E1E;
            font-weight: bold;
        }
        QListWidget::item:hover {
            background-color: #3C3C3C;
        }
        QStackedWidget {
            background-color: #1E1E1E;
        }
        QLabel {
            color: white;
        }
        QPushButton {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4C4C4C;
            border-color: #666666;
        }
        QPushButton:pressed {
            background-color: #2C2C2C;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 4px;
            text-align: center;
            background-color: #2C2C2C;
            color: white;
        }
        QProgressBar::chunk {
            background-color: #FFD700;
            border-radius: 3px;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
            color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px 0 4px;
            color: white;
        }
        QScrollBar:vertical {
            background-color: #2C2C2C;
            width: 12px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 6px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QComboBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid white;
        }
        QLineEdit {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #3C3C3C;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 5px;
        }
    """
