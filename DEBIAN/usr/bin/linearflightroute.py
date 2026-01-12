import sys
import json
import time
import requests
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from math import tan, radians, cos  # Import cos and radians
from PyQt5.QtCore import QUrl, QSettings
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QVBoxLayout, QPushButton, QLabel, QWidget, QTextEdit,
    QDoubleSpinBox, QLineEdit, QHBoxLayout, QSpinBox, QProgressBar, QComboBox, QMessageBox
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
                elif response.status_code == 429:  # Too many requests
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0


class LinearFlightRoute(QMainWindow):
    def __init__(self):
        super().__init__()
        self.terrain_query = TerrainQuery()
        self.settings = QSettings("FlightPlanner", "LinearFlightRoute")
        self.init_ui()
        self.path_coordinates = []
        self.takeoff_point = None
        self.landing_point = None

    def init_ui(self):
        self.setWindowTitle("Flight Planner with Drone Type Selection")
        self.resize(1200, 700)

        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.layout = QHBoxLayout(self.central_widget)

        # Left-side control panel
        self.control_panel = QVBoxLayout()
        self.layout.addLayout(self.control_panel)

        self.load_button = QPushButton("Load KML Path File")
        self.control_panel.addWidget(self.load_button)
        self.load_button.clicked.connect(self.load_kml_file)

        self.altitude_label = QLabel("Set Altitude Above Terrain (Feet):")
        self.control_panel.addWidget(self.altitude_label)
        self.altitude_input = QDoubleSpinBox()
        self.altitude_input.setRange(1, 16404)
        self.altitude_input.setValue(self.settings.value("altitude", 164, type=float))
        self.control_panel.addWidget(self.altitude_input)

        # Custom Takeoff Point
        self.takeoff_label = QLabel("Takeoff Point (latitude, longitude):")
        self.control_panel.addWidget(self.takeoff_label)
        self.takeoff_input = QLineEdit()
        self.takeoff_input.setPlaceholderText("Enter as: latitude, longitude")
        self.takeoff_input.setText(self.settings.value("takeoff_point", ""))
        self.control_panel.addWidget(self.takeoff_input)

        # Drone Type Selection
        self.drone_type_label = QLabel("Select Drone Type:")
        self.control_panel.addWidget(self.drone_type_label)
        self.drone_type_dropdown = QComboBox()
        self.drone_type_dropdown.addItems(["Multicopter/Helicopter", "Fixed-Wing", "Quadplane/VTOL Hybrid"])
        self.drone_type_dropdown.setCurrentText(self.settings.value("drone_type", "Multicopter/Helicopter"))
        self.control_panel.addWidget(self.drone_type_dropdown)

        # Waypoint Interval
        self.interval_label = QLabel("Waypoint Interval (meters):")
        self.control_panel.addWidget(self.interval_label)
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 1000)
        self.interval_input.setValue(self.settings.value("interval", 50, type=int))
        self.control_panel.addWidget(self.interval_input)

        # Landing Options
        self.landing_label = QLabel("Landing Point (latitude, longitude):")
        self.control_panel.addWidget(self.landing_label)
        self.landing_input = QLineEdit()
        self.landing_input.setPlaceholderText("Enter as: latitude, longitude")
        self.landing_input.setText(self.settings.value("landing_point", ""))
        self.control_panel.addWidget(self.landing_input)

        self.generate_flight_button = QPushButton("Generate Flight Plan")
        self.control_panel.addWidget(self.generate_flight_button)
        self.generate_flight_button.clicked.connect(self.generate_flight_plan)
        self.generate_flight_button.setEnabled(False)

        # Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        self.control_panel.addWidget(self.progress_bar)

        # Label for file info
        self.file_label = QLabel("No file loaded.")
        self.control_panel.addWidget(self.file_label)

        # Text box for displaying coordinates and generated flight path
        self.coordinates_text = QTextEdit()
        self.coordinates_text.setReadOnly(True)
        self.control_panel.addWidget(self.coordinates_text)

        # Right-side map view (Google Maps)
        self.map_view = QWebEngineView()
        self.layout.addWidget(self.map_view)
        self.load_google_maps()

    def closeEvent(self, event):
        """Save user preferences when the application is closed."""
        self.settings.setValue("altitude", self.altitude_input.value())
        self.settings.setValue("takeoff_point", self.takeoff_input.text())
        self.settings.setValue("drone_type", self.drone_type_dropdown.currentText())
        self.settings.setValue("interval", self.interval_input.value())
        self.settings.setValue("landing_point", self.landing_input.text())
        event.accept()

    def load_google_maps(self):
        self.map_view.setUrl(QUrl("https://www.google.com/maps"))

    def load_kml_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open KML Path File", "", "KML Files (*.kml)"
        )
        if not file_path:
            return

        self.file_label.setText(f"Loaded File: {file_path}")

        self.path_coordinates = self.extract_path_coordinates_from_kml(file_path)
        if self.path_coordinates:
            # Display coordinates in (lat, lon) format in the GUI
            self.coordinates_text.setText("\n".join([f"({lat}, {lon})" for lon, lat, _ in self.path_coordinates]))
            self.generate_flight_button.setEnabled(True)
            self.plot_path_on_map()
        else:
            self.coordinates_text.setText("No valid path found or an error occurred.")
            self.generate_flight_button.setEnabled(False)

    def extract_path_coordinates_from_kml(self, file_path):
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            line_elements = root.findall(".//kml:LineString/kml:coordinates", namespace)

            path_coordinates = []
            for element in line_elements:
                raw_coords = element.text.strip()
                for coord in raw_coords.split():
                    lon, lat, alt = map(float, coord.split(","))
                    path_coordinates.append((lon, lat, alt))
            return path_coordinates
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse KML file: {e}")
            return []

    def plot_path_on_map(self):
        """Plots the flight path on the Google Maps view."""
        if not self.path_coordinates:
            return

        # Generate a JavaScript command to plot the path
        path_coords = [f"{{lat: {lat}, lng: {lon}}}" for lon, lat, _ in self.path_coordinates]
        js_command = f"""
            var flightPath = new google.maps.Polyline({{
                path: [{", ".join(path_coords)}],
                geodesic: true,
                strokeColor: '#FF0000',
                strokeOpacity: 1.0,
                strokeWeight: 2
            }});
            flightPath.setMap(map);
        """
        self.map_view.page().runJavaScript(js_command)

    def calculate_landing_pattern_offset(self, altitude_meters):
        """Calculates the distance offset for the landing pattern based on altitude and glide slope."""
        glide_slope_angle = 7.4  # Degrees
        return altitude_meters / tan(radians(glide_slope_angle))

    def generate_takeoff_waypoint(self, altitude, terrain_elevation):
        """Generates a takeoff waypoint based on the selected drone type."""
        drone_type = self.drone_type_dropdown.currentText()
        if drone_type == "Quadplane/VTOL Hybrid":
            return {
                "command": 84,  # VTOL_TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }
        elif drone_type == "Fixed-Wing":
            return {
                "command": 22,  # FIXED_WING_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }
        else:
            return {
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 0,
                "params": [0, 0, 0, None, self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude,
                "AltitudeMode": 3
            }

    def generate_landing_waypoint(self, terrain_elevation):
        """Generates a landing waypoint based on the selected drone type."""
        drone_type = self.drone_type_dropdown.currentText()
        altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters

        if drone_type == "Quadplane/VTOL Hybrid":
            return {
                "command": 85,  # VTOL_LAND
                "doJumpId": 999,
                "frame": 0,
                "params": [0, 0, 0, 0, self.landing_point[0], self.landing_point[1], terrain_elevation],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": 0,
                "AltitudeMode": 3
            }
        elif drone_type == "Fixed-Wing":
            # Calculate the distance offset for the landing pattern
            distance_offset = self.calculate_landing_pattern_offset(altitude_meters)

            # Calculate the approach coordinates based on the distance offset
            approach_lat = self.landing_point[0] + (distance_offset / 111320.0)  # 1 degree ≈ 111,320 meters
            approach_lon = self.landing_point[1] + (distance_offset / (111320.0 * cos(radians(self.landing_point[0]))))

            return {
                "altitudesAreRelative": True,
                "complexItemType": "fwLandingPattern",
                "landCoordinate": [self.landing_point[0], self.landing_point[1], 0],
                "landingApproachCoordinate": [approach_lat, approach_lon, altitude_meters],
                "loiterClockwise": True,
                "loiterRadius": distance_offset,  # Use dynamic distance offset
                "stopTakingPhotos": True,
                "stopVideoPhotos": True,
                "type": "ComplexItem",
                "useLoiterToAlt": True,
                "valueSetIsDistance": False,
                "version": 2
            }
        else:
            return {
                "command": 21,  # LAND
                "doJumpId": 999,
                "frame": 0,
                "params": [0, 0, 0, 0, self.landing_point[0], self.landing_point[1], terrain_elevation],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": 0,
                "AltitudeMode": 3
            }

    def generate_flight_plan(self):
        """Generates the flight plan with waypoints."""
        if not self.path_coordinates:
            self.coordinates_text.setText("No valid path coordinates available.")
            return

        altitude_meters = self.altitude_input.value() * 0.3048  # Convert feet to meters
        interval = self.interval_input.value()

        # Validate and set the takeoff point
        try:
            takeoff_lat, takeoff_lon = map(float, self.takeoff_input.text().split(","))
            self.takeoff_point = (takeoff_lat, takeoff_lon)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid takeoff point coordinates. Please enter as: latitude, longitude.")
            return

        # Validate and set the landing point
        try:
            landing_lat, landing_lon = map(float, self.landing_input.text().split(","))
            self.landing_point = (landing_lat, landing_lon)
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid landing point coordinates. Please enter as: latitude, longitude.")
            return

        interpolated_path = self.interpolate_waypoints(self.path_coordinates, interval)

        # Set up progress bar
        total_steps = len(interpolated_path) + 2  # Path points + Takeoff + Landing
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        waypoints = []

        # Takeoff waypoint(s)
        terrain_elevation = self.terrain_query.get_elevation(self.takeoff_point[0], self.takeoff_point[1])
        takeoff_waypoint = self.generate_takeoff_waypoint(altitude_meters, terrain_elevation)
        waypoints.append(takeoff_waypoint)

        self.progress_bar.setValue(1)
        QApplication.processEvents()

        # Intermediate waypoints
        for i, (lon, lat, _) in enumerate(interpolated_path):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)
            waypoints.append({
                "command": 16,
                "doJumpId": i + 2,
                "frame": 0,
                "params": [0, 0, 0, 0, lat, lon, terrain_elevation + altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True,
                "AMSLAltAboveTerrain": terrain_elevation,
                "Altitude": altitude_meters,
                "AltitudeMode": 3
            })
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            QApplication.processEvents()

        # Landing waypoint
        landing_elevation = self.terrain_query.get_elevation(self.landing_point[0], self.landing_point[1])
        landing_waypoint = self.generate_landing_waypoint(landing_elevation)
        waypoints.append(landing_waypoint)
        self.progress_bar.setValue(total_steps)
        QApplication.processEvents()

        flight_plan = {
            "fileType": "Plan",
            "geoFence": {"circles": [], "polygons": [], "version": 2},
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": 15,
                "hoverSpeed": 5,
                "firmwareType": 12,
                "globalPlanAltitudeMode": 3,
                "items": waypoints,
                "plannedHomePosition": [self.takeoff_point[0], self.takeoff_point[1], terrain_elevation + altitude_meters],
                "vehicleType": 1 if self.drone_type_dropdown.currentText() == "Fixed-Wing" else 2,
                "version": 2
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

        self.save_flight_plan(flight_plan)
        self.progress_bar.setVisible(False)

    def save_flight_plan(self, flight_plan):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Flight Plan", "", "Plan Files (*.plan)")
        if save_path:
            try:
                with open(save_path, "w") as file:
                    json.dump(flight_plan, file, indent=4)
                self.coordinates_text.setText(f"Flight plan generated and saved to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save flight plan: {e}")
        else:
            self.coordinates_text.setText("Flight plan generation canceled.")

    def interpolate_waypoints(self, path_coords, interval):
        interpolated_coords = []

        for i in range(len(path_coords) - 1):
            start = (path_coords[i][1], path_coords[i][0])
            end = (path_coords[i + 1][1], path_coords[i + 1][0])
            distance = geodesic(start, end).meters

            interpolated_coords.append(path_coords[i])

            num_intervals = int(distance // interval)
            for j in range(1, num_intervals):
                fraction = j / num_intervals
                interpolated_point = (
                    start[0] + fraction * (end[0] - start[0]),
                    start[1] + fraction * (end[1] - start[1])
                )
                interpolated_coords.append((interpolated_point[1], interpolated_point[0], path_coords[i][2]))

        interpolated_coords.append(path_coords[-1])
        return interpolated_coords


if __name__ == "__main__":
    app = QApplication(sys.argv)
    planner = LinearFlightRoute()
    planner.show()
    sys.exit(app.exec())