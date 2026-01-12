# AutoFlightGenerator

Professional UAV Mission Planning Application for QGroundControl and MAVLink-compatible ground control stations.

## Overview

AutoFlightGenerator is a comprehensive mission planning tool that generates flight plan files (`.plan` format) compatible with QGroundControl and other MAVLink-based ground control stations. It features an intuitive GUI built with PyQt5 and includes advanced terrain following, aircraft parameter integration, and multiple mission types.

## Features

### Core Functionality
- **Interactive Map**: Click-to-set coordinates with real-time elevation data
- **Multiple Mission Types**: Delivery routes, multi-delivery, security routes, linear flights, tower inspections, and A-to-B missions
- **Terrain Following**: Automatic elevation data integration from OpenTopography API
- **QGroundControl Export**: Generate `.plan` files directly importable into QGC
- **Aircraft Parameters**: Import and apply ArduPilot/PX4 parameters for optimized flight planning
- **Mission Library**: Save, load, and manage mission plans
- **Altitude Visualization**: Generate detailed flight altitude profiles

### User Interface
- **Modern Dark Theme**: QGroundControl-inspired professional appearance
- **Responsive Layout**: Adapts to different screen sizes
- **Real-time Status**: Progress tracking and notifications
- **Video Tutorials**: Integrated instructional videos for all tools
- **Settings Management**: Global preferences for units (Metric/Imperial) and defaults

## Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 or macOS

### Option 1: Using the Installer (Recommended)

**Windows:**
1. Download `AutoFlightGenerator_Setup.exe` from the [Releases](../../releases) page
2. Run the installer and follow the setup wizard
3. Launch AutoFlightGenerator from the Start Menu or Desktop shortcut

**macOS:**
1. Download `AutoFlightGenerator.app` from the [Releases](../../releases) page
2. Extract the application bundle
3. Move to Applications folder
4. Double-click to launch (may need to allow in System Preferences)

### Option 2: From Source

1. Clone the repository:
```bash
git clone https://github.com/JamesM9/QGCAutoFlightGenerator.git
cd QGCAutoFlightGenerator
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
   - **Windows**: `venv\Scripts\activate`
   - **macOS/Linux**: `source venv/bin/activate`

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the application:
```bash
python dashboard.py
```

## Mission Types

- **Delivery Route**: Single delivery missions with precise waypoints and landing sequences
- **Multi-Delivery**: Complex multi-point delivery routes with multiple landing zones
- **Security Route**: Security patrol missions with geofencing and loiter capabilities
- **Linear Flight**: Linear inspection and survey routes
- **Tower Inspection**: Tower and infrastructure inspection missions
- **A-to-B Mission**: Simple point-to-point mission planning

## Building from Source

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for detailed build instructions.

### Quick Build Commands

**Windows:**
```batch
build_windows.bat
```

**macOS:**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

## Documentation

- [AIRCRAFT_PARAMETERS_GUIDE.md](AIRCRAFT_PARAMETERS_GUIDE.md): Comprehensive guide to the aircraft parameters system
- [VIDEO_TUTORIAL_SYSTEM.md](VIDEO_TUTORIAL_SYSTEM.md): Video tutorial system documentation
- [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md): Detailed installation and setup instructions
- [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md): Build and packaging guide
- [BUILD_WITH_INNOSETUP.md](BUILD_WITH_INNOSETUP.md): Windows installer creation guide
- [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md): General packaging information

## Requirements

See [requirements.txt](requirements.txt) for the complete list of Python dependencies.

Key dependencies include:
- PyQt5
- geopy
- requests
- shapely
- numpy
- matplotlib

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or feature requests, please open an issue on the [GitHub Issues](../../issues) page.

## Acknowledgments

- Built for compatibility with QGroundControl
- Uses OpenTopography API for terrain elevation data
- Inspired by professional UAV mission planning workflows
