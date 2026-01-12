# VERSATILE UAS Flight Generator - Build Guide v2.1.0

## Overview

This guide provides comprehensive instructions for building the VERSATILE UAS Flight Generator for Windows, macOS, and Linux platforms. The software now includes advanced aircraft parameter integration, enhanced tutorial system, and improved terrain following capabilities.

## Prerequisites

### System Requirements
- **Python 3.8+** (recommended: Python 3.10+)
- **Git** (for cloning the repository)
- **Internet connection** (for downloading dependencies)

### Platform-Specific Requirements

#### Windows
- **Inno Setup 6.0+** (for creating Windows installer)
- **Visual Studio Build Tools** (optional, for some Python packages)

#### macOS
- **Xcode Command Line Tools** (`xcode-select --install`)
- **Homebrew** (recommended for dependency management)
- **create-dmg** (optional, for DMG creation: `brew install create-dmg`)

#### Linux (Ubuntu/Debian)
- **snapcraft** (for Snap package creation: `sudo snap install snapcraft --classic`)
- **Build essentials** (automatically installed by build scripts)

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AutoFlightGenerator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Build for Your Platform

#### Windows
```cmd
build_windows.bat
```

#### macOS
```bash
chmod +x build_macos.sh
./build_macos.sh
```

#### Linux (Ubuntu/Debian)
```bash
chmod +x build_ubuntu.sh
./build_ubuntu.sh
```

#### Linux (Snap Package)
```bash
chmod +x build_snap.sh
./build_snap.sh
```

## Detailed Build Instructions

### Windows Build Process

#### Step 1: Prepare Environment
1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
2. Install Inno Setup from [jrsoftware.org](https://jrsoftware.org/isinfo.php)
3. Ensure both are added to your system PATH

#### Step 2: Run Build Script
```cmd
build_windows.bat
```

The script will:
- Check Python installation
- Install/upgrade pip
- Install PyInstaller and dependencies
- Build the executable using `AutoFlightGenerator.spec`
- Create Windows installer using `AutoFlightGenerator_Setup.iss`

#### Step 3: Output Files
- **Executable**: `dist/UASFlightGenerator.exe`
- **Installer**: `installer/UASFlightGenerator_Setup.exe`

### macOS Build Process

#### Step 1: Prepare Environment
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install qt5 webkitgtk gstreamer
```

#### Step 2: Run Build Script
```bash
chmod +x build_macos.sh
./build_macos.sh
```

#### Step 3: Create DMG (Optional)
```bash
# Install create-dmg tool
brew install create-dmg

# Create DMG installer
./create_dmg.sh
```

#### Step 4: Output Files
- **Executable**: `dist/UASFlightGenerator`
- **App Bundle**: `dist/UASFlightGenerator.app`
- **DMG**: `UASFlightGenerator_Setup.dmg` (if created)

### Linux Build Process

#### Ubuntu/Debian (Standalone Executable)
```bash
chmod +x build_ubuntu.sh
./build_ubuntu.sh
```

#### Snap Package (Recommended for Distribution)
```bash
chmod +x build_snap.sh
./build_snap.sh
```

#### Output Files
- **Executable**: `dist/UASFlightGenerator`
- **Snap Package**: `autoflight-generator_2.1.0_amd64.snap`

## Build Configuration Files

### PyInstaller Spec File (`AutoFlightGenerator.spec`)
- **Purpose**: Defines how PyInstaller builds the executable
- **Key Features**:
  - Includes all aircraft parameters modules
  - Bundles HTML files and images
  - Handles PyQt5 and PyQtWebEngine dependencies
  - Creates single-file executable

### InnoSetup Script (`AutoFlightGenerator_Setup.iss`)
- **Purpose**: Creates Windows installer
- **Key Features**:
  - Professional installer with modern UI
  - Includes all source files for reference
  - Creates desktop shortcuts
  - Registry integration for uninstall

### Snapcraft Configuration (`snapcraft.yaml`)
- **Purpose**: Creates Linux Snap package
- **Key Features**:
  - Strict confinement for security
  - Includes all Qt5 dependencies
  - Desktop integration
  - Automatic updates via Snap Store

## New Features in v2.1.0

### Aircraft Parameters System
- **Individual Tool Integration**: Each mission tool has its own parameter UI
- **ArduPilot & PX4 Support**: Full parameter file parsing and analysis
- **Smart Detection**: Automatic aircraft type detection from parameters
- **Performance Optimization**: Mission generation based on aircraft capabilities

### Enhanced Tutorial System
- **Comprehensive Coverage**: Tutorials for all tools and features
- **Latest Features Section**: Dedicated tutorial for new capabilities
- **Step-by-Step Guides**: Detailed instructions for all functionality
- **Troubleshooting**: Common issues and solutions

### Improved Map Integration
- **Google Satellite Default**: All tools default to satellite view
- **Enhanced Terrain Following**: Improved elevation queries with confirmation
- **Better Performance**: Non-blocking UI with progress updates

### Auto-Save Functionality
- **Security Route Tool**: Automatic save prompts after mission generation
- **User Choice**: Save to location of user's choosing
- **Seamless Integration**: Works with existing export functionality

## Troubleshooting

### Common Build Issues

#### Python Dependencies
```bash
# If pip install fails, try upgrading pip first
python -m pip install --upgrade pip

# Install packages individually if batch install fails
pip install requests PyQt5 PyQtWebEngine shapely numpy matplotlib pyinstaller
```

#### PyInstaller Issues
```bash
# Clean previous builds
rm -rf build dist

# Rebuild with verbose output
pyinstaller --log-level=DEBUG AutoFlightGenerator.spec
```

#### Qt/WebEngine Issues
- **Windows**: Ensure Visual C++ Redistributables are installed
- **macOS**: Install Xcode Command Line Tools
- **Linux**: Install Qt5 development packages

### Platform-Specific Issues

#### Windows
- **Antivirus False Positives**: Add build directory to exclusions
- **Path Issues**: Ensure Python and Inno Setup are in PATH
- **Permission Issues**: Run as Administrator if needed

#### macOS
- **Code Signing**: Required for distribution outside App Store
- **Gatekeeper**: May block unsigned applications
- **Dependencies**: Use Homebrew for consistent package management

#### Linux
- **Snap Confinement**: Some features may require additional permissions
- **Desktop Integration**: Ensure desktop environment supports .desktop files
- **Dependencies**: Use package manager for system dependencies

## Distribution

### Windows
- **Installer**: Use `installer/UASFlightGenerator_Setup.exe`
- **Portable**: Use `dist/UASFlightGenerator.exe` directly
- **Digital Signing**: Recommended for professional distribution

### macOS
- **App Store**: Requires Apple Developer account and code signing
- **Direct Distribution**: Use DMG file or App Bundle
- **Notarization**: Required for macOS 10.15+ distribution

### Linux
- **Snap Store**: Upload to official Snap Store for wide distribution
- **Direct Distribution**: Use standalone executable
- **Package Repositories**: Create .deb/.rpm packages for specific distributions

## Development Builds

### Testing Changes
```bash
# Run directly from source (no build required)
python dashboard.py

# Test specific tools
python deliveryroute.py
python securityroute.py
```

### Debug Builds
```bash
# Build with debug information
pyinstaller --debug=all AutoFlightGenerator.spec

# Run with console output
pyinstaller --console AutoFlightGenerator.spec
```

## Version History

### v2.1.0 (Current)
- Aircraft parameter integration system
- Enhanced tutorial system
- Improved terrain following
- Google Satellite map defaults
- Auto-save functionality
- Individual tool parameter control

### v2.0.0
- Multi-platform build system
- Enhanced UI and theming
- Improved mission generation
- Better error handling

## Support

For build issues or questions:
1. Check this guide for common solutions
2. Review error messages carefully
3. Ensure all prerequisites are installed
4. Try clean rebuilds if issues persist

## Contributing

To contribute to the build system:
1. Test builds on your target platform
2. Update documentation for any changes
3. Ensure backward compatibility
4. Test with clean environments
