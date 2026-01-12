import json
import sys
import time
import requests
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QLabel, QPushButton, QProgressBar, QComboBox, QVBoxLayout, QLineEdit, QListWidget, QHBoxLayout
from PyQt5.QtCore import QUrl, Qt
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
from geopy.distance import distance as geopy_distance


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


class MultiDelivery(QtWidgets.QWidget):
    """
    MultiDelivery: UI and logic for the multi-delivery mission planning tool.
    """
    def __init__(self):
        super().__init__()
        self.terrain_query = TerrainQuery()
        self.plan_file_path = None
        self.delivery_points = []  # To store delivery locations
        self.initUI()

    def initUI(self):
        self.setWindowTitle("UAV Multiple Delivery Mission Planner")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QtWidgets.QHBoxLayout(self)

        # Left side: Map view and instructions
        left_layout = QtWidgets.QVBoxLayout()

        # Collapsible Instructions with Toggle Button
        self.instructions_label = QLabel(
            "Instructions:\n"
            "1. Use the map to visualize your delivery route.\n"
            "2. Enter the start coordinates and multiple delivery locations below.\n"
            "3. Adjust settings (altitude, interval, geofence) as required.\n"
            "4. Specify delivery actions for each location: Loiter, Gripper, or Land.\n"
            "5. Choose the aircraft type and the final action (land or return to takeoff).\n"
            "6. Click 'Generate .plan File' to create the mission plan.\n"
            "7. Use QGroundControl to execute or simulate the mission."
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
        self.start_coords = QLineEdit(self)
        form_layout.addWidget(self.start_coords)

        # Delivery Points Section
        form_layout.addWidget(QLabel("Add Delivery Coordinates (lat,lon):"))
        delivery_input_layout = QHBoxLayout()
        self.delivery_coords_input = QLineEdit(self)
        self.add_delivery_btn = QPushButton("Add Delivery Point")
        self.add_delivery_btn.clicked.connect(self.add_delivery_point)
        delivery_input_layout.addWidget(self.delivery_coords_input)
        delivery_input_layout.addWidget(self.add_delivery_btn)
        form_layout.addLayout(delivery_input_layout)

        # List of delivery points
        self.delivery_points_list = QListWidget()
        self.delivery_points_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        form_layout.addWidget(self.delivery_points_list)

        # Aircraft Type Selection
        form_layout.addWidget(QLabel("Select Aircraft Type:"))
        self.aircraft_type = QComboBox(self)
        self.aircraft_type.addItems(["Multicopter/Helicopter", "Fixed Wing", "VTOL/Fixed Wing Hybrid"])
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

        # Delivery Action Selection
        form_layout.addWidget(QLabel("Delivery Action:"))
        self.delivery_action = QComboBox(self)
        self.delivery_action.addItems(["Release Mechanism", "Land at Delivery Location"])
        form_layout.addWidget(self.delivery_action)

        # Final Action Selection
        form_layout.addWidget(QLabel("Final Action:"))
        self.final_action = QComboBox(self)
        self.final_action.addItems(["Land at Final Delivery Location", "Return to Takeoff Location"])
        form_layout.addWidget(self.final_action)

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

    def parse_coordinates(self, coord_text):
        try:
            lat, lon = map(float, coord_text.split(','))
            return lat, lon
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter coordinates in 'lat,lon' format.")
            return None, None

    def add_delivery_point(self):
        """Adds a delivery location to the list."""
        lat, lon = self.parse_coordinates(self.delivery_coords_input.text())
        if lat is not None and lon is not None:
            self.delivery_points.append((lat, lon))
            self.delivery_points_list.addItem(f"{lat}, {lon}")
            self.delivery_coords_input.clear()

    def open_in_qgroundcontrol(self):
        """Opens the generated plan file in QGroundControl if available."""
        if self.plan_file_path:
            try:
                subprocess.run(["qgroundcontrol", self.plan_file_path], check=True)
            except FileNotFoundError:
                QMessageBox.warning(self, "Error", "QGroundControl is not installed or not in the system PATH.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to open QGroundControl: {e}")

    def interpolate_waypoints(self, start, end, interval):
        """
        Generates interpolated waypoints between two geographic coordinates.

        Args:
            start (tuple): Starting coordinates as (latitude, longitude).
            end (tuple): Ending coordinates as (latitude, longitude).
            interval (float): Distance between waypoints in meters.

        Returns:
            list: List of interpolated waypoints as (latitude, longitude) tuples.
        """
        start_lat, start_lon = start
        end_lat, end_lon = end
        distance = self.haversine_distance(start_lat, start_lon, end_lat, end_lon)

        # Calculate the number of waypoints needed
        num_points = max(int(distance // interval) + 1, 2)

        # Interpolate waypoints between start and end points
        latitudes = np.linspace(start_lat, end_lat, num_points)
        longitudes = np.linspace(start_lon, end_lon, num_points)
        return list(zip(latitudes, longitudes))

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculates the great-circle distance between two points on Earth.

        Args:
            lat1 (float): Latitude of the first point in decimal degrees.
            lon1 (float): Longitude of the first point in decimal degrees.
            lat2 (float): Latitude of the second point in decimal degrees.
            lon2 (float): Longitude of the second point in decimal degrees.

        Returns:
            float: Distance in meters.
        """
        R = 6371000  # Radius of Earth in meters
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)

        a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
        return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    def generate_geofence(self, waypoints, buffer_distance, extra_buffer_points, loiter_radius=None):
        """
        Generates a geofence around the flight path with additional buffer points for takeoff and landing.

        Args:
            waypoints (list): List of (latitude, longitude) tuples for the flight path.
            buffer_distance (float): Buffer distance in meters for the flight path.
            extra_buffer_points (list): List of (latitude, longitude) points for additional buffers (e.g., takeoff and landing).
            loiter_radius (float): Radius of the loiter waypoint in meters (optional).

        Returns:
            list: List of [longitude, latitude] pairs representing the geofence.
        """
        # Create a LineString from the waypoints
        line = LineString([(lon, lat) for lat, lon in waypoints])

        # Buffer the flight path
        buffered_area = line.buffer(buffer_distance / 111320.0, cap_style=2)  # Convert meters to degrees

        # Add buffers around extra points (e.g., takeoff and landing)
        extra_buffers = [Point(lon, lat).buffer(200 / 111320.0) for lat, lon in extra_buffer_points]  # 200 ft buffer

        # If a loiter radius is provided, add a buffer for the loiter area
        if loiter_radius is not None:
            # Add a buffer for the loiter waypoint
            loiter_buffer = Point(waypoints[-1][1], waypoints[-1][0]).buffer(loiter_radius / 111320.0)
            extra_buffers.append(loiter_buffer)

        # Combine all buffers
        combined_area = unary_union([buffered_area] + extra_buffers)

        # Extract the exterior of the combined polygon
        geofence_coords = list(combined_area.exterior.coords)

        # Convert back to [latitude, longitude] format
        return [[coord[1], coord[0]] for coord in geofence_coords]

    def add_takeoff_command(self, mission_items, start_lat, start_lon, altitude_meters):
        """Adds a takeoff command based on aircraft type."""
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
                "command": 22,  # FIXED_WING_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [15, 0, 0, None, start_lat, start_lon, altitude_meters],  # 15 m/s pitch
                "type": "SimpleItem",
                "autoContinue": True
            })
        elif aircraft_type == "VTOL/Fixed Wing Hybrid":
            mission_items.append({
                "command": 84,  # VTOL_TAKEOFF
                "doJumpId": 1,
                "frame": 3,
                "params": [0, 0, 0, None, start_lat, start_lon, altitude_meters],
                "type": "SimpleItem",
                "autoContinue": True
            })

    def add_waypoint_command(self, mission_items, index, lat, lon, altitude_meters):
        """Adds a waypoint command to the mission."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = elevation + altitude_meters
        mission_items.append({
            "AMSLAltAboveTerrain": amsl_altitude,
            "Altitude": altitude_meters,
            "AltitudeMode": 3,
            "autoContinue": True,
            "command": 16,
            "doJumpId": index + 2,
            "frame": 0,  # Use absolute altitude frame
            "params": [0, 0, 0, None, lat, lon, amsl_altitude],
            "type": "SimpleItem"
        })

    def add_loiter_command(self, mission_items, lat, lon, altitude_meters):
        """Adds a loiter command to the mission."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        amsl_altitude = elevation + altitude_meters
        mission_items.append({
            "autoContinue": True,
            "command": 183,  # LOITER_TO_ALT
            "doJumpId": len(mission_items) + 1,
            "frame": 2,
            "params": [1, 2000, 0, 0, 0, 0, 0],  # Loiter for 2000 seconds
            "type": "SimpleItem"
        })

    def add_landing_pattern(self, mission_items, land_lat, land_lon, approach_lat, approach_lon, altitude_meters):
        """Adds a fixed-wing landing pattern to the mission with dynamic distance offset."""
        # Calculate the distance offset based on altitude
        base_altitude_meters = 15.24  # 50 feet in meters
        base_distance_meters = 75  # Base distance offset at 50 feet
        altitude_difference = altitude_meters - base_altitude_meters
        distance_offset = base_distance_meters + (altitude_difference * (15 / 3.048))  # 15 meters per 10 feet

        # Ensure the distance offset is not too small
        distance_offset = max(distance_offset, 50)  # Minimum distance offset of 50 meters

        # Calculate the approach coordinates based on the distance offset
        approach_lat = land_lat + (distance_offset / 111320.0)  # 1 degree ≈ 111,320 meters
        approach_lon = land_lon + (distance_offset / (111320.0 * np.cos(np.radians(land_lat))))

        mission_items.append({
            "altitudesAreRelative": True,
            "complexItemType": "fwLandingPattern",
            "landCoordinate": [land_lat, land_lon, 0],
            "landingApproachCoordinate": [approach_lat, approach_lon, altitude_meters],
            "loiterClockwise": True,
            "loiterRadius": distance_offset,  # Use dynamic distance offset
            "stopTakingPhotos": True,
            "stopVideoPhotos": True,
            "type": "ComplexItem",
            "useLoiterToAlt": True,
            "valueSetIsDistance": False,
            "version": 2
        })

    def generate_plan(self):
        """Generates a flight plan for multiple delivery locations."""
        # Parse start coordinates
        start_lat, start_lon = self.parse_coordinates(self.start_coords.text())
        if None in (start_lat, start_lon):
            return

        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())
        interval_meters = self.convert_units(float(self.interval.text()), self.interval_units.currentText())
        geofence_buffer_meters = self.convert_units(float(self.geofence_buffer.text()), self.geofence_units.currentText())
        mission_items = []

        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.delivery_points) * 10 + 10)  # Approximation
        self.progress_bar.setValue(0)

        # Takeoff based on aircraft type
        self.add_takeoff_command(mission_items, start_lat, start_lon, altitude_meters)

        # Delivery points
        current_location = (start_lat, start_lon)
        all_waypoints = [current_location]
        for i, (lat, lon) in enumerate(self.delivery_points):
            waypoints = self.interpolate_waypoints(current_location, (lat, lon), interval_meters)
            all_waypoints.extend(waypoints)
            for waypoint_lat, waypoint_lon in waypoints:
                self.add_waypoint_command(mission_items, i, waypoint_lat, waypoint_lon, altitude_meters)
                self.progress_bar.setValue(self.progress_bar.value() + 1)

            # Add delivery-specific actions (Loiter, Gripper, or Land)
            self.add_delivery_action(mission_items, i, lat, lon, altitude_meters)
            current_location = (lat, lon)

        # Handle final action and geofence points
        extra_buffer_points = [(start_lat, start_lon)]  # Always include takeoff point
        if self.final_action.currentText() == "Return to Takeoff Location":
            # Interpolate return route
            waypoints = self.interpolate_waypoints(current_location, (start_lat, start_lon), interval_meters)
            all_waypoints.extend(waypoints)
            for waypoint_lat, waypoint_lon in waypoints:
                self.add_waypoint_command(mission_items, len(mission_items), waypoint_lat, waypoint_lon, altitude_meters)
                self.progress_bar.setValue(self.progress_bar.value() + 1)

            # Add loiter command before landing
            self.add_loiter_command(mission_items, start_lat, start_lon, altitude_meters)

            # Add landing pattern with dynamic distance offset
            approach_lat = start_lat + 0.001  # Temporary value, will be recalculated
            approach_lon = start_lon + 0.001  # Temporary value, will be recalculated
            self.add_landing_pattern(mission_items, start_lat, start_lon, approach_lat, approach_lon, altitude_meters)

            # Generate geofence with loiter radius
            loiter_radius = self.calculate_loiter_radius(altitude_meters)
            geofence_coords = self.generate_geofence(all_waypoints, geofence_buffer_meters, extra_buffer_points, loiter_radius)
        else:
            # Add loiter command before landing
            self.add_loiter_command(mission_items, current_location[0], current_location[1], altitude_meters)

            # Add landing pattern with dynamic distance offset
            approach_lat = current_location[0] + 0.001  # Temporary value, will be recalculated
            approach_lon = current_location[1] + 0.001  # Temporary value, will be recalculated
            self.add_landing_pattern(mission_items, current_location[0], current_location[1], approach_lat, approach_lon, altitude_meters)
            extra_buffer_points.append(current_location)  # Include final delivery point

            # Generate geofence with loiter radius
            loiter_radius = self.calculate_loiter_radius(altitude_meters)
            geofence_coords = self.generate_geofence(all_waypoints, geofence_buffer_meters, extra_buffer_points, loiter_radius)

        # Compile the plan data
        plan_data = self.compile_plan_data(mission_items, start_lat, start_lon, geofence_coords)

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

    def add_delivery_action(self, mission_items, index, lat, lon, altitude_meters):
        """Adds delivery-specific actions (Loiter, Gripper, or Land)."""
        elevation = self.terrain_query.get_elevation(lat, lon)
        loiter_altitude = self.convert_units(20, "Feet")  # 20 feet above terrain

        if self.delivery_action.currentText() == "Release Mechanism":
            # Loiter waypoint
            mission_items.append({
                "AMSLAltAboveTerrain": elevation + loiter_altitude,
                "Altitude": loiter_altitude,
                "AltitudeMode": 3,
                "autoContinue": False,
                "command": 19,  # LOITER_UNLIMITED
                "doJumpId": index + 3,
                "frame": 3,
                "params": [0, 0, 0, None, lat, lon, elevation + loiter_altitude],
                "type": "SimpleItem"
            })

            # Gripper mechanism (package release)
            mission_items.append({
                "command": 211,  # DO_GRIPPER
                "doJumpId": index + 4,
                "frame": 3,
                "params": [2, 0, 0, 0, 0, 0, 0],  # Gripper release
                "type": "SimpleItem",
                "autoContinue": True
            })
        else:
            # Land at delivery location
            self.add_landing_command(mission_items, lat, lon)

            # Takeoff after landing
            self.add_takeoff_command(mission_items, lat, lon, altitude_meters)

    def add_landing_command(self, mission_items, lat, lon):
        """Adds a landing command based on aircraft type."""
        aircraft_type = self.aircraft_type.currentText()
        if aircraft_type == "Multicopter/Helicopter":
            command = 21  # LAND
        elif aircraft_type == "Fixed Wing":
            command = 21  # LAND
        elif aircraft_type == "VTOL/Fixed Wing Hybrid":
            command = 85  # VTOL_LAND

        mission_items.append({
            "command": command,
            "doJumpId": len(mission_items) + 1,
            "frame": 3,
            "params": [0, 0, 0, None, lat, lon, 0],
            "type": "SimpleItem",
            "autoContinue": True
        })

    def compile_plan_data(self, mission_items, start_lat, start_lon, geofence_coords):
        """Compiles the mission data into the .plan format."""
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
                "plannedHomePosition": [start_lat, start_lon, 70],
                "vehicleType": 1 if self.aircraft_type.currentText() == "Fixed Wing" else 2,
                "version": 2
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1
        }

    def convert_units(self, value, units):
        """Convert input value to meters based on units (Feet or Meters)."""
        if units == "Feet":
            return value * 0.3048
        return value

    def calculate_loiter_radius(self, altitude_meters):
        """Calculates the loiter radius based on altitude."""
        base_altitude_meters = 15.24  # 50 feet in meters
        base_radius_meters = 75  # Base radius at 50 feet
        altitude_difference = altitude_meters - base_altitude_meters
        loiter_radius = base_radius_meters + (altitude_difference * (15 / 3.048))  # 15 meters per 10 feet
        return max(loiter_radius, 50)  # Minimum radius of 50 meters

    def visualize_altitude(self):
        """Visualizes the altitude profile of the mission."""
        if not self.waypoints:
            QMessageBox.warning(self, "No Data", "No waypoints available for visualization.")
            return

        altitudes_agl = []
        altitudes_amsl = []

        altitude_meters = self.convert_units(float(self.altitude.text()), self.altitude_units.currentText())

        for lat, lon in self.waypoints:
            elevation = self.terrain_query.get_elevation(lat, lon)
            altitudes_agl.append(altitude_meters)
            altitudes_amsl.append(elevation + altitude_meters)

        plt.figure(figsize=(10, 5))
        plt.plot(range(len(self.waypoints)), altitudes_amsl, label='AMSL Altitude (meters)')
        plt.plot(range(len(self.waypoints)), altitudes_agl, label='AGL Altitude (meters)', linestyle='--')
        plt.xlabel('Waypoint Index')
        plt.ylabel('Altitude (meters)')
        plt.title('Altitude Profile')
        plt.legend()
        plt.grid(True)
        plt.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = MultiDelivery()  # Updated class name
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()