#!/usr/bin/env python3
"""
Responsive Layout Management System
Provides responsive design for different screen sizes and orientations
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QStackedWidget, QGridLayout,
                              QApplication, QMainWindow)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor

class ResponsiveLayoutManager(QObject):
    """Manages responsive layouts for different screen sizes"""
    
    layout_changed = pyqtSignal(str)  # Emits new layout type
    
    def __init__(self):
        super().__init__()
        self.breakpoints = {
            'mobile': 480,
            'tablet': 768,
            'desktop': 1024,
            'large': 1440
        }
        self.current_layout = 'desktop'
        self.layout_configs = {
            'mobile': {
                'sidebar_width': 0,
                'sidebar_visible': False,
                'grid_columns': 1,
                'button_height': 44,
                'font_scale': 0.9,
                'margins': (10, 10, 10, 10)
            },
            'tablet': {
                'sidebar_width': 200,
                'sidebar_visible': True,
                'grid_columns': 2,
                'button_height': 40,
                'font_scale': 0.95,
                'margins': (15, 15, 15, 15)
            },
            'desktop': {
                'sidebar_width': 280,
                'sidebar_visible': True,
                'grid_columns': 4,
                'button_height': 36,
                'font_scale': 1.0,
                'margins': (20, 20, 20, 20)
            },
            'large': {
                'sidebar_width': 320,
                'sidebar_visible': True,
                'grid_columns': 4,
                'button_height': 36,
                'font_scale': 1.1,
                'margins': (25, 25, 25, 25)
            }
        }
        
    def get_current_breakpoint(self, width):
        """Determine current breakpoint based on width"""
        if width < self.breakpoints['mobile']:
            return 'mobile'
        elif width < self.breakpoints['tablet']:
            return 'tablet'
        elif width < self.breakpoints['desktop']:
            return 'desktop'
        else:
            return 'large'
            
    def apply_responsive_layout(self, main_widget):
        """Apply responsive layout to main widget"""
        def on_resize():
            width = main_widget.width()
            new_breakpoint = self.get_current_breakpoint(width)
            
            if new_breakpoint != self.current_layout:
                self.current_layout = new_breakpoint
                self.update_layout_for_breakpoint(main_widget, new_breakpoint)
                self.layout_changed.emit(new_breakpoint)
                
        # Connect resize event
        main_widget.resizeEvent = lambda event: on_resize()
        
        # Apply initial layout
        initial_breakpoint = self.get_current_breakpoint(main_widget.width())
        self.update_layout_for_breakpoint(main_widget, initial_breakpoint)
        
    def update_layout_for_breakpoint(self, widget, breakpoint):
        """Update layout based on breakpoint"""
        config = self.layout_configs.get(breakpoint, self.layout_configs['desktop'])
        
        # Apply sidebar configuration
        self.apply_sidebar_config(widget, config)
        
        # Apply grid configuration
        self.apply_grid_config(widget, config)
        
        # Apply button sizing
        self.apply_button_config(widget, config)
        
        # Apply font scaling
        self.apply_font_config(widget, config)
        
        # Apply margins
        self.apply_margin_config(widget, config)
        
    def apply_sidebar_config(self, widget, config):
        """Apply sidebar configuration"""
        # Find sidebar
        sidebar = self.find_widget_by_name(widget, 'sidebar')
        if sidebar:
            if config['sidebar_visible']:
                sidebar.setMaximumWidth(config['sidebar_width'])
                sidebar.setVisible(True)
            else:
                sidebar.setMaximumWidth(0)
                sidebar.setVisible(False)
                
    def apply_grid_config(self, widget, config):
        """Apply grid configuration"""
        # Find grid layouts
        for grid in widget.findChildren(QGridLayout):
            # Reset column stretches
            for i in range(grid.columnCount()):
                grid.setColumnStretch(i, 0)
                
            # Set new column configuration
            for i in range(config['grid_columns']):
                grid.setColumnStretch(i, 1)
                
    def apply_button_config(self, widget, config):
        """Apply button configuration"""
        for button in widget.findChildren(QPushButton):
            button.setMinimumHeight(config['button_height'])
            
    def apply_font_config(self, widget, config):
        """Apply font configuration"""
        base_font = widget.font()
        new_size = int(base_font.pointSize() * config['font_scale'])
        base_font.setPointSize(new_size)
        widget.setFont(base_font)
        
    def apply_margin_config(self, widget, config):
        """Apply margin configuration"""
        if hasattr(widget, 'layout'):
            widget.layout().setContentsMargins(*config['margins'])
            
    def find_widget_by_name(self, parent, name):
        """Find widget by object name"""
        for child in parent.findChildren(QWidget):
            if child.objectName() == name:
                return child
        return None

class ResponsiveCard(QFrame):
    """Responsive card that adapts to different screen sizes"""
    
    def __init__(self, title="", content="", parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the responsive card UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(self.title_label)
        
        # Content
        self.content_label = QLabel(self.content)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: white;")
        layout.addWidget(self.content_label)
        
        # Apply styling
        self.setStyleSheet("""
            ResponsiveCard {
                background-color: #1a2332;
                border: 1px solid #2d3748;
                border-radius: 8px;
                margin: 5px;
            }
            ResponsiveCard:hover {
                border-color: #00d4aa;
            }
        """)
        
    def adapt_to_screen_size(self, screen_width):
        """Adapt card to different screen sizes"""
        if screen_width < 480:  # Mobile
            self.setMinimumSize(200, 150)
            self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        elif screen_width < 768:  # Tablet
            self.setMinimumSize(250, 180)
            self.title_label.setFont(QFont("Arial", 13, QFont.Bold))
        elif screen_width < 1024:  # Desktop
            self.setMinimumSize(300, 200)
            self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        else:  # Large
            self.setMinimumSize(350, 220)
            self.title_label.setFont(QFont("Arial", 15, QFont.Bold))

class ResponsiveGrid(QWidget):
    """Responsive grid that adapts to different screen sizes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(15)
        self.cards = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the responsive grid UI"""
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        
    def add_card(self, card, row=None, col=None):
        """Add a card to the grid"""
        self.cards.append(card)
        
        if row is None or col is None:
            # Auto-position based on current grid
            current_count = len(self.cards) - 1
            current_columns = self.get_current_columns()
            row = current_count // current_columns
            col = current_count % current_columns
            
        self.grid_layout.addWidget(card, row, col)
        
    def get_current_columns(self):
        """Get current number of columns based on screen size"""
        screen_width = self.width()
        
        if screen_width < 480:  # Mobile
            return 1
        elif screen_width < 768:  # Tablet
            return 2
        elif screen_width < 1024:  # Desktop
            return 3
        else:  # Large
            return 4
            
    def adapt_layout(self, screen_width):
        """Adapt grid layout to screen size"""
        # Clear current layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        # Re-add cards with new positioning
        columns = self.get_current_columns()
        for i, card in enumerate(self.cards):
            row = i // columns
            col = i % columns
            self.grid_layout.addWidget(card, row, col)
            
        # Update card sizes
        for card in self.cards:
            if hasattr(card, 'adapt_to_screen_size'):
                card.adapt_to_screen_size(screen_width)

class ResponsiveSidebar(QFrame):
    """Responsive sidebar that adapts to different screen sizes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the responsive sidebar UI"""
        self.setStyleSheet("""
            ResponsiveSidebar {
                background-color: #1a2332;
                border-right: 1px solid #2d3748;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Logo area
        self.logo_label = QLabel("🚁")
        self.logo_label.setFont(QFont("Arial", 24))
        self.logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.logo_label)
        
        # Navigation area
        self.nav_widget = QWidget()
        self.nav_layout = QVBoxLayout(self.nav_widget)
        self.nav_layout.setSpacing(5)
        layout.addWidget(self.nav_widget)
        
        layout.addStretch()
        
    def adapt_to_screen_size(self, screen_width):
        """Adapt sidebar to different screen sizes"""
        if screen_width < 480:  # Mobile
            self.setMaximumWidth(0)
            self.setVisible(False)
        elif screen_width < 768:  # Tablet
            self.setMaximumWidth(200)
            self.setVisible(True)
            self.logo_label.setFont(QFont("Arial", 20))
        elif screen_width < 1024:  # Desktop
            self.setMaximumWidth(280)
            self.setVisible(True)
            self.logo_label.setFont(QFont("Arial", 24))
        else:  # Large
            self.setMaximumWidth(320)
            self.setVisible(True)
            self.logo_label.setFont(QFont("Arial", 28))

class ResponsiveMainWindow(QMainWindow):
    """Main window with responsive layout support"""
    
    def __init__(self):
        super().__init__()
        self.responsive_manager = ResponsiveLayoutManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the responsive main window UI"""
        self.setWindowTitle("Responsive Flight Generator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        self.sidebar = ResponsiveSidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QWidget()
        content_layout = QVBoxLayout(self.content_area)
        
        # Responsive grid
        self.responsive_grid = ResponsiveGrid()
        content_layout.addWidget(self.responsive_grid)
        
        main_layout.addWidget(self.content_area)
        
        # Apply responsive layout
        self.responsive_manager.apply_responsive_layout(self)
        
        # Connect layout change signal
        self.responsive_manager.layout_changed.connect(self.on_layout_changed)
        
    def on_layout_changed(self, new_layout):
        """Handle layout changes"""
        print(f"Layout changed to: {new_layout}")
        
        # Adapt components to new layout
        screen_width = self.width()
        
        if hasattr(self, 'sidebar'):
            self.sidebar.adapt_to_screen_size(screen_width)
            
        if hasattr(self, 'responsive_grid'):
            self.responsive_grid.adapt_layout(screen_width)
            
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        
        # Trigger responsive layout update
        self.responsive_manager.apply_responsive_layout(self)

# Global responsive manager instance
responsive_manager = ResponsiveLayoutManager()

def apply_responsive_layout(widget):
    """Global function to apply responsive layout"""
    return responsive_manager.apply_responsive_layout(widget)
