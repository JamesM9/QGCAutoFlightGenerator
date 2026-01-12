import sys
import json
import requests
import time
import math
import random
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon, Point
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit,
    QSpinBox, QDoubleSpinBox, QLineEdit, QHBoxLayout, QProgressBar, QComboBox, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView


class TerrainQuery:
    """Class to fetch terrain elevation using OpenTopography API."""
    def __init__(self):
        self.api_url = "https://api.opentopodata.org/v1/srtm90m"

    def get_elevation(self, lat, lon):
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(self.api_url, params={'locations': f"{lat},{lon}"}, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if "results" in data and data["results"]:
                        elevation = data["results"][0]["elevation"]
                        return elevation if elevation is not None else 0
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0


class SecurityRoute(QMainWindow):
    def __init__(self):
        super().__init__()
        self.terrain_query = TerrainQuery()
        self.init_ui()
        self.guiding_coordinates = []
        self.polygon = None
        self.takeoff_point = None

    def init_ui(self):
        self.setWindowTitle("QGroundControl Flight Planner with Geofence")
        self.resize(1200, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Control panel
        self.control_panel = QVBoxLayout()
        self.layout.addLayout(self.control_panel)

        # Vehicle type selection
        self.vehicle_type_label = QLabel("Select Vehicle Type:")
        self.control_panel.addWidget(self.vehicle_type_label)
        self.vehicle_type_combo = QComboBox()
        self.vehicle_type_combo.addItems(["Multicopter", "Fixed-Wing", "Quadplane/VTOL"])
        self.vehicle_type_combo.setCurrentText("Multicopter")  # Default to Multicopter
        self.control_panel.addWidget(self.vehicle_type_combo)

        # Route type selection
        self.route_type_label = QLabel("Select Flight Route Type:")
        self.control_panel.addWidget(self.route_type_label)
        self.route_type_combo = QComboBox()
        self.route_type_combo.addItems(["Random Route", "Perimeter Route"])
        self.route_type_combo.setCurrentText("Random Route")  # Default to "Random Route"
        self.control_panel.addWidget(self.route_type_combo)
        self.route_type_combo.currentTextChanged.connect(self.update_waypoint_input_state)

        # Load KML file button
        self.load_button = QPushButton("Load KML File")
        self.control_panel.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_kml_file)

        # Altitude input
        self.altitude_label = QLabel("Set Altitude Above Terrain (Feet):")
        self.control_panel.addWidget(self.altitude_label)
        self.altitude_input = QDoubleSpinBox()
        self.altitude_input.setRange(1, 16404)  # Altitude input in feet
        self.altitude_input.setValue(100)  # Default altitude
        self.control_panel.addWidget(self.altitude_input)

        # Waypoints input
        self.waypoints_label = QLabel("Number of Waypoints:")
        self.control_panel.addWidget(self.waypoints_label)
        self.waypoints_input = QSpinBox()
        self.waypoints_input.setRange(1, 100)  # Waypoint count input
        self.waypoints_input.setValue(10)  # Default value
        self.control_panel.addWidget(self.waypoints_input)

        # Takeoff coordinates input
        self.takeoff_label = QLabel("Takeoff and Landing Coordinates (lat, lon):")
        self.control_panel.addWidget(self.takeoff_label)
        self.takeoff_input = QLineEdit()
        self.takeoff_input.setPlaceholderText("e.g., 37.7749, -122.4194")  # Latitude, Longitude
        self.control_panel.addWidget(self.takeoff_input)

        # Generate flight plan button
        self.generate_flight_button = QPushButton("Generate Flight Plan")
        self.control_panel.addWidget(self.generate_flight_button)
        self.generate_flight_button.clicked.connect(self.generate_flight_plan)
        self.generate_flight_button.setEnabled(False)

        # Help button
        self.help_button = QPushButton("Help")
        self.control_panel.addWidget(self.help_button)
        self.help_button.clicked.connect(self.show_help)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.control_panel.addWidget(self.progress_bar)

        # File label and coordinates text
        self.file_label = QLabel("No file loaded.")
        self.control_panel.addWidget(self.file_label)
        self.coordinates_text = QTextEdit()
        self.coordinates_text.setReadOnly(True)
        self.control_panel.addWidget(self.coordinates_text)

        # Map view
        self.map_view = QWebEngineView()
        self.layout.addWidget(self.map_view)
        self.load_google_maps()

    def load_google_maps(self):
        """Load Google Maps in the QWebEngineView."""
        self.map_view.setUrl(QUrl("https://www.google.com/maps"))

    def update_waypoint_input_state(self):
        """Enable or disable waypoint input based on route type."""
        selected_route = self.route_type_combo.currentText()
        if selected_route == "Random Route":
            self.waypoints_input.setEnabled(True)  # Enable for Random route
        else:
            self.waypoints_input.setEnabled(False)  # Disable for Perimeter route

    def show_help(self):
        """Display instructions for flight pattern tools."""
        help_text = (
            "<b>Flight Pattern Tools:</b><br><br>"
            "<b>Random Route:</b><br>"
            "Generates a random set of waypoints within the loaded polygon.<br><br>"
            "<b>Perimeter Route:</b><br>"
            "Generates waypoints along the boundary of the polygon for a perimeter scan.<br><br>"
            "Load a KML file to define the geofence and set the desired altitude. "
            "Click 'Generate Flight Plan' to create your route."
        )
        QMessageBox.information(self, "Help - Flight Pattern Tools", help_text)

    def load_kml_file(self):
        """Load a KML file and extract coordinates."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open KML File", "", "KML Files (*.kml)")
        if not file_path:
            return

        self.file_label.setText(f"Loaded File: {file_path}")
        self.guiding_coordinates = self.extract_coordinates_from_kml(file_path)
        if self.guiding_coordinates:
            # Swap latitude and longitude for polygon creation
            self.polygon = Polygon([(lat, lon) for lon, lat, _ in self.guiding_coordinates])
            # Display coordinates as latitude, longitude
            self.coordinates_text.setText("\n".join([f"{lat}, {lon}" for lon, lat, _ in self.guiding_coordinates]))
            self.generate_flight_button.setEnabled(True)
        else:
            self.coordinates_text.setText("No coordinates found or an error occurred.")
            self.generate_flight_button.setEnabled(False)

    def extract_coordinates_from_kml(self, file_path):
        """Extract coordinates from a KML file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            coordinates_elements = root.findall(".//kml:coordinates", namespace)
            coordinates_list = []

            for element in coordinates_elements:
                raw_coords = element.text.strip()
                for coord in raw_coords.split():
                    lon, lat, alt = map(float, coord.split(","))
                    coordinates_list.append((lon, lat, alt))
            return coordinates_list
        except Exception as e:
            print(f"Error while extracting coordinates: {e}")
            return []

    def create_waypoint(self, lat, lon, altitude_above_terrain_feet, command, do_jump_id):
        """Create a waypoint with altitude above terrain, converted to meters for the .plan file."""
        terrain_elevation_meters = self.terrain_query.get_elevation(lat, lon)
        altitude_above_terrain_meters = altitude_above_terrain_feet * 0.3048  # Convert feet to meters
        altitude_meters = terrain_elevation_meters + altitude_above_terrain_meters

        return {
            "AMSLAltAboveTerrain": altitude_meters,
            "Altitude": altitude_above_terrain_meters,
            "AltitudeMode": 1,  # Relative to terrain
            "autoContinue": True,
            "command": command,
            "doJumpId": do_jump_id,
            "frame": 3,
            "params": [0, 0, 0, 0, lat, lon, altitude_meters],
            "type": "SimpleItem"
        }

    def generate_flight_plan(self):
        """Generate the flight plan based on the selected vehicle type and route type."""
        route_type = self.route_type_combo.currentText()
        vehicle_type = self.vehicle_type_combo.currentText()
        try:
            # Parse takeoff coordinates as latitude, longitude
            takeoff_lat, takeoff_lon = map(float, self.takeoff_input.text().split(","))
            self.takeoff_point = (takeoff_lat, takeoff_lon)
        except ValueError:
            self.coordinates_text.setText("Invalid takeoff coordinates. Use 'lat, lon'.")
            return

        altitude_above_terrain_feet = self.altitude_input.value()
        num_waypoints = self.waypoints_input.value()  # Get total number of waypoints
        waypoints = []
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # Add takeoff waypoint based on vehicle type
        if vehicle_type == "Multicopter":
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 22, 1
            ))
        elif vehicle_type == "Fixed-Wing":
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 22, 1
            ))
            # Add a waypoint for the launch sequence
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 16, 2
            ))
        elif vehicle_type == "Quadplane/VTOL":
            # Use VTOL takeoff command (84) for Quadplane/VTOL
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 84, 1
            ))
            # Add a waypoint for the transition to forward flight
            waypoints.append(self.create_waypoint(
                self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 16, 2
            ))

        if route_type == "Random Route":
            self.generate_random_waypoints(waypoints, altitude_above_terrain_feet, num_waypoints)
            # Add a return waypoint to the takeoff location
            if vehicle_type == "Quadplane/VTOL":
                # Use VTOL Land command (85) for Quadplane/VTOL
                waypoints.append(self.create_waypoint(
                    self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 85, len(waypoints) + 1
                ))
            else:
                # Use standard Land command (21) for other vehicle types
                waypoints.append(self.create_waypoint(
                    self.takeoff_point[0], self.takeoff_point[1], altitude_above_terrain_feet, 21, len(waypoints) + 1
                ))
        elif route_type == "Perimeter Route":
            self.generate_perimeter_waypoints(waypoints, altitude_above_terrain_feet)

        # Ensure progress bar reaches 100% after waypoint generation
        self.progress_bar.setValue(100)

        # Save the flight plan
        planned_home_position = [
            self.takeoff_point[0],
            self.takeoff_point[1],
            altitude_above_terrain_feet * 0.3048  # Convert planned home altitude to meters
        ]
        self.save_flight_plan(waypoints, planned_home_position)
        self.progress_bar.setVisible(False)

    def generate_perimeter_waypoints(self, waypoints, altitude):
        """Generate waypoints along the perimeter of the polygon, offset inside the geofence."""
        if not self.polygon:
            self.coordinates_text.setText("No geofence polygon loaded.")
            return

        # Offset the polygon inward by a fixed distance (e.g., 0.0001 degrees)
        offset_distance = -0.0001  # Negative value for inward offset
        offset_polygon = self.polygon.buffer(offset_distance)

        if isinstance(offset_polygon, Polygon):
            perimeter_coords = list(offset_polygon.exterior.coords)
            for i, (lat, lon) in enumerate(perimeter_coords):
                waypoints.append(self.create_waypoint(lat, lon, altitude, 16, i + 2))
                self.progress_bar.setValue(min(100, ((i + 1) / len(perimeter_coords)) * 100))
                QApplication.processEvents()

    def generate_random_waypoints(self, waypoints, altitude, num_waypoints):
        """Generate a specified number of random waypoints within the polygon."""
        if not self.polygon:
            self.coordinates_text.setText("No geofence polygon loaded.")
            return

        for i in range(num_waypoints):
            lat, lon = self.generate_random_point_in_polygon()
            waypoints.append(self.create_waypoint(lat, lon, altitude, 16, i + 2))
            self.progress_bar.setValue(min(100, (i + 1) * 100 // num_waypoints))  # Update progress bar
            QApplication.processEvents()  # Keep UI responsive

        self.coordinates_text.setText(f"Generated {num_waypoints} random waypoints.")

    def generate_random_point_in_polygon(self):
        """Generate a random point within the polygon."""
        minx, miny, maxx, maxy = self.polygon.bounds
        while True:
            random_lat = random.uniform(minx, maxx)
            random_lon = random.uniform(miny, maxy)
            if self.polygon.contains(Point(random_lat, random_lon)):
                return random_lat, random_lon

    def save_flight_plan(self, waypoints, planned_home_position):
        """Save the flight plan to a .plan file."""
        vehicle_type = self.vehicle_type_combo.currentText()
        if vehicle_type == "Multicopter":
            cruise_speed = 15
            hover_speed = 5
            vehicle_type_code = 2
        elif vehicle_type == "Fixed-Wing":
            cruise_speed = 25
            hover_speed = 0
            vehicle_type_code = 1
        elif vehicle_type == "Quadplane/VTOL":
            cruise_speed = 20
            hover_speed = 5
            vehicle_type_code = 3

        geo_fence_polygon = [{"polygon": [[lat, lon] for lon, lat, _ in self.guiding_coordinates], 
                              "inclusion": True, "version": 1}]
        flight_plan = {
            "fileType": "Plan",
            "version": 1,
            "groundStation": "QGroundControl",
            "mission": {
                "items": waypoints,
                "plannedHomePosition": planned_home_position,
                "cruiseSpeed": cruise_speed,
                "hoverSpeed": hover_speed,
                "firmwareType": 12,
                "vehicleType": vehicle_type_code,
                "globalPlanAltitudeMode": 3,
                "version": 2
            },
            "geoFence": {
                "circles": [],
                "polygons": geo_fence_polygon,
                "version": 2
            },
            "rallyPoints": {
                "points": [],
                "version": 2
            }
        }

        # Save as .plan file
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Flight Plan", "", "Plan Files (*.plan)")
        if save_path:
            if not save_path.endswith(".plan"):
                save_path += ".plan"  # Ensure the file has a .plan extension
            with open(save_path, "w") as file:
                json.dump(flight_plan, file, indent=4)
            self.coordinates_text.setText(f"Flight plan with geofence saved to:\n{save_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    planner = SecurityRoute()
    planner.show()
    sys.exit(app.exec())