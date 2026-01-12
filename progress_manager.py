#!/usr/bin/env python3
"""
Progress and Status Management System
Provides progress indicators and status updates for long operations
"""

import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QFrame, QTextEdit,
                              QMessageBox, QApplication, QWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor

class ProgressManager(QObject):
    """Manages progress indicators and status updates"""
    
    progress_updated = pyqtSignal(int, str)  # step, message
    operation_completed = pyqtSignal(bool, str)  # success, message
    operation_cancelled = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.current_operation = None
        self.progress_dialog = None
        self.is_cancelled = False
        
    def show_progress(self, operation_name, steps, parent=None):
        """Show progress dialog for multi-step operations"""
        self.progress_dialog = ProgressDialog(operation_name, steps, parent)
        self.progress_dialog.cancelled.connect(self.cancel_operation)
        self.progress_dialog.show()
        
        # Connect signals
        self.progress_updated.connect(self.progress_dialog.update_progress)
        self.operation_completed.connect(self.progress_dialog.operation_finished)
        
        return self.progress_dialog
        
    def update_progress(self, step, message):
        """Update progress bar and status message"""
        self.progress_updated.emit(step, message)
        
    def complete_operation(self, success, message):
        """Mark operation as completed"""
        self.operation_completed.emit(success, message)
        
    def cancel_operation(self):
        """Cancel the current operation"""
        self.is_cancelled = True
        self.operation_cancelled.emit()
        
    def reset(self):
        """Reset the progress manager"""
        self.is_cancelled = False
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None

class ProgressDialog(QDialog):
    """Progress dialog with detailed status information"""
    
    cancelled = pyqtSignal()
    
    def __init__(self, operation_name, steps, parent=None):
        super().__init__(parent)
        self.operation_name = operation_name
        self.total_steps = steps
        self.current_step = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the progress dialog UI"""
        self.setWindowTitle(f"Processing: {self.operation_name}")
        self.setFixedSize(700, 500)  # Increased size for better comfort
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        
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
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 5px;
                text-align: center;
                background-color: #2d3748;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 5px;
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
        layout.setContentsMargins(40, 40, 40, 40)  # Increased margins for better spacing
        
        # Header
        header_layout = QHBoxLayout()
        
        # Icon
        icon_label = QLabel("⚙️")
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Operation info
        info_layout = QVBoxLayout()
        
        operation_label = QLabel(self.operation_name)
        operation_label.setFont(QFont("Arial", 14, QFont.Bold))
        operation_label.setStyleSheet("color: #00d4aa;")
        info_layout.addWidget(operation_label)
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setFont(QFont("Arial", 11))
        info_layout.addWidget(self.status_label)
        
        header_layout.addLayout(info_layout)
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Step %v of %m (%p%)")
        layout.addWidget(self.progress_bar)
        
        # Detailed status
        status_label = QLabel("Detailed Status:")
        status_label.setFont(QFont("Arial", 12, QFont.Bold))
        status_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)  # Increased height for better visibility
        self.status_text.setReadOnly(True)
        self.status_text.setPlainText("Starting operation...")
        layout.addWidget(self.status_text)
        
        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("❌ Cancel")
        self.cancel_btn.clicked.connect(self.cancel_operation)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def update_progress(self, step, message):
        """Update progress bar and status message"""
        self.current_step = step
        self.progress_bar.setValue(step)
        self.status_label.setText(message)
        
        # Add to detailed status
        current_text = self.status_text.toPlainText()
        timestamp = QTimer().remainingTime()  # Simple timestamp
        new_line = f"Step {step}: {message}"
        self.status_text.setPlainText(current_text + "\n" + new_line)
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def operation_finished(self, success, message):
        """Handle operation completion"""
        if success:
            self.status_label.setText("✅ " + message)
            self.cancel_btn.setText("✓ Close")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.accept)
        else:
            self.status_label.setText("❌ " + message)
            self.cancel_btn.setText("✕ Close")
            self.cancel_btn.clicked.disconnect()
            self.cancel_btn.clicked.connect(self.accept)
            
        # Add completion message to status
        current_text = self.status_text.toPlainText()
        completion_msg = f"\n{'✅ Operation completed successfully' if success else '❌ Operation failed'}: {message}"
        self.status_text.setPlainText(current_text + completion_msg)
        
    def cancel_operation(self):
        """Cancel the operation"""
        reply = QMessageBox.question(
            self, 
            "Cancel Operation", 
            "Are you sure you want to cancel this operation?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cancelled.emit()
            self.accept()

class StatusBar(QWidget):
    """Status bar widget for showing current status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup status bar UI"""
        self.setFixedHeight(30)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Status icon
        self.status_icon = QLabel("🟢")
        self.status_icon.setFont(QFont("Arial", 12))
        layout.addWidget(self.status_icon)
        
        # Status message
        self.status_message = QLabel("Ready")
        self.status_message.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_message)
        
        layout.addStretch()
        
        # Progress indicator (hidden by default)
        self.progress_indicator = QProgressBar()
        self.progress_indicator.setFixedWidth(150)
        self.progress_indicator.setVisible(False)
        layout.addWidget(self.progress_indicator)
        
        # Apply styling
        self.setStyleSheet("""
            QWidget {
                background-color: #2d3748;
                border-top: 1px solid #4a5568;
            }
            QLabel {
                color: white;
            }
            QProgressBar {
                border: 1px solid #4a5568;
                border-radius: 3px;
                background-color: #1a2332;
                text-align: center;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
        """)
        
    def set_status(self, message, status_type="info"):
        """Set status message with type"""
        self.status_message.setText(message)
        
        # Set icon based on status type
        icons = {
            "info": "🟢",
            "warning": "🟡",
            "error": "🔴",
            "success": "✅",
            "loading": "⏳"
        }
        
        self.status_icon.setText(icons.get(status_type, "🟢"))
        
    def show_progress(self, show=True):
        """Show or hide progress indicator"""
        self.progress_indicator.setVisible(show)
        
    def set_progress(self, value, maximum=100):
        """Set progress bar value"""
        self.progress_indicator.setMaximum(maximum)
        self.progress_indicator.setValue(value)

class BackgroundWorker(QThread):
    """Background worker for long operations"""
    
    progress_updated = pyqtSignal(int, str)
    operation_completed = pyqtSignal(bool, str)
    
    def __init__(self, operation_func, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        self.is_cancelled = False
        
    def run(self):
        """Run the background operation"""
        try:
            # Connect progress signals
            if hasattr(self.operation_func, 'progress_updated'):
                self.operation_func.progress_updated.connect(self.progress_updated.emit)
                
            # Run the operation
            result = self.operation_func(*self.args, **self.kwargs)
            self.operation_completed.emit(True, "Operation completed successfully")
            
        except Exception as e:
            self.operation_completed.emit(False, f"Operation failed: {str(e)}")
            
    def cancel(self):
        """Cancel the operation"""
        self.is_cancelled = True
        self.terminate()
        self.wait()

# Global progress manager instance
progress_manager = ProgressManager()

def show_progress(operation_name, steps, parent=None):
    """Global function to show progress dialog"""
    return progress_manager.show_progress(operation_name, steps, parent)

def update_progress(step, message):
    """Global function to update progress"""
    progress_manager.update_progress(step, message)

def complete_operation(success, message):
    """Global function to complete operation"""
    progress_manager.complete_operation(success, message)
