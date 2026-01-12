import sys
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QStackedWidget, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics

# Import external components
from atob_mission_planner import MissionPlanner
from deliveryroute import DeliveryRoute
from multidelivery import MultiDelivery
from securityroute import SecurityRoute
from linearflightroute import LinearFlightRoute
from towerinspection import TowerInspection


# Centralized Styling
def get_button_style():
    return """
        QPushButton {
            font-size: 18px;
            padding: 10px 20px;
            background-color: #0078D7;
            color: white;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #005BB5;
        }
    """


def get_dark_theme():
    return """
        QMainWindow {
            background-color: #2C2C2C;
        }
        QListWidget {
            background-color: #3C3C3C;
            color: white;
            border: none;
        }
        QListWidget::item {
            padding: 10px;
            font-size: 14px;
        }
        QListWidget::item:selected {
            background-color: #555555;
        }
        QStackedWidget {
            background-color: white;
            border: 1px solid #CCCCCC;
        }
        QLabel {
            font-size: 16px;
            color: #888888;
        }
    """


# Opening Page
class OpeningPage(QWidget):
    def __init__(self, switch_page):
        super().__init__()
        self.switch_page = switch_page

        # Main Layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Title
        title = QLabel("Welcome to QGC Automated Flight Planner")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")

        # Introduction Text
        intro_text = QLabel(
            "This tool allows you to create automated flight plans for various scenarios, "
            "including point-to-point navigation, delivery routes, security inspections, and more. "
            "For instructions and tutorials, click on the 'Tutorials' button below."
        )
        intro_text.setWordWrap(True)  # Enable line wrapping
        intro_text.setAlignment(Qt.AlignCenter)
        intro_text.setStyleSheet("font-size: 16px; padding: 10px;")

        # Buttons
        tutorials_button = QPushButton("Tutorials")

        # Apply Button Style
        button_style = get_button_style()
        tutorials_button.setStyleSheet(button_style)

        # Add Widgets to Layout
        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(intro_text)
        layout.addSpacing(20)
        layout.addWidget(tutorials_button)

        # Connect Buttons
        tutorials_button.clicked.connect(self.open_tutorials)

        self.setLayout(layout)

    def open_tutorials(self):
        """Open the video tutorial website."""
        url = "https://jamesm9.github.io/versarouteplanner.github.io/#installation"  # Replace with your actual URL
        webbrowser.open(url)


# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QGC Automated Flight Planner")
        self.setGeometry(100, 100, 1000, 600)

        # Apply Dark Theme
        self.setStyleSheet(get_dark_theme())

        # Main Widget and Layout
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        self.setCentralWidget(main_widget)

        # Sidebar for Navigation
        self.sidebar = QListWidget()
        self.sidebar_items = [
            "Home",
            "Point A to Point B Planning",
            "Delivery Route",
            "Multi-Delivery",
            "Security Route",
            "Linear Flight Route",
            "Tower Inspection"
        ]
        self.sidebar.addItems(self.sidebar_items)
        self.adjust_sidebar_width()
        self.sidebar.currentRowChanged.connect(self.switch_page)

        # Main Content Area (Right Frame)
        self.content_area = QStackedWidget()
        self.init_pages()

        # Add Widgets to Main Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        main_layout.setStretch(1, 4)

    def adjust_sidebar_width(self):
        font_metrics = QFontMetrics(self.sidebar.font())
        max_width = max(font_metrics.width(item) for item in self.sidebar_items)
        self.sidebar.setFixedWidth(max_width + 40)

    def init_pages(self):
        """
        Initialize all pages and add them to the stacked widget.
        """
        self.pages = {
            "home": OpeningPage(self.switch_page)
        }

        # External Pages
        try:
            self.pages["planning"] = MissionPlanner()
        except Exception as e:
            self.pages["planning"] = self.create_error_page("Mission Planner", str(e))
        try:
            self.pages["delivery"] = DeliveryRoute()
        except Exception as e:
            self.pages["delivery"] = self.create_error_page("Delivery Route", str(e))
        try:
            self.pages["multi_delivery"] = MultiDelivery()
        except Exception as e:
            self.pages["multi_delivery"] = self.create_error_page("Multi-Delivery", str(e))
        try:
            self.pages["security"] = SecurityRoute()
        except Exception as e:
            self.pages["security"] = self.create_error_page("Security Route", str(e))
        try:
            self.pages["linear_flight"] = LinearFlightRoute()
        except Exception as e:
            self.pages["linear_flight"] = self.create_error_page("Linear Flight Route", str(e))
        try:
            self.pages["inspection"] = TowerInspection()
        except Exception as e:
            self.pages["inspection"] = self.create_error_page("Tower Inspection", str(e))

        # Add Pages to Stacked Widget
        for page_name, page in self.pages.items():
            self.content_area.addWidget(page)

        # Default to Home Page
        self.switch_page(0)

    def create_error_page(self, title, error_message):
        error_page = QWidget()
        layout = QVBoxLayout(error_page)
        layout.addWidget(QLabel(f"{title} - Error Loading Page"))
        layout.addWidget(QLabel(f"Error: {error_message}"))
        return error_page

    def switch_page(self, index):
        """
        Switch the content in the right frame based on the selected sidebar item.
        """
        # Map the index to the page names
        page_mapping = [
            "home",               # Index 0
            "planning",           # Index 1
            "delivery",           # Index 2
            "multi_delivery",     # Index 3
            "security",           # Index 4
            "linear_flight",      # Index 5
            "inspection"          # Index 6
        ]
        # Ensure the index is valid before proceeding
        if 0 <= index < len(page_mapping):
            page_name = page_mapping[index]
            if page_name in self.pages:
                self.content_area.setCurrentWidget(self.pages[page_name])


# Main Entry Point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
