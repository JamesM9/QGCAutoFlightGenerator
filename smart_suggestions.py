#!/usr/bin/env python3
"""
Smart Suggestions System
Provides intelligent defaults and recommendations based on user behavior and mission context
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QListWidget, QListWidgetItem,
                              QDialog, QDialogButtonBox, QTextEdit, QComboBox,
                              QSpinBox, QCheckBox, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter

class MissionTemplate:
    """Mission template with predefined settings"""
    
    def __init__(self, name, description, mission_type, settings):
        self.name = name
        self.description = description
        self.mission_type = mission_type
        self.settings = settings
        self.usage_count = 0
        self.last_used = None
        self.created_date = datetime.now().isoformat()
        
    def to_dict(self):
        """Convert template to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'mission_type': self.mission_type,
            'settings': self.settings,
            'usage_count': self.usage_count,
            'last_used': self.last_used,
            'created_date': self.created_date
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create template from dictionary"""
        template = cls(
            data['name'],
            data['description'],
            data['mission_type'],
            data['settings']
        )
        template.usage_count = data.get('usage_count', 0)
        template.last_used = data.get('last_used')
        template.created_date = data.get('created_date', datetime.now().isoformat())
        return template

class UserBehaviorTracker:
    """Tracks user behavior for smart suggestions"""
    
    def __init__(self):
        self.mission_history = []
        self.settings_preferences = defaultdict(Counter)
        self.frequent_locations = Counter()
        self.usage_patterns = defaultdict(list)
        self.error_patterns = Counter()
        
    def record_mission_creation(self, mission_type, settings, location=None):
        """Record a mission creation event"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'mission_type': mission_type,
            'settings': settings,
            'location': location
        }
        self.mission_history.append(event)
        
        # Update usage patterns
        self.usage_patterns[mission_type].append(event)
        
        # Update settings preferences
        for key, value in settings.items():
            self.settings_preferences[f"{mission_type}_{key}"][value] += 1
            
        # Update location preferences
        if location:
            self.frequent_locations[location] += 1
    
    def record_error(self, error_type, context):
        """Record an error event"""
        self.error_patterns[f"{error_type}_{context}"] += 1
    
    def get_popular_settings(self, mission_type, setting_key):
        """Get most popular settings for a mission type"""
        key = f"{mission_type}_{setting_key}"
        if key in self.settings_preferences:
            return self.settings_preferences[key].most_common(3)
        return []
    
    def get_frequent_locations(self, limit=5):
        """Get most frequently used locations"""
        return self.frequent_locations.most_common(limit)
    
    def get_mission_type_preference(self):
        """Get user's preferred mission type"""
        mission_counts = Counter()
        for event in self.mission_history:
            mission_counts[event['mission_type']] += 1
        return mission_counts.most_common(1)[0][0] if mission_counts else None
    
    def get_recent_activity(self, days=7):
        """Get recent activity within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_events = []
        for event in self.mission_history:
            event_date = datetime.fromisoformat(event['timestamp'])
            if event_date >= cutoff_date:
                recent_events.append(event)
        return recent_events

class SmartSuggestionsEngine(QObject):
    """Engine for generating smart suggestions"""
    
    suggestion_ready = pyqtSignal(str, dict)  # suggestion_type, suggestion_data
    
    def __init__(self):
        super().__init__()
        self.behavior_tracker = UserBehaviorTracker()
        self.templates = {}
        self.suggestion_rules = {}
        self.load_templates()
        self.setup_suggestion_rules()
        
    def load_templates(self):
        """Load mission templates"""
        templates_file = "mission_templates.json"
        try:
            if os.path.exists(templates_file):
                with open(templates_file, 'r') as f:
                    data = json.load(f)
                    for template_name, template_data in data.items():
                        self.templates[template_name] = MissionTemplate.from_dict(template_data)
        except Exception as e:
            print(f"Error loading templates: {e}")
            self.create_default_templates()
    
    def save_templates(self):
        """Save mission templates"""
        templates_file = "mission_templates.json"
        try:
            data = {}
            for name, template in self.templates.items():
                data[name] = template.to_dict()
            
            with open(templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving templates: {e}")
    
    def create_default_templates(self):
        """Create default mission templates"""
        default_templates = {
            "Quick Delivery": MissionTemplate(
                "Quick Delivery",
                "Fast delivery mission with optimized route",
                "Delivery Route",
                {
                    "altitude": 100,
                    "waypoint_interval": 50,
                    "speed": "fast",
                    "safety_margin": 20
                }
            ),
            "High Precision Survey": MissionTemplate(
                "High Precision Survey",
                "Detailed survey with high precision waypoints",
                "Mapping Flight",
                {
                    "altitude": 80,
                    "waypoint_interval": 25,
                    "overlap": 80,
                    "camera_angle": 90
                }
            ),
            "Security Patrol": MissionTemplate(
                "Security Patrol",
                "Perimeter security patrol with geofencing",
                "Security Route",
                {
                    "altitude": 120,
                    "waypoint_interval": 75,
                    "geofence_buffer": 150,
                    "loiter_time": 30
                }
            ),
            "Infrastructure Inspection": MissionTemplate(
                "Infrastructure Inspection",
                "Detailed infrastructure inspection mission",
                "Tower Inspection",
                {
                    "altitude": 60,
                    "orbit_radius": 30,
                    "camera_angle": 45,
                    "inspection_height": 40
                }
            )
        }
        
        self.templates.update(default_templates)
        self.save_templates()
    
    def setup_suggestion_rules(self):
        """Setup suggestion rules"""
        self.suggestion_rules = {
            'altitude': {
                'delivery': {'min': 50, 'max': 150, 'default': 100},
                'mapping': {'min': 60, 'max': 120, 'default': 80},
                'security': {'min': 80, 'max': 200, 'default': 120},
                'inspection': {'min': 40, 'max': 100, 'default': 60}
            },
            'waypoint_interval': {
                'delivery': {'min': 25, 'max': 100, 'default': 50},
                'mapping': {'min': 15, 'max': 50, 'default': 25},
                'security': {'min': 50, 'max': 150, 'default': 75},
                'inspection': {'min': 20, 'max': 60, 'default': 40}
            },
            'safety_margin': {
                'default': 20,
                'urban': 30,
                'mountainous': 50,
                'water': 40
            }
        }
    
    def get_smart_defaults(self, mission_type, context=None):
        """Get smart defaults for a mission type"""
        defaults = {}
        
        # Get rule-based defaults
        if mission_type in self.suggestion_rules:
            for setting, rules in self.suggestion_rules[mission_type].items():
                defaults[setting] = rules['default']
        
        # Get user preference-based defaults
        user_prefs = self.behavior_tracker.get_popular_settings(mission_type, 'altitude')
        if user_prefs:
            defaults['altitude'] = user_prefs[0][0]
        
        user_prefs = self.behavior_tracker.get_popular_settings(mission_type, 'waypoint_interval')
        if user_prefs:
            defaults['waypoint_interval'] = user_prefs[0][0]
        
        # Apply context-specific adjustments
        if context:
            if context.get('terrain') == 'mountainous':
                defaults['safety_margin'] = self.suggestion_rules['safety_margin']['mountainous']
            elif context.get('environment') == 'urban':
                defaults['safety_margin'] = self.suggestion_rules['safety_margin']['urban']
        
        return defaults
    
    def get_template_suggestions(self, mission_type=None):
        """Get template suggestions based on user behavior"""
        suggestions = []
        
        # Get frequently used templates
        for template in self.templates.values():
            if mission_type is None or template.mission_type == mission_type:
                score = self.calculate_template_score(template)
                suggestions.append((template, score))
        
        # Sort by score (usage + recency)
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [template for template, score in suggestions[:5]]
    
    def calculate_template_score(self, template):
        """Calculate template suggestion score"""
        score = template.usage_count * 10  # Base score from usage
        
        # Recency bonus
        if template.last_used:
            last_used = datetime.fromisoformat(template.last_used)
            days_since = (datetime.now() - last_used).days
            if days_since < 7:
                score += 50  # Recent usage bonus
            elif days_since < 30:
                score += 20  # Recent usage bonus
        
        return score
    
    def get_location_suggestions(self, current_location=None):
        """Get location suggestions"""
        suggestions = []
        
        # Get frequently used locations
        frequent_locations = self.behavior_tracker.get_frequent_locations()
        for location, count in frequent_locations:
            if location != current_location:
                suggestions.append({
                    'type': 'frequent_location',
                    'location': location,
                    'usage_count': count,
                    'description': f"Used {count} times"
                })
        
        return suggestions
    
    def get_mission_suggestions(self, mission_type):
        """Get comprehensive suggestions for a specific mission type"""
        suggestions = []
        
        # Get mission description and applications
        mission_info = self.get_mission_info(mission_type)
        if mission_info:
            suggestions.append(f"📋 **{mission_type} - Applications & Use Cases:**")
            suggestions.append(f"   {mission_info['description']}")
            suggestions.append("")
            suggestions.append("🎯 **Common Applications:**")
            for app in mission_info['applications']:
                suggestions.append(f"   • {app}")
            suggestions.append("")
        
        # Get smart defaults for this mission type
        defaults = self.get_smart_defaults(mission_type.lower().replace(' ', '_'), {})
        if defaults:
            suggestions.append(f"⚙️ **Recommended Settings for {mission_type}:**")
            for setting, value in defaults.items():
                suggestions.append(f"   • {setting.replace('_', ' ').title()}: {value}")
            suggestions.append("")
        
        # Get template suggestions
        templates = self.get_template_suggestions(mission_type)
        if templates:
            suggestions.append(f"🎯 **Available Templates for {mission_type}:**")
            for template in templates[:3]:  # Show top 3 templates
                suggestions.append(f"   • {template.name}: {template.description}")
            suggestions.append("")
        
        # Get location suggestions
        locations = self.get_location_suggestions()
        if locations:
            suggestions.append("📍 **Frequently Used Locations:**")
            for location_data in locations[:3]:  # Show top 3 locations
                suggestions.append(f"   • {location_data['location']} (used {location_data['usage_count']} times)")
            suggestions.append("")
        
        # Add mission-specific tips
        mission_tips = self.get_mission_tips(mission_type)
        if mission_tips:
            suggestions.append("💡 **Mission-Specific Tips:**")
            for tip in mission_tips:
                suggestions.append(f"   • {tip}")
            suggestions.append("")
        
        # Add general best practices
        suggestions.append("🔧 **General Best Practices:**")
        suggestions.append("   • Always verify coordinates before mission execution")
        suggestions.append("   • Check weather conditions and wind forecasts")
        suggestions.append("   • Ensure adequate battery life for mission duration")
        suggestions.append("   • Test mission in simulation mode first")
        suggestions.append("   • Keep safety margins appropriate for terrain")
        suggestions.append("   • Follow local aviation regulations and airspace restrictions")
        
        return "\n".join(suggestions)
    
    def get_mission_info(self, mission_type):
        """Get mission description and common applications"""
        mission_info = {
            "Delivery Route": {
                "description": "Point-to-point delivery missions for transporting payloads between specific locations.",
                "applications": [
                    "Medical supply delivery to remote areas",
                    "Package delivery for e-commerce",
                    "Emergency supplies to disaster zones",
                    "Agricultural supplies to farms",
                    "Parts delivery for industrial maintenance",
                    "Food delivery to isolated communities",
                    "Document delivery between offices",
                    "Sample collection and return missions"
                ]
            },
            "Multi-Delivery": {
                "description": "Efficient multi-point delivery missions optimizing route for multiple destinations.",
                "applications": [
                    "Multiple package deliveries in urban areas",
                    "Medical supplies to multiple clinics",
                    "Agricultural supplies to multiple farms",
                    "Maintenance parts to multiple facilities",
                    "Food delivery to multiple restaurants",
                    "Document distribution to multiple offices",
                    "Emergency supplies to multiple locations",
                    "Sample collection from multiple sites"
                ]
            },
            "Security Route": {
                "description": "Perimeter security and surveillance missions with geofencing and patrol patterns.",
                "applications": [
                    "Industrial facility perimeter monitoring",
                    "Construction site security surveillance",
                    "Agricultural field protection",
                    "Event venue security monitoring",
                    "Border and coastal surveillance",
                    "Infrastructure protection (pipelines, power lines)",
                    "Wildlife conservation area monitoring",
                    "Military base perimeter security"
                ]
            },
            "Linear Flight": {
                "description": "Linear survey and inspection missions following straight paths or corridors.",
                "applications": [
                    "Pipeline inspection and monitoring",
                    "Power line and transmission tower inspection",
                    "Railway track and infrastructure monitoring",
                    "Highway and bridge inspection",
                    "Canal and waterway surveying",
                    "Fence line and border monitoring",
                    "Agricultural field row inspection",
                    "Coastal shoreline surveying"
                ]
            },
            "Tower Inspection": {
                "description": "Detailed inspection missions for vertical structures using orbital patterns.",
                "applications": [
                    "Cell tower and communication infrastructure",
                    "Wind turbine inspection and maintenance",
                    "Radio and TV broadcast towers",
                    "Power transmission towers",
                    "Water towers and storage tanks",
                    "Chimney and industrial stack inspection",
                    "Bridge support structure inspection",
                    "Building facade and rooftop inspection"
                ]
            },
            "A-to-B Mission": {
                "description": "Simple point-to-point missions for direct transportation or reconnaissance.",
                "applications": [
                    "Quick reconnaissance missions",
                    "Emergency response coordination",
                    "Search and rescue operations",
                    "Wildlife monitoring and tracking",
                    "Traffic monitoring and reporting",
                    "Weather observation missions",
                    "Emergency medical transport coordination",
                    "Simple cargo transport between points"
                ]
            },
            "Mapping Flight": {
                "description": "Area mapping and surveying missions using grid patterns for comprehensive coverage.",
                "applications": [
                    "Real estate and property surveying",
                    "Construction site progress monitoring",
                    "Agricultural field mapping and analysis",
                    "Environmental impact assessment",
                    "Archaeological site documentation",
                    "Forestry and vegetation mapping",
                    "Urban planning and development",
                    "Disaster damage assessment"
                ]
            },
            "Structure Scan": {
                "description": "3D scanning missions for complete structure analysis using orbital patterns.",
                "applications": [
                    "Building and structure 3D modeling",
                    "Historical monument documentation",
                    "Industrial facility 3D mapping",
                    "Mining and quarry volume calculations",
                    "Construction progress 3D monitoring",
                    "Archaeological site 3D documentation",
                    "Infrastructure 3D assessment",
                    "Real estate virtual tour creation"
                ]
            }
        }
        
        return mission_info.get(mission_type, {
            "description": "General mission planning for custom flight operations.",
            "applications": [
                "Custom flight operations",
                "Specialized surveying missions",
                "Research and development flights",
                "Training and demonstration flights"
            ]
        })
    
    def get_mission_tips(self, mission_type):
        """Get mission-specific tips and recommendations"""
        tips = {
            "Delivery Route": [
                "Use higher altitudes (100-150m) for longer delivery routes to avoid obstacles",
                "Consider payload weight when setting waypoint intervals (heavier payloads need wider turns)",
                "Plan return route to optimize battery usage and flight time",
                "Set appropriate loiter times (10-30s) at delivery points for safe payload release",
                "Use geofencing to ensure safe flight corridors",
                "Consider wind conditions for payload stability during delivery",
                "Plan for emergency landing zones along the route",
                "Test payload release mechanism before mission execution"
            ],
            "Multi-Delivery": [
                "Optimize route order to minimize total flight time and battery consumption",
                "Use consistent altitude (100-120m) for all delivery points to maintain efficiency",
                "Plan for payload drop/release mechanisms at each stop",
                "Consider weather conditions and wind patterns for multiple stops",
                "Set appropriate loiter times at each delivery point",
                "Use geofencing to define safe delivery zones",
                "Plan for battery swaps or charging stops for long multi-delivery missions",
                "Consider payload weight changes as deliveries are completed"
            ],
            "Security Route": [
                "Use geofencing to define patrol boundaries and prevent unauthorized flight",
                "Set appropriate loiter times (15-60s) at checkpoints for thorough surveillance",
                "Consider night vision capabilities for 24/7 patrol operations",
                "Plan escape routes and emergency landing zones in case of threats",
                "Use varying altitudes (80-200m) to avoid detection patterns",
                "Implement random patrol patterns to prevent predictability",
                "Consider weather conditions for optimal surveillance visibility",
                "Plan for multiple patrol shifts and battery management"
            ],
            "Linear Flight": [
                "Use consistent altitude (60-120m) for smooth data collection and analysis",
                "Set appropriate overlap (60-80%) for mapping missions to ensure complete coverage",
                "Consider wind direction for linear surveys to maintain consistent data quality",
                "Plan for battery swaps on long linear routes (every 15-20 minutes)",
                "Use geofencing to maintain safe distance from linear infrastructure",
                "Implement gradual altitude changes for terrain following",
                "Consider lighting conditions for optimal inspection visibility",
                "Plan for emergency landing zones along the linear route"
            ],
            "Tower Inspection": [
                "Use orbital patterns with 30-50m radius for comprehensive structure coverage",
                "Set appropriate camera angles (30-90°) for detailed inspection views",
                "Maintain safe distance (10-20m) from structures to prevent collisions",
                "Plan for multiple inspection passes at different heights and angles",
                "Use geofencing to define safe inspection boundaries",
                "Consider lighting conditions for optimal inspection visibility",
                "Implement gradual approach and departure patterns",
                "Plan for emergency procedures in case of structure proximity issues"
            ],
            "A-to-B Mission": [
                "Use direct routes for simple point-to-point missions to minimize flight time",
                "Consider terrain elevation for optimal altitude (50-150m above ground level)",
                "Plan for emergency landing zones along the route",
                "Set appropriate speed (5-15 m/s) based on mission requirements and weather",
                "Use geofencing to ensure safe flight corridors",
                "Consider wind conditions for efficient flight planning",
                "Plan for battery reserves (20-30%) for unexpected conditions",
                "Implement gradual altitude changes for terrain following"
            ],
            "Mapping Flight": [
                "Use grid patterns with 60-80% overlap for comprehensive area coverage",
                "Set appropriate camera angles (90° for nadir, 45° for oblique) for mapping quality",
                "Consider camera settings (resolution, ISO, shutter speed) for optimal image quality",
                "Plan for consistent lighting conditions (avoid harsh shadows)",
                "Use geofencing to define mapping boundaries",
                "Implement systematic flight patterns for complete coverage",
                "Consider ground control points for accurate georeferencing",
                "Plan for multiple flights for large area mapping"
            ],
            "Structure Scan": [
                "Use 3D orbital patterns with multiple passes at different heights (20-100m)",
                "Set appropriate camera angles (0-90°) for complete structure coverage",
                "Plan for multiple passes at different heights for detailed 3D reconstruction",
                "Consider structure size for optimal scan patterns and resolution",
                "Use geofencing to define safe scanning boundaries",
                "Implement gradual approach and departure patterns",
                "Consider lighting conditions for optimal scan quality",
                "Plan for emergency procedures in case of proximity issues"
            ]
        }
        
        return tips.get(mission_type, [
            "Ensure all coordinates are valid and accessible before mission planning",
            "Set appropriate altitude for your specific location and terrain",
            "Consider local regulations and airspace restrictions",
            "Test mission parameters in simulation mode before execution",
            "Plan for emergency procedures and landing zones",
            "Consider weather conditions and wind patterns",
            "Use geofencing to define safe flight boundaries",
            "Maintain adequate battery reserves for unexpected conditions"
        ])
    
    def get_error_prevention_suggestions(self, mission_type, context):
        """Get suggestions to prevent common errors"""
        suggestions = []
        
        # Check for common error patterns
        error_key = f"validation_error_{mission_type}"
        if error_key in self.behavior_tracker.error_patterns:
            common_errors = self.behavior_tracker.error_patterns[error_key]
            if common_errors > 2:
                suggestions.append({
                    'type': 'error_prevention',
                    'title': 'Common Validation Error',
                    'description': f'This mission type has {common_errors} validation errors. Check your settings carefully.',
                    'priority': 'high'
                })
        
        # Terrain-specific suggestions
        if context.get('terrain') == 'mountainous':
            suggestions.append({
                'type': 'terrain_warning',
                'title': 'Mountainous Terrain',
                'description': 'Consider increasing safety margins and altitude for mountainous terrain.',
                'priority': 'medium'
            })
        
        return suggestions
    
    def record_mission_creation(self, mission_type, settings, location=None):
        """Record mission creation for learning"""
        self.behavior_tracker.record_mission_creation(mission_type, settings, location)
        
        # Update template usage if it matches a template
        for template in self.templates.values():
            if template.mission_type == mission_type:
                # Check if settings match template (with some tolerance)
                if self.settings_match_template(settings, template.settings):
                    template.usage_count += 1
                    template.last_used = datetime.now().isoformat()
                    self.save_templates()
                    break
    
    def settings_match_template(self, settings, template_settings, tolerance=0.2):
        """Check if settings match a template within tolerance"""
        matches = 0
        total_checks = 0
        
        for key, template_value in template_settings.items():
            if key in settings:
                total_checks += 1
                user_value = settings[key]
                
                # Numeric comparison with tolerance
                if isinstance(template_value, (int, float)) and isinstance(user_value, (int, float)):
                    if abs(user_value - template_value) / template_value <= tolerance:
                        matches += 1
                # Exact match for strings
                elif template_value == user_value:
                    matches += 1
        
        return total_checks > 0 and matches / total_checks >= 0.8

class SuggestionWidget(QWidget):
    """Widget for displaying smart suggestions"""
    
    suggestion_selected = pyqtSignal(dict)  # Emits suggestion data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.suggestions_engine = SmartSuggestionsEngine()
        self.current_suggestions = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the suggestion widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header_label = QLabel("Smart Suggestions")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(header_label)
        
        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(300)
        self.suggestions_list.itemClicked.connect(self.on_suggestion_selected)
        layout.addWidget(self.suggestions_list)
        
        # Apply theme
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1a2332;
                color: white;
            }
            QListWidget {
                background-color: #2d3748;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 3px;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #4a5568;
                border-color: #00d4aa;
            }
            QListWidget::item:selected {
                background-color: #00d4aa;
                color: #1a2332;
            }
        """)
        
    def update_suggestions(self, mission_type=None, context=None):
        """Update suggestions based on mission type and context"""
        self.current_suggestions = []
        
        # Get template suggestions
        template_suggestions = self.suggestions_engine.get_template_suggestions(mission_type)
        for template in template_suggestions:
            self.current_suggestions.append({
                'type': 'template',
                'title': template.name,
                'description': template.description,
                'data': template.settings,
                'priority': 'high' if template.usage_count > 5 else 'medium'
            })
        
        # Get location suggestions
        location_suggestions = self.suggestions_engine.get_location_suggestions()
        for suggestion in location_suggestions:
            self.current_suggestions.append({
                'type': 'location',
                'title': f"Use {suggestion['location']}",
                'description': suggestion['description'],
                'data': {'location': suggestion['location']},
                'priority': 'medium'
            })
        
        # Get error prevention suggestions
        if mission_type and context:
            error_suggestions = self.suggestions_engine.get_error_prevention_suggestions(mission_type, context)
            for suggestion in error_suggestions:
                self.current_suggestions.append(suggestion)
        
        self.update_suggestions_display()
        
    def update_suggestions_display(self):
        """Update the suggestions list display"""
        self.suggestions_list.clear()
        
        for suggestion in self.current_suggestions:
            item = QListWidgetItem()
            
            # Create suggestion text
            priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡" if suggestion['priority'] == 'medium' else "🟢"
            title = f"{priority_icon} {suggestion['title']}"
            description = suggestion['description']
            
            item.setText(f"{title}\n{description}")
            item.setData(Qt.UserRole, suggestion)
            
            # Set item styling based on type
            if suggestion['type'] == 'template':
                item.setBackground(QColor("#2d3748"))
            elif suggestion['type'] == 'location':
                item.setBackground(QColor("#1a2332"))
            elif suggestion['type'] == 'error_prevention':
                item.setBackground(QColor("#7c2d12"))
            
            self.suggestions_list.addItem(item)
        
        if not self.current_suggestions:
            no_suggestions_item = QListWidgetItem("No suggestions available")
            no_suggestions_item.setBackground(QColor("#4a5568"))
            self.suggestions_list.addItem(no_suggestions_item)
    
    def on_suggestion_selected(self, item):
        """Handle suggestion selection"""
        suggestion_data = item.data(Qt.UserRole)
        if suggestion_data:
            self.suggestion_selected.emit(suggestion_data)
    
    def record_mission_creation(self, mission_type, settings, location=None):
        """Record mission creation for learning"""
        self.suggestions_engine.record_mission_creation(mission_type, settings, location)

class SmartDefaultsDialog(QDialog):
    """Dialog for applying smart defaults"""
    
    defaults_applied = pyqtSignal(dict)  # Emits applied defaults
    
    def __init__(self, mission_type, current_settings=None, parent=None):
        super().__init__(parent)
        self.mission_type = mission_type
        self.current_settings = current_settings or {}
        self.suggestions_engine = SmartSuggestionsEngine()
        self.setup_ui()
        self.load_suggestions()
        self.apply_theme()
        
    def setup_ui(self):
        """Setup the smart defaults dialog UI"""
        self.setWindowTitle("Smart Defaults & Suggestions")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel(f"Smart Suggestions for {self.mission_type}")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: #00d4aa;")
        layout.addWidget(header_label)
        
        # Smart defaults section
        defaults_group = QGroupBox("Recommended Defaults")
        defaults_layout = QVBoxLayout(defaults_group)
        
        self.defaults_text = QTextEdit()
        self.defaults_text.setMaximumHeight(150)
        self.defaults_text.setReadOnly(True)
        defaults_layout.addWidget(self.defaults_text)
        
        apply_defaults_btn = QPushButton("Apply Smart Defaults")
        apply_defaults_btn.clicked.connect(self.apply_smart_defaults)
        defaults_layout.addWidget(apply_defaults_btn)
        
        layout.addWidget(defaults_group)
        
        # Suggestions section
        suggestions_group = QGroupBox("Smart Suggestions")
        suggestions_layout = QVBoxLayout(suggestions_group)
        
        self.suggestions_widget = SuggestionWidget()
        self.suggestions_widget.suggestion_selected.connect(self.on_suggestion_selected)
        suggestions_layout.addWidget(self.suggestions_widget)
        
        layout.addWidget(suggestions_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_suggestions(self):
        """Load smart suggestions"""
        # Get smart defaults
        smart_defaults = self.suggestions_engine.get_smart_defaults(self.mission_type)
        
        # Display defaults
        defaults_text = "Recommended settings:\n\n"
        for key, value in smart_defaults.items():
            defaults_text += f"• {key.replace('_', ' ').title()}: {value}\n"
        
        self.defaults_text.setPlainText(defaults_text)
        
        # Update suggestions
        self.suggestions_widget.update_suggestions(self.mission_type)
        
    def apply_smart_defaults(self):
        """Apply smart defaults"""
        smart_defaults = self.suggestions_engine.get_smart_defaults(self.mission_type)
        self.defaults_applied.emit(smart_defaults)
        self.accept()
        
    def on_suggestion_selected(self, suggestion_data):
        """Handle suggestion selection"""
        if suggestion_data['type'] == 'template':
            self.defaults_applied.emit(suggestion_data['data'])
            self.accept()
        elif suggestion_data['type'] == 'location':
            # Handle location suggestion
            pass
    
    def apply_theme(self):
        """Apply the dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1a2332;
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
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00d4aa;
            }
            QTextEdit {
                background-color: #2d3748;
                color: white;
                border: 2px solid #4a5568;
                border-radius: 5px;
                padding: 10px;
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
        """)

# Global suggestions engine instance
smart_suggestions_engine = SmartSuggestionsEngine()
