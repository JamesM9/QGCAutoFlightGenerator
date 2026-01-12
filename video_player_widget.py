#!/usr/bin/env python3
"""
Video Player Widget for Tutorial System
Supports both embedded video players and external video links
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import webbrowser


class VideoPlayerWidget(QWidget):
    """Widget for playing instructional videos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the video player UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Video player (initially hidden)
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(200)
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background-color: #1a1a1a;
                border: 2px solid #4a5568;
                border-radius: 8px;
            }
        """)
        self.video_widget.hide()
        
        # Media player
        self.media_player = QMediaPlayer()
        self.media_player.setVideoOutput(self.video_widget)
        
        # Video controls
        self.controls_frame = QFrame()
        self.controls_frame.setStyleSheet("""
            QFrame {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.controls_frame.hide()
        
        controls_layout = QHBoxLayout(self.controls_frame)
        
        # Play/Pause button
        self.play_btn = QPushButton("▶️ Play")
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #00d4aa;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00b894;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        controls_layout.addWidget(self.play_btn)
        
        # Stop button
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_video)
        controls_layout.addWidget(self.stop_btn)
        
        controls_layout.addStretch()
        
        # Volume control
        volume_label = QLabel("🔊")
        volume_label.setStyleSheet("color: white; font-size: 14px;")
        controls_layout.addWidget(volume_label)
        
        # Close video button
        self.close_btn = QPushButton("❌ Close Video")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.close_btn.clicked.connect(self.close_video)
        controls_layout.addWidget(self.close_btn)
        
        # Add widgets to layout
        layout.addWidget(self.video_widget)
        layout.addWidget(self.controls_frame)
        
        # Connect media player signals
        self.media_player.stateChanged.connect(self.on_state_changed)
        
    def play_video(self, video_path):
        """Play a local video file"""
        if os.path.exists(video_path):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
            self.video_widget.show()
            self.controls_frame.show()
            self.media_player.play()
        else:
            QMessageBox.warning(self, "Error", f"Video file not found: {video_path}")
    
    def play_network_video(self, url):
        """Play a network video (streaming)"""
        self.media_player.setMedia(QMediaContent(QUrl(url)))
        self.video_widget.show()
        self.controls_frame.show()
        self.media_player.play()
    
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def stop_video(self):
        """Stop video playback"""
        self.media_player.stop()
    
    def close_video(self):
        """Close video player"""
        self.media_player.stop()
        self.video_widget.hide()
        self.controls_frame.hide()
    
    def on_state_changed(self, state):
        """Handle media player state changes"""
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸️ Pause")
        else:
            self.play_btn.setText("▶️ Play")


class VideoLinkWidget(QWidget):
    """Widget for displaying video links with embedded player option"""
    
    def __init__(self, title, url, description, parent=None):
        super().__init__(parent)
        self.title = title
        self.url = url
        self.description = description
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the video link UI"""
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        
        # Video info
        info_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa;")
        info_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(self.description)
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setStyleSheet("color: #a0aec0;")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(5)
        
        # Open in browser button
        browser_btn = QPushButton("🌐 Open in Browser")
        browser_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3748;
                color: #00d4aa;
                border: 1px solid #4a5568;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
        """)
        browser_btn.clicked.connect(self.open_in_browser)
        button_layout.addWidget(browser_btn)
        
        # Try embedded player button (for local files)
        if self.url.startswith('file://') or not self.url.startswith('http'):
            embed_btn = QPushButton("📺 Play Embedded")
            embed_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d3748;
                    color: #f39c12;
                    border: 1px solid #4a5568;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 9px;
                }
                QPushButton:hover {
                    background-color: #4a5568;
                    border-color: #f39c12;
                }
            """)
            embed_btn.clicked.connect(self.play_embedded)
            button_layout.addWidget(embed_btn)
        
        layout.addLayout(button_layout)
        
    def open_in_browser(self):
        """Open video in default browser"""
        try:
            webbrowser.open(self.url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open video link: {str(e)}")
    
    def play_embedded(self):
        """Play video in embedded player"""
        # This would need to be connected to a parent widget with video player
        # For now, just show a message
        QMessageBox.information(self, "Embedded Player", 
                               "Embedded video player would open here.\n"
                               "This feature requires additional setup for video playback.")


class VideoSectionWidget(QWidget):
    """Widget for organizing video links in sections"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title
        self.video_player = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the video section UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Section title
        title_label = QLabel(f"📹 {self.title}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #00d4aa; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Video links container
        self.video_links_layout = QVBoxLayout()
        self.video_links_layout.setSpacing(5)
        layout.addLayout(self.video_links_layout)
        
    def add_video_link(self, title, url, description):
        """Add a video link to the section"""
        video_widget = VideoLinkWidget(title, url, description)
        self.video_links_layout.addWidget(video_widget)
        
    def set_video_player(self, video_player):
        """Set the video player widget for embedded playback"""
        self.video_player = video_player
