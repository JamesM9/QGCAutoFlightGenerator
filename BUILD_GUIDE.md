# VERSATILE UAS Flight Generator - Build Guide

This guide provides comprehensive instructions for building the VERSATILE UAS Flight Generator application for Windows, macOS, and Ubuntu/Linux platforms.

## Prerequisites

### General Requirements
- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Platform-Specific Requirements

#### Windows
- Python 3.8+ (from python.org or Microsoft Store)
- Inno Setup 6.0+ (for creating installers) - Download from: https://jrsoftware.org/isinfo.php
- Visual Studio Build Tools (optional, for some dependencies)

#### macOS
- Python 3.8+ (from python.org or Homebrew)
- Homebrew (recommended for system dependencies) - Install from: https://brew.sh/
- Xcode Command Line Tools: `xcode-select --install`

#### Ubuntu/Linux
- Python 3.8+ and pip
- System build tools and libraries
- Qt5 development libraries

## Quick Start

### Windows Build
```batch
# Run the Windows build script
build_windows.bat
```

### macOS Build
```bash
# Make the script executable and run it
chmod +x build_macos.sh
./build_macos.sh
```

### Ubuntu/Linux Build
```bash
# Make the script executable and run it
chmod +x build_ubuntu.sh
./build_ubuntu.sh
```

## Detailed Build Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AutoFlightGenerator
```

### 2. Install Python Dependencies
```bash
# Install all required Python packages
pip install -r requirements.txt
```

### 3. Platform-Specific Builds

#### Windows Build Process

1. **Install Prerequisites**
   - Install Python 3.8+ from https://www.python.org/downloads/
   - Install Inno Setup from https://jrsoftware.org/isinfo.php
   - Ensure both are added to PATH

2. **Run Build Script**
   ```batch
   build_windows.bat
   ```

3. **Output Files**
   - `dist/UASFlightGenerator.exe` - Standalone executable
   - `installer/UASFlightGenerator_Setup.exe` - Windows installer

4. **Testing**
   - Test the executable: `dist\UASFlightGenerator.exe`
   - Test the installer: `installer\UASFlightGenerator_Setup.exe`

#### macOS Build Process

1. **Install Prerequisites**
   ```bash
   # Install Homebrew (if not already installed)
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install Python and system dependencies
   brew install python3
   brew install qt5
   brew install webkitgtk
   brew install gstreamer
   ```

2. **Run Build Script**
   ```bash
   chmod +x build_macos.sh
   ./build_macos.sh
   ```

3. **Output Files**
   - `dist/UASFlightGenerator` - Standalone executable
   - `dist/UASFlightGenerator.app` - macOS app bundle

4. **Installation Options**
   ```bash
   # Install system-wide
   sudo ./install_macos.sh
   
   # Create DMG installer (optional)
   brew install create-dmg
   ./create_dmg.sh
   ```

#### Ubuntu/Linux Build Process

1. **Install System Dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
       python3-dev \
       python3-pip \
       build-essential \
       libgl1-mesa-dev \
       libglib2.0-dev \
       libgirepository1.0-dev \
       libcairo2-dev \
       libpango1.0-dev \
       libatk1.0-dev \
       libgtk-3-dev \
       libwebkit2gtk-4.0-dev \
       libgstreamer1.0-dev \
       libgstreamer-plugins-base1.0-dev \
       gstreamer1.0-plugins-base \
       gstreamer1.0-plugins-good \
       gstreamer1.0-plugins-bad \
       gstreamer1.0-plugins-ugly \
       gstreamer1.0-libav
   ```

2. **Run Build Script**
   ```bash
   chmod +x build_ubuntu.sh
   ./build_ubuntu.sh
   ```

3. **Output Files**
   - `dist/UASFlightGenerator` - Standalone executable
   - `UASFlightGenerator.desktop` - Desktop shortcut file

4. **Installation**
   ```bash
   # Install desktop shortcut for current user
   cp UASFlightGenerator.desktop ~/.local/share/applications/
   
   # Or install system-wide
   sudo cp UASFlightGenerator.desktop /usr/share/applications/
   ```

## Manual Build Process

If the automated scripts don't work, you can build manually:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Build with PyInstaller
```bash
# Windows
pyinstaller --clean AutoFlightGenerator.spec

# macOS
pyinstaller --clean UASFlightGenerator_macos.spec

# Linux
pyinstaller --clean UASFlightGenerator_linux.spec
```

### 3. Create Installer (Windows)
```batch
iscc AutoFlightGenerator_Setup.iss
```

## Troubleshooting

### Common Issues

#### PyQt5/PyQtWebEngine Issues
- **Windows**: Install Visual Studio Build Tools
- **macOS**: Use Homebrew to install Qt5: `brew install qt5`
- **Linux**: Install Qt5 development packages

#### Missing Dependencies
```bash
# Install missing packages individually
pip install PyQt5==5.15.7
pip install PyQtWebEngine==5.15.7
pip install shapely==2.0.1
pip install numpy==1.24.3
pip install matplotlib==3.7.2
```

#### Build Failures
1. Clean previous builds: `rm -rf build dist *.spec`
2. Upgrade pip: `pip install --upgrade pip`
3. Reinstall PyInstaller: `pip install --force-reinstall pyinstaller==5.13.0`

#### Runtime Issues
- Ensure all HTML files are included in the build
- Check that all Python modules are properly imported
- Verify system dependencies are installed

### Platform-Specific Issues

#### Windows
- **Antivirus blocking**: Add build directory to exclusions
- **Path issues**: Ensure Python and Inno Setup are in PATH
- **Permission issues**: Run as Administrator if needed

#### macOS
- **Gatekeeper**: Right-click app and select "Open" for first run
- **Code signing**: For distribution, sign the app with Apple Developer certificate
- **Homebrew issues**: Update Homebrew: `brew update && brew upgrade`

#### Linux
- **Library issues**: Install missing libraries with `apt-get`
- **Permission issues**: Ensure executable permissions: `chmod +x dist/UASFlightGenerator`
- **Desktop integration**: Check desktop file syntax and permissions

## Distribution

### Windows
- Distribute `installer/UASFlightGenerator_Setup.exe`
- Users can run the installer to install the application

### macOS
- Distribute `dist/UASFlightGenerator.app` or `UASFlightGenerator_Setup.dmg`
- Users can drag the app to Applications folder or run the DMG

### Linux
- Distribute `dist/UASFlightGenerator` executable
- Include `UASFlightGenerator.desktop` for desktop integration
- Consider creating a .deb package for Ubuntu/Debian systems

## Development Build

For development and testing:
```bash
# Run directly with Python
python dashboard.py

# Or run individual tools
python securityroute.py
python mapping_flight.py
python structure_scan.py
```

## Build Configuration Files

- `AutoFlightGenerator.spec` - PyInstaller spec for Windows
- `UASFlightGenerator_macos.spec` - PyInstaller spec for macOS
- `UASFlightGenerator_linux.spec` - PyInstaller spec for Linux
- `AutoFlightGenerator_Setup.iss` - Inno Setup script for Windows installer
- `requirements.txt` - Python dependencies

## Support

If you encounter build issues:
1. Check the troubleshooting section above
2. Ensure all prerequisites are installed
3. Try the manual build process
4. Check the PyInstaller documentation: https://pyinstaller.org/
5. Verify system-specific requirements for your platform
