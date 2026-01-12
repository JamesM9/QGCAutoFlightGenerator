#!/usr/bin/env python3
"""
Adaptive Layout System
Provides dynamic component sizing based on content and screen size
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QFrame, QPushButton, QTextEdit, QTableWidget,
                              QGridLayout, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QRect, QObject
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QColor, QPixmap

class ScreenBreakpoint:
    """Screen size breakpoints for responsive design"""
    MOBILE = 768
    SMALL = 1366
    MEDIUM = 1920
    LARGE = 2560

class AdaptiveLayoutManager(QObject):
    """Manages adaptive layouts for different screen sizes"""
    
    layout_changed = pyqtSignal(str)  # Emits new breakpoint
    
    def __init__(self):
        super().__init__()
        self.breakpoints = {
            'mobile': ScreenBreakpoint.MOBILE,
            'small': ScreenBreakpoint.SMALL,
            'medium': ScreenBreakpoint.MEDIUM,
            'large': ScreenBreakpoint.LARGE
        }
        
        self.layout_configs = {
            'mobile': {
                'font_size': 10,
                'padding': 10,
                'spacing': 8,
                'columns': 1,
                'card_height': 120,
                'button_height': 40
            },
            'small': {
                'font_size': 11,
                'padding': 15,
                'spacing': 12,
                'columns': 2,
                'card_height': 140,
                'button_height': 45
            },
            'medium': {
                'font_size': 12,
                'padding': 20,
                'spacing': 15,
                'columns': 3,
                'card_height': 160,
                'button_height': 50
            },
            'large': {
                'font_size': 14,
                'padding': 25,
                'spacing': 20,
                'columns': 4,
                'card_height': 180,
                'button_height': 55
            }
        }
        
        self.current_breakpoint = 'medium'
        
    def get_current_breakpoint(self, width):
        """Get current breakpoint based on screen width"""
        if width < self.breakpoints['mobile']:
            return 'mobile'
        elif width < self.breakpoints['small']:
            return 'small'
        elif width < self.breakpoints['medium']:
            return 'medium'
        else:
            return 'large'
            
    def apply_adaptive_layout(self, main_widget):
        """Apply adaptive layout to main widget"""
        width = main_widget.width()
        new_breakpoint = self.get_current_breakpoint(width)
        
        if new_breakpoint != self.current_breakpoint:
            self.current_breakpoint = new_breakpoint
            self.update_layout_for_breakpoint(main_widget, new_breakpoint)
            self.layout_changed.emit(new_breakpoint)
            
    def update_layout_for_breakpoint(self, widget, breakpoint):
        """Update layout for specific breakpoint"""
        config = self.layout_configs[breakpoint]
        
        # Apply to all child widgets recursively
        self.apply_config_to_widget(widget, config)
        
    def apply_config_to_widget(self, widget, config):
        """Apply configuration to a widget and its children"""
        # Apply font size
        if hasattr(widget, 'setFont'):
            current_font = widget.font()
            current_font.setPointSize(config['font_size'])
            widget.setFont(current_font)
            
        # Apply padding and spacing to layouts
        if hasattr(widget, 'layout'):
            layout = widget.layout()
            if layout:
                layout.setContentsMargins(config['padding'], config['padding'], 
                                        config['padding'], config['padding'])
                layout.setSpacing(config['spacing'])
                
        # Apply to children
        for child in widget.findChildren(QWidget):
            self.apply_config_to_widget(child, config)

class AdaptiveCard(QFrame):
    """Card widget that adapts to content and screen size"""
    
    def __init__(self, title="", content="", icon_path=None, color="#00d4aa", parent=None):
        super().__init__(parent)
        self.title = title
        self.content = content
        self.icon_path = icon_path
        self.color = color
        self.adaptive_manager = AdaptiveLayoutManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the adaptive card UI"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.setMidLineWidth(1)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {self.color};")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        
        # Content
        if self.content:
            self.content_label = QLabel(self.content)
            self.content_label.setWordWrap(True)
            self.content_label.setStyleSheet("color: white;")
            layout.addWidget(self.content_label)
            
        # Icon (if provided)
        if self.icon_path:
            self.icon_label = QLabel()
            self.icon_label.setPixmap(QPixmap(self.icon_path).scaled(32, 32, Qt.KeepAspectRatio))
            self.icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.icon_label)
            
        layout.addStretch()
        
        # Apply adaptive sizing
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(120)
        
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet(f"""
            AdaptiveCard {{
                background-color: #1a2332;
                border: 2px solid #2d3748;
                border-radius: 10px;
                margin: 5px;
            }}
            AdaptiveCard:hover {{
                border-color: {self.color};
                background-color: #2d3748;
            }}
        """)
        
    def resizeEvent(self, event):
        """Handle resize events for adaptive sizing"""
        super().resizeEvent(event)
        self.adapt_to_size(event.size())
        
    def adapt_to_size(self, size):
        """Adapt the card to the new size"""
        width = size.width()
        
        # Adjust font sizes based on width
        if width < 200:
            font_size = 10
            padding = 10
        elif width < 300:
            font_size = 11
            padding = 12
        else:
            font_size = 12
            padding = 15
            
        # Update fonts
        title_font = self.title_label.font()
        title_font.setPointSize(font_size + 1)
        self.title_label.setFont(title_font)
        
        if hasattr(self, 'content_label'):
            content_font = self.content_label.font()
            content_font.setPointSize(font_size)
            self.content_label.setFont(content_font)
            
        # Update layout margins
        layout = self.layout()
        if layout:
            layout.setContentsMargins(padding, padding, padding, padding)

class AdaptiveGrid(QWidget):
    """Grid layout that adapts to screen size"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.adaptive_manager = AdaptiveLayoutManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the adaptive grid UI"""
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(20, 20, 20, 20)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
    def add_widget(self, widget, row, col, row_span=1, col_span=1):
        """Add widget to grid with adaptive positioning"""
        self.grid_layout.addWidget(widget, row, col, row_span, col_span)
        
    def resizeEvent(self, event):
        """Handle resize events for adaptive grid"""
        super().resizeEvent(event)
        self.adapt_grid_to_size(event.size())
        
    def adapt_grid_to_size(self, size):
        """Adapt grid layout to new size"""
        width = size.width()
        
        # Determine number of columns based on width
        if width < 600:
            columns = 1
            spacing = 10
        elif width < 900:
            columns = 2
            spacing = 12
        elif width < 1200:
            columns = 3
            spacing = 15
        else:
            columns = 4
            spacing = 20
            
        # Update grid spacing
        self.grid_layout.setSpacing(spacing)
        
        # Update column stretches
        for i in range(columns):
            self.grid_layout.setColumnStretch(i, 1)

class AdaptiveTextArea(QTextEdit):
    """Text area that adapts to content size"""
    
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.placeholder = placeholder
        self.setPlaceholderText(placeholder)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the adaptive text area UI"""
        self.setMinimumHeight(100)
        self.setMaximumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Apply theme
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #00d4aa;
            }
        """)
        
    def resizeEvent(self, event):
        """Handle resize events for adaptive sizing"""
        super().resizeEvent(event)
        self.adapt_to_content()
        
    def adapt_to_content(self):
        """Adapt height to content"""
        document_height = self.document().size().height()
        viewport_height = self.viewport().height()
        
        # Calculate optimal height
        optimal_height = min(max(document_height + 20, 100), 300)
        
        if abs(optimal_height - self.height()) > 10:
            self.setFixedHeight(int(optimal_height))

class AdaptiveButton(QPushButton):
    """Button that adapts to content and screen size"""
    
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.icon_path = icon_path
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the adaptive button UI"""
        if self.icon_path:
            self.setIcon(QPixmap(self.icon_path))
            
        self.setMinimumHeight(40)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        
        # Apply theme
        self.setStyleSheet("""
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
        """)
        
    def resizeEvent(self, event):
        """Handle resize events for adaptive sizing"""
        super().resizeEvent(event)
        self.adapt_to_size(event.size())
        
    def adapt_to_size(self, size):
        """Adapt button to new size"""
        width = size.width()
        
        # Adjust padding based on width
        if width < 100:
            padding = "5px 10px"
            font_size = 10
        elif width < 150:
            padding = "8px 15px"
            font_size = 11
        else:
            padding = "10px 20px"
            font_size = 12
            
        # Update styling
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: {padding};
                font-size: {font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4a5568;
                border-color: #00d4aa;
            }}
            QPushButton:pressed {{
                background-color: #00d4aa;
                color: #1a2332;
            }}
        """)

class AdaptiveTable(QTableWidget):
    """Table that adapts column widths to content"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the adaptive table UI"""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Apply theme
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                gridline-color: #4a5568;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
            QHeaderView::section {
                background-color: #1a2332;
                color: white;
                padding: 8px;
                border: 1px solid #4a5568;
                font-weight: bold;
            }
        """)
        
    def resizeEvent(self, event):
        """Handle resize events for adaptive column sizing"""
        super().resizeEvent(event)
        self.adapt_columns_to_content()
        
    def adapt_columns_to_content(self):
        """Adapt column widths to content"""
        if self.columnCount() == 0:
            return
            
        # Calculate optimal column widths
        total_width = self.viewport().width()
        column_widths = []
        
        for col in range(self.columnCount()):
            max_width = 0
            
            # Check header width
            header_text = self.horizontalHeaderItem(col).text() if self.horizontalHeaderItem(col) else ""
            header_width = self.fontMetrics().horizontalAdvance(header_text) + 20
            
            # Check content widths
            for row in range(self.rowCount()):
                item = self.item(row, col)
                if item:
                    text_width = self.fontMetrics().horizontalAdvance(item.text()) + 20
                    max_width = max(max_width, text_width)
                    
            # Use the larger of header or content width
            max_width = max(max_width, header_width)
            column_widths.append(max_width)
            
        # Distribute remaining space proportionally
        total_content_width = sum(column_widths)
        if total_content_width < total_width:
            # Expand columns proportionally
            for i, width in enumerate(column_widths):
                if total_content_width > 0:
                    ratio = width / total_content_width
                    column_widths[i] = int(ratio * total_width)
                    
        # Apply column widths
        for col, width in enumerate(column_widths):
            self.setColumnWidth(col, width)

# Global adaptive layout manager
adaptive_layout_manager = AdaptiveLayoutManager()
