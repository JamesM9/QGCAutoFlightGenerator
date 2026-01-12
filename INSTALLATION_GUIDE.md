# AutoFlightGenerator - Professional Windows Installer

## Overview

AutoFlightGenerator is a comprehensive UAV flight planning application that provides multiple mission planning tools including point-to-point navigation, delivery routes, security inspections, and more.

## System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Architecture**: 64-bit (x64)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: Minimum 2GB free space
- **Internet Connection**: Required for initial installation and Google Maps functionality
- **Administrator Rights**: Required for installation

## New Features in v1.1.0

### Aircraft Parameters System
- **Import ArduPilot/PX4 Parameters**: Load real parameter files from your aircraft
- **Automatic Optimization**: Flight plans automatically optimized for your specific aircraft
- **Global Control**: Enable/disable parameters from the main dashboard
- **Smart Integration**: All mission tools automatically apply aircraft parameters
- **Safety Compliance**: Ensures missions stay within aircraft certified limits

### Enhanced Mission Planning
- **Terrain Proximity Monitoring**: Automatic detection of waypoints too close to terrain
- **Altitude Profile Visualization**: Comprehensive elevation data and safety statistics
- **Improved Safety Monitoring**: Real-time safety alerts and terrain clearance verification
- **Enhanced User Interface**: Better logo display and improved visual design

## Installation Options

### Option 1: Professional Installer (Recommended)

1. **Download the installer files**:
   - `Install_AutoFlightGenerator.bat` - Main installer launcher
   - `AutoFlightGenerator_Setup.ps1` - PowerShell installer script
   - `AutoFlightGenerator_Setup.exe` - Alternative batch installer

2. **Run as Administrator**:
   - Right-click on `Install_AutoFlightGenerator.bat`
   - Select "Run as Administrator"
   - Follow the on-screen instructions

3. **What the installer does**:
   - Checks system requirements
   - Installs Python 3.11 (if not present)
   - Creates virtual environment
   - Installs all Python dependencies
   - Creates desktop and Start Menu shortcuts
   - Sets up registry entries for uninstallation
   - Tests the installation

### Option 2: Manual Installation

If the automatic installer fails, you can install manually:

1. **Install Python 3.11**:
   - Download from https://www.python.org/downloads/
   - Ensure "Add Python to PATH" is checked
   - Install for all users

2. **Install Microsoft Visual C++ Build Tools** (if needed):
   - Download from https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install with "C++ build tools" workload

3. **Create virtual environment**:
   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   ```

4. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```

## Dependencies Installed

The installer automatically installs these Python packages:

### Core Dependencies
- **requests==2.28.1** - HTTP library for API calls
- **numpy==1.23.1** - Numerical computing
- **matplotlib==3.5.2** - Plotting and visualization

### GUI Framework
- **PyQt5==5.15.7** - Main GUI framework
- **PyQtWebEngine==5.15.7** - Web browser component for maps

### Geospatial Libraries
- **shapely==1.8.2** - Geometric operations
- **pyproj==3.3.1** - Coordinate transformations
- **geopy==2.2.0** - Geocoding and distance calculations

### Build Tools
- **pyinstaller** - For creating standalone executables

## Installation Directory

The application is installed to:
```
C:\Program Files\AutoFlightGenerator\
```

## Files Created

### Application Files
- All Python source files (`.py`)
- HTML files (`.html`)
- PyInstaller spec files (`.spec`)

### Launcher Scripts
- `run_autoflight.bat` - Main application launcher
- `uninstall.bat` - Uninstaller script

### Shortcuts
- Desktop shortcut: `%USERPROFILE%\Desktop\AutoFlightGenerator.bat`
- Start Menu shortcut: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\AutoFlightGenerator\AutoFlightGenerator.bat`

### Documentation
- `README.txt` - Installation and usage instructions

## Running the Application

### Method 1: Desktop Shortcut
- Double-click the `AutoFlightGenerator` shortcut on your desktop

### Method 2: Start Menu
- Click Start Menu → Programs → AutoFlightGenerator → AutoFlightGenerator

### Method 3: Direct Execution
- Open Command Prompt as Administrator
- Navigate to installation directory: `cd "C:\Program Files\AutoFlightGenerator"`
- Run: `run_autoflight.bat`

## Post-Installation Setup

### Google Maps API Key (Required)

1. **Get an API key**:
   - Go to https://console.cloud.google.com
   - Create a new project or select existing
   - Enable Maps JavaScript API
   - Create credentials (API key)

2. **Configure the application**:
   - Open `map.html` in the installation directory
   - Replace `YOUR_GOOGLE_MAPS_API_KEY` with your actual API key
   - Save the file

### Aircraft Parameters Setup (Optional but Recommended)

The Aircraft Parameters System allows you to import real ArduPilot or PX4 parameter files from your aircraft and automatically optimize all flight plans for your specific aircraft's capabilities.

1. **Import Parameter Files**:
   - Connect to your aircraft with Mission Planner, QGroundControl, or similar
   - Export your current parameter file (.param, .params, or .txt format)
   - In the dashboard, click "Import Parameter File" in the Aircraft Parameters section

2. **Create Aircraft Configuration**:
   - Click "Manage" in the Aircraft Parameters section
   - Click "New Configuration" to create a new aircraft profile
   - Give your configuration a descriptive name (e.g., "DJI Phantom 4 Pro")
   - Select the imported parameter file and save

3. **Enable Parameters Globally**:
   - Check "Enable Aircraft Parameters" in the dashboard
   - Select your aircraft configuration from the dropdown
   - All mission tools will now automatically use these parameters

4. **Benefits**:
   - Flight plans automatically optimized for your specific aircraft
   - Altitude, speed, and waypoint settings tailored to your aircraft's capabilities
   - Enhanced safety through firmware compliance
   - No need to configure parameters in each individual tool

### Testing the Installation

After installation, the application should:
- Start without errors
- Display the main GUI
- Show Google Maps in the map view (if API key is configured)
- Allow access to all planning tools

## Application Features

### Mission Planning Tools
1. **Point A to Point B Planning** - Basic navigation between two points
2. **Delivery Route** - Single delivery mission planning
3. **Multi-Delivery** - Multiple delivery locations in one mission
4. **Security Route** - Perimeter and random security patrols
5. **Linear Flight Route** - Path following missions
6. **Tower Inspection** - Infrastructure inspection missions

### Key Features
- **Interactive Maps** - Google Maps integration
- **Terrain Elevation** - Automatic elevation data from OpenTopography API
- **Multiple Aircraft Types** - Support for multicopter, fixed-wing, and VTOL
- **Export to QGroundControl** - Generate `.plan` files for mission execution
- **Geofence Generation** - Automatic safety boundary creation
- **Altitude Planning** - Terrain-aware altitude calculations

## Troubleshooting

### Common Issues

#### 1. "Python not found" Error
- Ensure Python 3.11 is installed
- Check that Python is added to PATH
- Try running the installer as Administrator

#### 2. "Microsoft Visual C++ 14.0 required" Error
- Install Microsoft Visual C++ Build Tools
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Select "C++ build tools" workload

#### 3. "PyQtWebEngine import error"
- The installer should handle this automatically
- If it fails, try: `pip install PyQtWebEngine==5.15.7`

#### 4. "Shapely DLL error"
- This is usually resolved by the installer
- If it persists, try: `pip install shapely==1.8.2`

#### 5. "Google Maps not loading"
- Ensure you have a valid Google Maps API key
- Check that the API key is enabled for Maps JavaScript API
- Verify the key is correctly placed in `map.html`

### Getting Help

If you encounter issues:

1. **Check the console output** for error messages
2. **Verify all dependencies** are installed correctly
3. **Ensure you have administrator rights**
4. **Check your internet connection**
5. **Verify Google Maps API key** is configured

## Uninstalling

### Method 1: Using the Uninstaller
- Run: `C:\Program Files\AutoFlightGenerator\uninstall.bat`
- Confirm the uninstallation when prompted

### Method 2: Windows Programs and Features
- Open Control Panel → Programs and Features
- Find "AutoFlightGenerator" in the list
- Click "Uninstall"

### Method 3: Manual Removal
- Delete the installation directory: `C:\Program Files\AutoFlightGenerator`
- Remove desktop shortcut: `%USERPROFILE%\Desktop\AutoFlightGenerator.bat`
- Remove Start Menu folder: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\AutoFlightGenerator`

## Support

For technical support or bug reports:
- Check the console output for error messages
- Ensure all system requirements are met
- Verify Google Maps API key configuration
- Test with a fresh installation if needed

## License

This software is provided as-is for educational and research purposes. Please ensure compliance with local regulations when using for actual flight operations.

---

**Note**: This installer creates a professional installation similar to commercial software, with proper shortcuts, registry entries, and uninstall capabilities. The application is ready to use immediately after installation (with Google Maps API key configuration). 