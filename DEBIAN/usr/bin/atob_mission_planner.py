import json
import sys
import time
import requests
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout, QTextEdit, QLineEdit, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import QUrl, Qt
from shapely.geometry import LineString
from shapely.ops import transform
from pyproj import Proj, Transformer


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
                elif response.status_code == 429:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
            time.sleep(0.5)
        return 0


class MissionPlanner(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.terrain_query = TerrainQuery()
        self.plan_file_path = None
        self.kml_coordinates = []  # Store coordinates extracted from KML
        self.initUI()

    def initUI(self):
        self.setWindowTitle("UAV Mission Planner")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QtWidgets.QHBoxLayout(self)

        # Left side: Map view and instructions
        left_layout = QtWidgets.QVBoxLayout()

        # Collapsible Instructions with Toggle Button
        self.instructions_label = QLabel(
            "Instructions:\n"
            "1. Select whether to use a KML file or manually enter start and end points.\n"
            "2. If using a KML file, load it and view the extracted path.\n"
            "3. Adjust settings (altitude, interval, geofence) as required, then generate the plan."
        )
        self.instructions_label.setWordWrap(True)
        self.instructions_label.setVisible(False)

        self.toggle_instructions_btn = QPushButton("Show Instructions", self)
        self.toggle_instructions_btn.setCheckable(True)
        self.toggle_instructions_btn.clicked.connect(self.toggle_instructions)

        left_layout.addWidget(self.toggle_instructions_btn)
        left_layout.addWidget(self.instructions_label)

        # Map View
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        self.map_view.setUrl(QUrl("https://www.google.com/maps"))
        left_layout.addWidget(self.map_view)

        # Choice between manual or KML path
        self.path_choice_label = QLabel("Select Path Input Method:")
        left_layout.addWidget(self.path_choice_label)

        self.path_choice_group = QButtonGroup(self)
        self.manual_path_radio = QRadioButton("Manual Entry (Takeoff and Landing)")
        self.kml_path_radio = QRadioButton("Load KML Path File")
        self.manual_path_radio.setChecked(True)

        self.path_choice_group.addButton(self.manual_path_radio)
        self.path_choice_group.addButton(self.kml_path_radio)

        left_layout.addWidget(self.manual_path_radio)
        left_layout.addWidget(self.kml_path_radio)

        # KML Path File Controls (hidden by default)
        self.load_kml_btn = QPushButton("Load KML Path File")
        self.load_kml_btn.setVisible(False)
        self.load_kml_btn.clicked.connect(self.load_kml_file)
        left_layout.addWidget(self.load_kml_btn)

        self.kml_file_label = QLabel("No KML file loaded.")
        self.kml_file_label.setVisible(False)
        left_layout.addWidget(self.kml_file_label)

        self.kml_coordinates_text = QTextEdit()
        self.kml_coordinates_text.setReadOnly(True)
        self.kml_coordinates_text.setVisible(False)
        left_layout.addWidget(self.kml_coordinates_text)

        # Connect radio buttons to toggle UI elements
        self.manual_path_radio.toggled.connect(self.toggle_path_input)
        self.kml_path_radio.toggled.connect(self.toggle_path_input)

        main_layout.addLayout(left_layout, 2)

        # Right side: Form input fields and buttons
        form_layout = QtWidgets.QVBoxLayout()

        form_layout.addWidget(QLabel("Enter Start Coordinates (lat,lon):"))
        self.start_coords = QLineEdit(self)
        form_layout.addWidget(self.start_coords)

        form_layout.addWidget(QLabel("Enter End Coordinates (lat,lon):"))
        self.end_coords = QLineEdit(self)
        form_layout.addWidget(self.end_coords)

        # Aircraft Type Selection
        form_layout.addWidget(QLabel("Select Aircraft Type:"))
        self.aircraft_type = QComboBox(self)
        self.aircraft_type.addItems(["Multicopter/Helicopter", "Fixed Wing", "Quadplane/VTOL Hybrid"])
        form_layout.addWidget(self.aircraft_type)

        # Altitude Above Terrain
        form_layout.addWidget(QLabel("Altitude Above Terrain:"))
        self.altitude = QLineEdit(self)
        form_layout.addWidget(self.altitude)

        # Altitude Units
        self.altitude_units = QComboBox(self)
        self.altitude_units.addItems(["Feet", "Meters"])
        form_layout.addWidget(self.altitude_units)

        # Waypoint Interval
        form_layout.addWidget(QLabel("Waypoint Interval:"))
        self.interval = QLineEdit(self)
        form_layout.addWidget(self.interval)

        # Waypoint Interval Units
        self.interval_units = QComboBox(self)
        self.interval_units.addItems(["Meters", "Feet"])
        form_layout.addWidget(self.interval_units)

        # Geofence Buffer
        form_layout.addWidget(QLabel("Geofence Buffer:"))
        self.geofence_buffer = QLineEdit(self)
        form_layout.addWidget(self.geofence_buffer)

        # Geofence Units
        self.geofence_units = QComboBox(self)
        self.geofence_units.addItems(["Feet", "Meters"])
        form_layout.addWidget(self.geofence_units)

        # Button to generate .plan file
        self.generate_btn = QPushButton("Generate .plan File", self)
        self.generate_btn.clicked.connect(self.generate_plan)
        form_layout.addWidget(self.generate_btn)

        # Button to open .plan file in QGroundControl (initially disabled)
        self.open_btn = QPushButton("Open in QGroundControl", self)
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_in_qgroundcontrol)
        form_layout.addWidget(self.open_btn)

        # Button to visualize altitude profile (initially disabled)
        self.visualize_btn = QPushButton("Visualize Altitude Profile", self)
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self.visualize_altitude)
        form_layout.addWidget(self.visualize_btn)

        # Progress bar for generating .plan file
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)

        main_layout.addLayout(form_layout, 1)
        self.setLayout(main_layout)

        self.waypoints = []  # Placeholder for storing waypoints for visualization

    def toggle_instructions(self):
        if self.toggle_instructions_btn.isChecked():
            self.instructions_label.setVisible(True)
            self.toggle_instructions_btn.setText("Hide Instructions")
        else:
            self.instructions_label.setVisible(False)
            self.toggle_instructions_btn.setText("Show Instructions")

    def toggle_path_input(self):
        """Toggle visibility of KML tools based on user choice."""
        use_kml = self.kml_path_radio.isChecked()
        self.load_kml_btn.setVisible(use_kml)
        self.kml_file_label.setVisible(use_kml)
        self.kml_coordinates_text.setVisible(use_kml)

    def load_kml_file(self):
        """Loads a KML file and extracts path coordinates."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open KML Path File", "", "KML Files (*.kml)")
        if not file_path:
            return

        self.kml_file_label.setText(f"Loaded KML File: {file_path}")
        self.kml_coordinates = self.extract_kml_coordinates(file_path)

        if self.kml_coordinates:
            self.kml_coordinates_text.setText("\n".join(map(str, self.kml_coordinates)))
        else:
            self.kml_coordinates_text.setText("No valid coordinates found in the KML file.")

    def extract_kml_coordinates(self, file_path):
        """Extracts coordinates from the <LineString> tag in a KML file."""
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            line_elements = root.findall(".//kml:LineString/kml:coordinates", namespace)

            path_coordinates = []
            for element in line_elements:
                raw_coords = element.text.strip()
                for coord in raw_coords.split():
                    lon, lat, alt = map(float, coord.split(","))
                    path_coordinates.append((lat, lon, alt))
            return path_coordinates
        except Exception as e:
            print(f"Error parsing KML file: {e}")
            return []

    def parse_coordinates(self, coord_text):
        try:
            lat, lon = map(float, coord_text.split(','))
            return lat, lon
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in 'lat,lon' format.")
            return None, None

    def convert_units(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def interpolate_kml_path(self, start_coords, end_coords, interval):
        """Interpolates waypoints between two points based on the interval."""
        start_lat, start_lon = start_coords
        end_lat, end_lon = end_coords
        distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)

        interpolated_coords = [start_coords]

        num_intervals = int(distance // interval)
        for j in range(1, num_intervals):
            fraction = j / num_intervals
            interpolated_point = (
                start_lat + fraction * (end_lat - start_lat),
                start_lon + fraction * (end_lon - start_lon)
            )
            interpolated_coords.append(interpolated_point)

        interpolated_coords.append(end_coords)
        return interpolated_coords

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000  # Earth radius in meters
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def generate_plan(self):
        """Generates a flight plan based on the selected input method."""
        if self.kml_path_radio.isChecked():
            if not self.kml_coordinates:
                QMessageBox.warning(self, "No KML Path", "Please load a KML path file first.")
                return

            # User-defined waypoint interval (convert to meters if necessary)
            interval_meters = self.convert_units(float(self.interval.text()), self.interval_units.currentText())

            # Interpolate the KML path based on the interval
            self.waypoints = []
            for i in range(len(self.kml_coordinates) - 1):
                start_coords = (self.kml_coordinates[i][0], self.kml_coordinates[i][1])
                end_coords = (self.kml_coordinates[i + 1][0], self.kml_coordinates[i + 1][1])
                segment_waypoints = self.interpolate_kml_path(start_coords, end_coords, interval_meters)
                self.waypoints.extend(segment_waypoints[:-1])  # Avoid duplicating the last point of each segment

            # Add the final KML point
            self.waypoints.append((self.kml_coordinates[-1][0], self.kml_coordinates[-1][1]))
        else:
            # Handle manual entry for takeoff and landing
            start_lat, start_lon = self.parse_coordinates(self.start_coords.text())
            end_lat, end_lon = self.parse_coordinates(self.end_coords.text())
            if None in (start_lat, start_lon, end_lat, end_lon):
                return

            interval_meters = self.convert_units(float(self.interval.text()), self.interval_units.currentText())

            # Interpolate waypoints between start and end locations
            self.waypoints = self.interpolate_kml_path((start_lat, start_lon), (end_lat, end_lon), interval_meters)

        # Progress bar setup
        total_steps = len(self.waypoints) + 2  # Add steps for takeoff and landing
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
        mission_items = []

        # Add takeoff sequence
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 22,  # TAKEOFF command for Multicopter
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, self.waypoints[0][0], self.waypoints[0][1], altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })
        self.progress_bar.setValue(1)
        QtWidgets.QApplication.processEvents()

        # Add waypoints
        for i, (lat, lon) in enumerate(self.waypoints):
            terrain_elevation = self.terrain_query.get_elevation(lat, lon)  # Get terrain height
            waypoint_amsl_altitude = terrain_elevation + altitude_meters  # ✅ Ensures correct terrain-following altitude

            mission_items.append({
                "AMSLAltAboveTerrain": waypoint_amsl_altitude,  # ✅ Now correctly set
                "Altitude": altitude_meters,  # ✅ User-defined AGL altitude (constant)
                "AltitudeMode": 3,  # ✅ Mode 3 = Terrain Following
                "autoContinue": True,
                "command": 16,  # Waypoint command
                "doJumpId": i + 2,
                "frame": 0,  # ✅ Absolute altitude (Terrain Following Mode)
                "params": [0, 0, 0, None, lat, lon, waypoint_amsl_altitude],  # ✅ Uses terrain-following altitude
                "type": "SimpleItem"
            })

            self.progress_bar.setValue(self.progress_bar.value() + 1)
            QtWidgets.QApplication.processEvents()

        # Add landing sequence
        final_lat, final_lon = self.waypoints[-1]  # Unpack lat and lon
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 21,  # LAND command for Multicopter
                "doJumpId": len(self.waypoints) + 2,
                "frame": 3,
                "params": [0, 0, 0, None, final_lat, final_lon, 0],
                "type": "SimpleItem",
                "autoContinue": True
            })

        # Calculate lateral geofence buffer using Shapely
        waypoints_line = LineString([(lon, lat) for lat, lon in self.waypoints])  # Convert to (lon, lat) format
        geofence_buffer_meters = self.convert_units(float(self.geofence_buffer.text()), self.geofence_units.currentText())

        # Define projections
        proj_wgs84 = Proj(proj='latlong', datum='WGS84')
        proj_aeqd = Proj(proj='aeqd', datum='WGS84', lat_0=self.waypoints[0][0], lon_0=self.waypoints[0][1])
        transformer_to_aeqd = Transformer.from_proj(proj_wgs84, proj_aeqd)
        transformer_to_wgs84 = Transformer.from_proj(proj_aeqd, proj_wgs84)

        # Apply buffer
        projected_line = transform(transformer_to_aeqd.transform, waypoints_line)
        buffered_polygon = projected_line.buffer(geofence_buffer_meters)
        buffered_polygon = transform(transformer_to_wgs84.transform, buffered_polygon)  # Convert back to lat/lon

        # Extract polygon coordinates for the geofence
        geofence_polygon = [[lat, lon] for lon, lat in list(buffered_polygon.exterior.coords)]

        geofence_data = {
            "circles": [],
            "polygons": [{
                "inclusion": True,
                "polygon": geofence_polygon,
                "version": 1
            }],
            "version": 2  # Geofence version
        }

        # Ensure home elevation is defined before using it
        home_elevation = self.terrain_query.get_elevation(self.waypoints[0][0], self.waypoints[0][1])  # ✅ Fetch terrain elevation
                
        # Save flight plan
        plan_data = {
            "fileType": "Plan",
            "version": 1,  # Root-level version
            "geoFence": geofence_data,
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": 15,
                "firmwareType": 12,
                "globalPlanAltitudeMode": 3,
                "hoverSpeed": 5,
                "items": mission_items,
                "plannedHomePosition": [self.waypoints[0][0], self.waypoints[0][1], home_elevation],  # ✅ Use real terrain altitude
                "vehicleType": 2,
                "version": 2  # Mission version
            },
            "rallyPoints": {
                "points": [],
                "version": 2  # Rally points version
            }
        }

        filename, _ = QFileDialog.getSaveFileName(self, "Save Plan File", "", ".plan")
        if filename:
            with open(filename, 'w') as file:
                json.dump(plan_data, file, indent=2)
            self.plan_file_path = filename
            self.open_btn.setEnabled(True)
            self.visualize_btn.setEnabled(True)

        # Hide progress bar after completion
        self.progress_bar.setValue(total_steps)
        self.progress_bar.setVisible(False)

    def visualize_altitude(self):
        """Visualizes the altitude profile for the waypoints."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        altitudes_agl = []
        altitudes_amsl = []

        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())

        for lat, lon in self.waypoints:
            elevation = self.terrain_query.get_elevation(lat, lon)
            waypoint_altitude = elevation + altitude_meters  # ✅ Correctly sets altitude AGL
            altitudes_agl.append(altitude_meters)  # ✅ AGL remains the same
            altitudes_amsl.append(waypoint_altitude)  # ✅ Correct AMSL altitude for visualization

        plt.figure(figsize=(10, 5))
        plt.plot(range(len(self.waypoints)), altitudes_amsl, label='AMSL Altitude (meters)')
        plt.plot(range(len(self.waypoints)), altitudes_agl, label='AGL Altitude (meters)', linestyle='--')
        plt.xlabel('Waypoint Index')
        plt.ylabel('Altitude (meters)')
        plt.title('Altitude Profile')
        plt.legend()
        plt.grid(True)
        plt.show()

    def open_in_qgroundcontrol(self):
        """Opens the generated .plan file in QGroundControl."""
        if self.plan_file_path:
            subprocess.run(["qgroundcontrol", self.plan_file_path], check=True)


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = MissionPlanner()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
