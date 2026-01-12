#!/bin/bash

echo "========================================"
echo "VERSATILE UAS Flight Generator - macOS Build Script"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python3; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    echo "Or use Homebrew: brew install python3"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $python_version"

# Check if Homebrew is installed (recommended for macOS)
if command_exists brew; then
    echo "Homebrew detected. Installing system dependencies..."
    brew install qt5
    brew install webkitgtk
    brew install gstreamer
    brew install gst-plugins-base
    brew install gst-plugins-good
    brew install gst-plugins-bad
    brew install gst-plugins-ugly
    brew install gst-libav
else
    echo "WARNING: Homebrew not detected. You may need to install Qt5 and other dependencies manually."
    echo "Install Homebrew from: https://brew.sh/"
fi

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller==5.13.0
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyInstaller"
        exit 1
    fi
fi

# Check if required packages are installed
echo "Checking dependencies..."
if ! python3 -c "import PyQt5, PyQtWebEngine, requests, shapely, numpy, matplotlib" >/dev/null 2>&1; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install required packages"
        echo "Trying to install packages individually..."
        
        pip3 install requests==2.28.1
        pip3 install PyQt5==5.15.7
        pip3 install PyQtWebEngine==5.15.7
        pip3 install shapely==2.0.1
        pip3 install numpy==1.24.3
        pip3 install matplotlib==3.7.2
        
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to install packages individually"
            exit 1
        fi
    fi
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
# Don't delete spec files as they are needed for the build

# Build with PyInstaller using the spec file
echo "Building application with PyInstaller..."
pyinstaller AutoFlightGenerator.spec
if [ $? -ne 0 ]; then
    echo "ERROR: PyInstaller build failed"
    echo "Check the error messages above for details"
    exit 1
fi

# Check if executable was created
if [ ! -f "dist/AutoFlightGenerator" ] && [ ! -d "dist/AutoFlightGenerator.app" ]; then
    echo "ERROR: Executable not found in dist folder"
    echo "Build may have failed or executable was not created"
    exit 1
fi

# Make executable executable
if [ -f "dist/AutoFlightGenerator" ]; then
    chmod +x dist/AutoFlightGenerator
fi

echo
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo
echo "Files created:"
if [ -f "dist/AutoFlightGenerator" ]; then
    echo "- Executable: dist/AutoFlightGenerator"
fi
if [ -d "dist/AutoFlightGenerator.app" ]; then
    echo "- App Bundle: dist/AutoFlightGenerator.app"
fi
echo
echo "To test the application:"
if [ -f "dist/AutoFlightGenerator" ]; then
    echo "1. Run: ./dist/AutoFlightGenerator"
fi
if [ -d "dist/AutoFlightGenerator.app" ]; then
    echo "2. Or double-click: dist/AutoFlightGenerator.app"
    echo "3. Or run: open dist/AutoFlightGenerator.app"
fi
echo

# Create a simple installer script
echo "Creating installer script..."
cat > install_macos.sh << 'EOF'
#!/bin/bash

echo "Installing VERSATILE UAS Flight Generator..."

# Check if app bundle exists
if [ ! -d "dist/AutoFlightGenerator.app" ]; then
    echo "ERROR: App bundle not found. Please run build_macos.sh first."
    exit 1
fi

# Copy to Applications folder
echo "Copying to Applications folder..."
cp -R dist/AutoFlightGenerator.app /Applications/

# Set permissions
chmod +x /Applications/AutoFlightGenerator.app/Contents/MacOS/AutoFlightGenerator

echo "Installation completed!"
echo "You can now find VERSATILE UAS Flight Generator in your Applications folder."
echo "You can also launch it from Spotlight or the Applications folder."
EOF

chmod +x install_macos.sh

echo "Installer script created: install_macos.sh"
echo "To install the application system-wide, run:"
echo "sudo ./install_macos.sh"
echo

# Create DMG creation script (optional)
echo "Creating DMG creation script..."
cat > create_dmg.sh << 'EOF'
#!/bin/bash

# This script creates a DMG installer (requires create-dmg tool)
# Install create-dmg: brew install create-dmg

if ! command -v create-dmg >/dev/null 2>&1; then
    echo "ERROR: create-dmg not found. Install it with: brew install create-dmg"
    exit 1
fi

if [ ! -d "dist/AutoFlightGenerator.app" ]; then
    echo "ERROR: App bundle not found. Please run build_macos.sh first."
    exit 1
fi

echo "Creating DMG installer..."
create-dmg \
    --volname "VERSATILE UAS Flight Generator" \
    --volicon "Images/icon.icns" \
    --window-pos 200 120 \
    --window-size 600 300 \
    --icon-size 100 \
    --icon "AutoFlightGenerator.app" 175 120 \
    --hide-extension "AutoFlightGenerator.app" \
    --app-drop-link 425 120 \
    "AutoFlightGenerator_Setup.dmg" \
    "dist/"

echo "DMG created: AutoFlightGenerator_Setup.dmg"
EOF

chmod +x create_dmg.sh

echo "DMG creation script created: create_dmg.sh"
echo "To create a DMG installer, run:"
echo "brew install create-dmg  # Install the tool first"
echo "./create_dmg.sh"
echo
