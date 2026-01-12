import sys
import json
from PyQt5 import QtWidgets, QtWebEngineWidgets
from PyQt5.QtWidgets import QFileDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QMessageBox
from PyQt5.QtCore import QUrl, Qt
import math


class TowerInspection(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Tower Inspection Planner")
        self.setGeometry(100, 100, 1200, 800)

        main_layout = QtWidgets.QHBoxLayout(self)

        # Left Panel: Map View
        left_layout = QtWidgets.QVBoxLayout()
        self.map_view = QtWebEngineWidgets.QWebEngineView()
        self.map_view.setUrl(QUrl("https://www.google.com/maps"))
        left_layout.addWidget(self.map_view)

        # Right Panel: Input Form and Buttons
        right_layout = QtWidgets.QVBoxLayout()

        # Input fields
        right_layout.addWidget(QLabel("Takeoff and Landing Coordinates (lat, lon):"))
        self.takeoff_coords = QLineEdit()
        right_layout.addWidget(self.takeoff_coords)

        right_layout.addWidget(QLabel("Tower Coordinates (lat, lon):"))
        self.tower_coords = QLineEdit()
        right_layout.addWidget(self.tower_coords)

        # Offset Distance Input
        right_layout.addWidget(QLabel("Waypoint Offset Distance:"))
        offset_layout = QtWidgets.QHBoxLayout()
        self.offset_distance = QLineEdit()
        self.offset_distance.setPlaceholderText("Enter offset distance")
        offset_layout.addWidget(self.offset_distance)

        self.offset_units = QComboBox()
        self.offset_units.addItems(["Meters", "Feet"])
        offset_layout.addWidget(self.offset_units)
        right_layout.addLayout(offset_layout)

        # Generate Plan Button
        self.generate_btn = QPushButton("Generate Flight Plan")
        self.generate_btn.clicked.connect(self.generate_flight_plan)
        right_layout.addWidget(self.generate_btn)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

    def generate_flight_plan(self):
        try:
            # Parse input coordinates
            takeoff_lat, takeoff_lon = map(float, self.takeoff_coords.text().split(","))
            tower_lat, tower_lon = map(float, self.tower_coords.text().split(","))
            offset_distance = float(self.offset_distance.text())

            # Convert offset distance to meters if necessary
            if self.offset_units.currentText() == "Feet":
                offset_distance *= 0.3048  # Convert feet to meters

            altitude_takeoff = 3.048  # 10 feet (fixed for takeoff)
            altitude_inspection = 30.48  # 100 feet (fixed for inspection)

            # Define waypoints and mission items
            mission_items = self.create_mission_items(
                takeoff_lat, takeoff_lon, tower_lat, tower_lon, altitude_takeoff, altitude_inspection, offset_distance
            )

            # Define rectangular geofence
            geofence_polygon = self.create_geofence_rectangle(takeoff_lat, takeoff_lon, tower_lat, tower_lon)

            # Save the .plan file
            self.save_plan_file(takeoff_lat, takeoff_lon, mission_items, geofence_polygon)

        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid coordinates and offset distance.")

    def create_mission_items(self, takeoff_lat, takeoff_lon, tower_lat, tower_lon, altitude_takeoff, altitude_inspection, offset_distance):
        """Generate mission items with user-defined takeoff, landing, and ROI."""
        mission_items = []

        # 1. Takeoff
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": altitude_takeoff,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 22,
            "doJumpId": 1,
            "frame": 3,
            "params": [0, 0, 0, None, takeoff_lat, takeoff_lon, altitude_takeoff],
            "type": "SimpleItem",
        })

        # 2. ROI (Region of Interest) - Tower Center
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": 0,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 201,  # MAV_CMD_DO_SET_ROI_LOCATION
            "doJumpId": 2,
            "frame": 3,
            "params": [0, 0, 0, None, tower_lat, tower_lon, 0],
            "type": "SimpleItem",
        })

        # Adjust latitude and longitude offsets for the given distance
        lat_offset = offset_distance / 111320  # Approximate meters to degrees latitude
        lon_offset = offset_distance / (111320 * math.cos(math.radians(tower_lat)))

        # Generate waypoints offset from the tower
        waypoints = [
            (tower_lat + lat_offset, tower_lon + lon_offset),
            (tower_lat - lat_offset, tower_lon + lon_offset),
            (tower_lat - lat_offset, tower_lon - lon_offset),
            (tower_lat + lat_offset, tower_lon - lon_offset),
        ]

        for i, (way_lat, way_lon) in enumerate(waypoints, start=3):
            # Low-altitude waypoint
            mission_items.append({
                "AMSLAltAboveTerrain": None,
                "Altitude": altitude_takeoff,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 16,
                "doJumpId": i * 2 - 1,
                "frame": 3,
                "params": [0, 0, 0, None, way_lat, way_lon, altitude_takeoff],
                "type": "SimpleItem",
            })

            # High-altitude waypoint
            mission_items.append({
                "AMSLAltAboveTerrain": None,
                "Altitude": altitude_inspection,
                "AltitudeMode": 1,
                "autoContinue": True,
                "command": 16,
                "doJumpId": i * 2,
                "frame": 3,
                "params": [0, 0, 0, None, way_lat, way_lon, altitude_inspection],
                "type": "SimpleItem",
            })

        # Return to Landing
        mission_items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": altitude_takeoff,
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 16,
            "doJumpId": len(mission_items) + 1,
            "frame": 3,
            "params": [0, 0, 0, None, takeoff_lat, takeoff_lon, altitude_takeoff],
            "type": "SimpleItem",
        })

        # Land
        mission_items.append({
            "autoContinue": True,
            "command": 20,
            "doJumpId": len(mission_items) + 2,
            "frame": 2,
            "params": [0, 0, 0, 0, 0, 0, 0],
            "type": "SimpleItem",
        })

        return mission_items

    def create_geofence_rectangle(self, takeoff_lat, takeoff_lon, tower_lat, tower_lon):
        """Create a rectangular geofence combining takeoff and tower areas."""
        lat_offset = 0.0003  # ~30 meters offset
        lon_offset = 0.0005  # ~50 meters offset

        return [
            [max(takeoff_lat, tower_lat) + lat_offset, min(takeoff_lon, tower_lon) - lon_offset],
            [max(takeoff_lat, tower_lat) + lat_offset, max(takeoff_lon, tower_lon) + lon_offset],
            [min(takeoff_lat, tower_lat) - lat_offset, max(takeoff_lon, tower_lon) + lon_offset],
            [min(takeoff_lat, tower_lat) - lat_offset, min(takeoff_lon, tower_lon) - lon_offset],
        ]

    def save_plan_file(self, takeoff_lat, takeoff_lon, mission_items, geofence_polygon):
        """Save the flight plan to a .plan file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Plan File", "", ".plan")
        if not filename:
            return

        plan_data = {
            "fileType": "Plan",
            "geoFence": {
                "circles": [],
                "polygons": [{"inclusion": True, "polygon": geofence_polygon, "version": 1}],
                "version": 2,
            },
            "groundStation": "QGroundControl",
            "mission": {
                "cruiseSpeed": 15,
                "firmwareType": 12,
                "globalPlanAltitudeMode": 1,
                "hoverSpeed": 5,
                "items": mission_items,
                "plannedHomePosition": [takeoff_lat, takeoff_lon, 70],
                "vehicleType": 2,
                "version": 2,
            },
            "rallyPoints": {"points": [], "version": 2},
            "version": 1,
        }

        with open(filename, "w") as file:
            json.dump(plan_data, file, indent=2)

        QMessageBox.information(self, "Plan Saved", f"Plan saved to {filename}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    planner = TowerInspection()
    planner.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
