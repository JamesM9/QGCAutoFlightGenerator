import json
import sys
import time
import requests
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import (
    QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout
)
from PyQt5.QtCore import QUrl, Qt
from shapely.geometry import Point, MultiPoint
from geopy.distance import distance as geopy_distance


class TerrainQuery:
    """Class to fetch terrain elevation using OpenTopography API with rate limiting and caching."""
    def __init__(self):
        self.api_url = "https://api.opentopodata.org/v1/srtm90m"
        self.cache = {}  # Cache to store elevation data for coordinates
        self.rate_limit_delay = 1  # Initial delay in seconds for rate limiting
        self.max_retries = 5  # Maximum number of retries for failed requests

    def get_elevation(self, lat, lon):
        # Check if elevation is already cached
        cache_key = (lat, lon)
        if cache_key in self.cache:
            return self.cache[cache_key]

        retries = 0
        while retries < self.max_retries:
            try:
                response = requests.get(self.api_url, params={'locations': f"{lat},{lon}"}, timeout=5)
                response.raise_for_status()  # Raises an HTTPError for bad responses
                data = response.json()
                if "results" in data and data["results"]:
                    elevation = data["results"][0]["elevation"]
                    if elevation is not None:
                        self.cache[cache_key] = elevation  # Cache the elevation
                        return elevation
            except requests.exceptions.RequestException as e:
                print(f"Error fetching elevation data: {e}")
                if response.status_code == 429:  # Rate limit exceeded
                    retries += 1
                    if retries >= self.max_retries:
                        QMessageBox.warning(None, "API Error", "Failed to fetch elevation data after several attempts.")
                        return 0
                    # Exponential backoff for rate limiting
                    time.sleep(self.rate_limit_delay * (2 ** retries))
                else:
                    QMessageBox.warning(None, "API Error", f"Failed to fetch elevation data: {e}")
                    return 0
        return 0


class DeliveryRoute(QtWidgets.QWidget):
    """
    DeliveryRoute: UI and logic for the delivery route planning tool.
    """
    def __init__(self):
        super().__init__()
        self.terrain_query = TerrainQuery()
        self.plan_file_path = None
        self.waypoints = []  # Placeholder for storing waypoints for visualization
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Delivery Route Planner")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QtWidgets.QHBoxLayout(self)

        # Left side: Map view and instructions
        left_layout = QtWidgets.QVBoxLayout()

        # Collapsible Instructions with Toggle Button
        self.instructions_label = QLabel(
            "Instructions:\n"
            "1. Use the map to select your start and end locations.\n"
            "2. Enter the decimal coordinates for the start and end points below.\n"
            "3. Adjust settings (altitude, interval, geofence) as required.\n"
            "4. Select whether the drone should use a payload mechanism or land and takeoff when commanded to return:\n"
            "   - If you select 'Land and Takeoff When Commanded to Return', ensure the firmware supports the ability for the aircraft\n"
            "     to re-arm and retain the current waypoint after landing (special use firmware only).\n"
            "5. Click 'Generate .plan File' to create the mission plan.\n"
            "6. Use QGroundControl to execute or simulate the mission."
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

        main_layout.addLayout(left_layout, 2)

        # Right side: Form input fields and buttons
        form_layout = QtWidgets.QVBoxLayout()

        form_layout.addWidget(QLabel("Enter Start Coordinates (lat,lon):"))
        self.start_coords = QtWidgets.QLineEdit(self)
        form_layout.addWidget(self.start_coords)

        form_layout.addWidget(QLabel("Enter End Coordinates (lat,lon):"))
        self.end_coords = QtWidgets.QLineEdit(self)
        form_layout.addWidget(self.end_coords)

        # Aircraft Type Selection
        form_layout.addWidget(QLabel("Select Aircraft Type:"))
        self.aircraft_type = QComboBox(self)
        self.aircraft_type.addItems(["Multicopter/Helicopter", "Fixed Wing", "Quadplane/VTOL Hybrid"])
        form_layout.addWidget(self.aircraft_type)

        # Altitude Above Terrain
        form_layout.addWidget(QLabel("Altitude Above Terrain:"))
        self.altitude = QtWidgets.QLineEdit(self)
        form_layout.addWidget(self.altitude)

        # Altitude Units
        self.altitude_units = QComboBox(self)
        self.altitude_units.addItems(["Feet", "Meters"])
        form_layout.addWidget(self.altitude_units)

        # Waypoint Interval
        form_layout.addWidget(QLabel("Waypoint Interval:"))
        self.interval = QtWidgets.QLineEdit(self)
        form_layout.addWidget(self.interval)

        # Waypoint Interval Units
        self.interval_units = QComboBox(self)
        self.interval_units.addItems(["Meters", "Feet"])
        form_layout.addWidget(self.interval_units)

        # Geofence Buffer
        form_layout.addWidget(QLabel("Geofence Buffer:"))
        self.geofence_buffer = QtWidgets.QLineEdit(self)
        form_layout.addWidget(self.geofence_buffer)

        # Geofence Units
        self.geofence_units = QComboBox(self)
        self.geofence_units.addItems(["Feet", "Meters"])
        form_layout.addWidget(self.geofence_units)

        # Landing Behavior at Point B
        form_layout.addWidget(QLabel("Landing Behavior at Point B:"))
        self.landing_behavior = QComboBox(self)
        self.landing_behavior.addItems(["Payload Mechanism", "Land and Takeoff When Commanded to Return"])
        form_layout.addWidget(self.landing_behavior)

        # Button to generate .plan file
        self.generate_btn = QtWidgets.QPushButton("Generate .plan File", self)
        self.generate_btn.clicked.connect(self.generate_plan)
        form_layout.addWidget(self.generate_btn)

        # Button to open .plan file in QGroundControl (initially disabled)
        self.open_btn = QtWidgets.QPushButton("Open in QGroundControl", self)
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.open_in_qgroundcontrol)
        form_layout.addWidget(self.open_btn)

        # Button to visualize altitude profile (initially disabled)
        self.visualize_btn = QtWidgets.QPushButton("Visualize Altitude Profile", self)
        self.visualize_btn.setEnabled(False)
        self.visualize_btn.clicked.connect(self.visualize_altitude)
        form_layout.addWidget(self.visualize_btn)

        # Progress bar for generating .plan file
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)
        form_layout.addWidget(self.progress_bar)

        main_layout.addLayout(form_layout, 1)
        self.setLayout(main_layout)

    def toggle_instructions(self):
        if self.toggle_instructions_btn.isChecked():
            self.instructions_label.setVisible(True)
            self.toggle_instructions_btn.setText("Hide Instructions")
        else:
            self.instructions_label.setVisible(False)
            self.toggle_instructions_btn.setText("Show Instructions")

    def parse_coordinates(self, coord_text):
        try:
            lat, lon = map(float, coord_text.split(','))
            return lat, lon
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in 'lat,lon' format.")
            return None, None

    def interpolate_waypoints(self, start, end, interval):
        start_lat, start_lon = start
        end_lat, end_lon = end
        distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)
        num_points = int(distance // interval) + 1
        latitudes = np.linspace(start_lat, end_lat, num_points)
        longitudes = np.linspace(start_lon, end_lon, num_points)
        return list(zip(latitudes, longitudes))

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def offset_waypoints(self, waypoints, offset_distance):
        offset_points = []
        bearings = [0, 90, 180, 270]

        for lat, lon in waypoints:
            for bearing in bearings:
                offset_point = geopy_distance(meters=offset_distance).destination((lat, lon), bearing)
                offset_points.append((offset_point.latitude, offset_point.longitude))
        return offset_points

    def generate_geofence(self, offset_points):
        points = MultiPoint([Point(lon, lat) for lat, lon in offset_points])
        hull = points.convex_hull
        return [[coord[1], coord[0]] for coord in hull.exterior.coords]

    def convert_to_meters(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def validate_numeric_input(self, text, field_name):
        try:
            value = float(text)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", f"Please enter a positive number for {field_name}.")
            return None

    def add_takeoff_command(self, mission_items, start_lat, start_lon, altitude_meters):
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            mission_items.append({
                "command": 22,  # TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "Fixed Wing":
            mission_items.append({
                "command": 22,  # TAKEOFF (Fixed Wing uses command 22 with frame 3)
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "Quadplane/VTOL Hybrid":
            mission_items.append({
                "command": 84,  # VTOL TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })

    def add_waypoint_command(self, mission_items, index, lat, lon, altitude_meters):
        terrain_elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = terrain_elevation + altitude_meters

        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,  # ✅ Now includes terrain elevation
            "Altitude": altitude_meters,  # ✅ AGL (user-defined altitude above terrain)
            "AltitudeMode": 3,  # ✅ Mode 3 = Terrain Following
            "autoContinue": True,
            "command": 16,  # Waypoint command
            "doJumpId": index + 2,
            "frame": 0,  # ✅ Use absolute altitude frame
            "params": [0, 0, 0, None, lat, lon, amsl_altitude],
            "type": "SimpleItem"
        })

    def add_vtol_transition_command(self, mission_items, transition_mode):
        mission_items.append({
            "command": 3000,  # VTOL TRANSITION
            "doJumpId": len(mission_items) + 1,
            "frame": 2,
            "params": [transition_mode, 0, 0, 0, 0, 0, 0],
            "type": "SimpleItem",
            "autoContinue": True
        })

    def add_landing_or_loiter_command(self, mission_items, lat, lon, altitude_meters):
        aircraft_type = self.aircraft_type.currentText()

        # **Lower altitude to 20 feet (6.096 meters) at the loiter waypoint**
        loiter_altitude_meters = 6.096  # 20 feet in meters

        # **Always Loiter at Delivery Waypoint**
        mission_items.append({
            "AMSLAltAboveTerrain": loiter_altitude_meters,
            "Altitude": loiter_altitude_meters,
            "AltitudeMode": 3,
            "autoContinue": False,
            "command": 19,  # LOITER_UNLIMITED
            "doJumpId": len(mission_items) + 1,
            "frame": 3,
            "params": [0, 0, 0, None, lat, lon, loiter_altitude_meters],
            "type": "SimpleItem"
        })

        # **Gripper Release (Drop Payload)**
        if self.landing_behavior.currentText() == "Payload Mechanism":
            mission_items.append({
                "autoContinue": True,
                "command": 211,  # DO_GRIPPER (release payload)
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [2, 0, 0, 0, 0, 0, 0],  # "2" assumes release action
                "type": "SimpleItem"
            })

    def add_fixed_wing_landing_pattern(self, mission_items, start_lat, start_lon, home_elevation, altitude_meters):
        """Add a fixed-wing landing pattern to the mission."""
        landing_approach_coord = [
            start_lat + 0.001,  # Adjust these values as needed
            start_lon + 0.001,
            home_elevation + altitude_meters  # Use user-defined altitude above terrain
        ]

        mission_items.append({
            "altitudesAreRelative": True,
            "complexItemType": "fwLandingPattern",
            "landCoordinate": [start_lat, start_lon, 0],
            "landingApproachCoordinate": landing_approach_coord,
            "loiterClockwise": True,
            "loiterRadius": 75,
            "stopTakingPhotos": True,
            "stopVideoPhotos": True,
            "type": "ComplexItem",
            "useLoiterToAlt": True,
            "valueSetIsDistance": False,
            "version": 2
        })

    def compile_plan_data(self, mission_items, geofence_coords, start_lat, start_lon, home_elevation):
        return {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [{"polygon": geofence_coords, "inclusion": True, "version": 1}],
                "version": 2
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": 15,
                "hoverSpeed": 5,
                "firmwareType": 12,
                "globalPlanAltitudeMode": 3,
                "items": mission_items,
                "plannedHomePosition": [start_lat, start_lon, home_elevation],  # ✅ Uses real terrain altitude
                "vehicleType": 1 if self.aircraft_type.currentText() == "Fixed Wing" else 2,
                "version": 2
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QtWidgets.QApplication.processEvents()

    def generate_plan(self):
        # Validate and parse coordinates
        start_lat, start_lon = self.parse_coordinates(self.start_coords.text())
        end_lat, end_lon = self.parse_coordinates(self.end_coords.text())
        if None in (start_lat, start_lon, end_lat, end_lon):
            return

        home_elevation = self.terrain_query.get_elevation(start_lat, start_lon)

        altitude_meters = self.validate_numeric_input(self.altitude.text(), "Altitude")
        interval_meters = self.validate_numeric_input(self.interval.text(), "Waypoint Interval")
        geofence_buffer_meters = self.validate_numeric_input(self.geofence_buffer.text(), "Geofence Buffer")
        if None in (altitude_meters, interval_meters, geofence_buffer_meters):
            return

        altitude_meters = self.convert_to_meters(altitude_meters, self.altitude_units.currentText())
        interval_meters = self.convert_to_meters(interval_meters, self.interval_units.currentText())
        geofence_buffer_meters = self.convert_to_meters(geofence_buffer_meters, self.geofence_units.currentText())

        self.waypoints = self.interpolate_waypoints((start_lat, start_lon), (end_lat, end_lon), interval_meters)
        mission_items = []

        offset_points = self.offset_waypoints(self.waypoints, geofence_buffer_meters)
        geofence_coords = self.generate_geofence(offset_points)

        aircraft_type = self.aircraft_type.currentText()
        landing_behavior = self.landing_behavior.currentText()

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum((len(self.waypoints) * 2) + 5)
        self.progress_bar.setValue(0)

        # **1️⃣ Takeoff**
        self.add_takeoff_command(mission_items, start_lat, start_lon, altitude_meters)

        # **2️⃣ Outbound Waypoints (STOP before final delivery)**
        for i, (lat, lon) in enumerate(self.waypoints[:-1]):  # Exclude last delivery point for now
            self.add_waypoint_command(mission_items, i + 1, lat, lon, altitude_meters)
            self.update_progress(i + 1)

        # **3️⃣ Delivery Handling**
        final_lat, final_lon = self.waypoints[-1]

        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition to Multirotor Before Delivery**
            self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)

        # **Loiter at Delivery Waypoint (20 feet altitude)**
        self.add_landing_or_loiter_command(mission_items, final_lat, final_lon, altitude_meters)

        # **Payload Mechanism or Landing Behavior**
        if landing_behavior == "Land and Takeoff When Commanded to Return":
            # **Land at Point B**
            mission_items.append({
                "command": 21,  # LAND
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [0, 0, 0, None, final_lat, final_lon, 0],
                "type": "SimpleItem",
                "autoContinue": True
            })

        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition Back to Fixed-Wing After Drop**
            self.add_vtol_transition_command(mission_items, 4)  # Transition to Fixed-Wing (mode 4)

        # **4️⃣ Return Waypoints (Back to Home)**
        for i, (lat, lon) in enumerate(reversed(self.waypoints[:-1])):  # Reverse outbound waypoints without last point
            self.add_waypoint_command(mission_items, len(mission_items) + 1, lat, lon, altitude_meters)
            self.update_progress(len(self.waypoints) + i + 2)

        # **5️⃣ Landing at Home**
        if aircraft_type == "Quadplane/VTOL Hybrid":
            # **Transition to Multirotor for Landing**
            self.add_vtol_transition_command(mission_items, 3)  # Transition to Multirotor (mode 3)

            # **Land at Home**
            mission_items.append({
                "command": 85,  # VTOL Land
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, 0],
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "Fixed Wing":
            # **Add Fixed-Wing Landing Pattern**
            self.add_fixed_wing_landing_pattern(mission_items, start_lat, start_lon, home_elevation, altitude_meters)

        # **6️⃣ Add Land Waypoint at the End**
        if aircraft_type != "Fixed Wing":  # Fixed-wing uses a landing pattern, so no need for a separate land command
            mission_items.append({
                "command": 21,  # LAND
                "doJumpId": len(mission_items) + 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, 0],
                "type": "SimpleItem",
                "autoContinue": True
            })

        # Compile the plan data
        plan_data = self.compile_plan_data(mission_items, geofence_coords, start_lat, start_lon, home_elevation)

        # Save the plan file
        filename, _ = QFileDialog.getSaveFileName(self, "Save Plan File", "", "Plan Files (*.plan)")
        if filename:
            with open(filename, 'w') as file:
                json.dump(plan_data, file, indent=2)
            self.plan_file_path = filename
            self.open_btn.setEnabled(True)
            self.visualize_btn.setEnabled(True)

        # Hide progress bar
        self.progress_bar.setVisible(False)

    def visualize_altitude(self):
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        altitudes_agl = []
        altitudes_amsl = []

        altitude_meters = self.convert_to_meters(float(self.altitude.text()), self.altitude_units.currentText())

        for lat, lon in self.waypoints:
            altitudes_agl.append(altitude_meters)
            altitudes_amsl.append(altitude_meters)  # ✅ Use only AGL altitude

        plt.figure(figsize=(10, 5))
        plt.plot(range(len(self.waypoints)), altitudes_amsl, label='AGL Altitude (meters)')
        plt.xlabel('Waypoint Index')
        plt.ylabel('Altitude (meters)')
        plt.title('Altitude Profile')
        plt.legend()
        plt.grid(True)
        plt.show()

    def open_in_qgroundcontrol(self):
        if self.plan_file_path:
            subprocess.run(["qgroundcontrol", self.plan_file_path], check=True)


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = DeliveryRoute()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()