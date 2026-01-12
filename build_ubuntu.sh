#!/bin/bash

echo "========================================"
echo "VERSATILE UAS Flight Generator - Ubuntu/Linux Build Script"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running on Ubuntu/Debian
if ! command_exists apt-get; then
    echo "WARNING: This script is optimized for Ubuntu/Debian systems"
    echo "You may need to install dependencies manually on other distributions"
fi

# Check if Python is installed
if ! command_exists python3; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3: sudo apt-get install python3 python3-pip"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $python_version"

# Install system dependencies
echo "Installing system dependencies..."
if command_exists apt-get; then
    sudo apt-get update
    sudo apt-get install -y \
        python3-dev \
        python3-pip \
        python3-venv \
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
        libgstreamer-plugins-bad1.0-dev \
        gstreamer1.0-plugins-base \
        gstreamer1.0-plugins-good \
        gstreamer1.0-plugins-bad \
        gstreamer1.0-plugins-ugly \
        gstreamer1.0-libav \
        gstreamer1.0-tools \
        gstreamer1.0-x \
        gstreamer1.0-alsa \
        gstreamer1.0-gl \
        gstreamer1.0-gtk3 \
        gstreamer1.0-qt5 \
        gstreamer1.0-pulseaudio
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
if [ ! -f "dist/UASFlightGenerator" ]; then
    echo "ERROR: Executable not found in dist folder"
    echo "Build may have failed or executable was not created"
    exit 1
fi

# Make executable executable
chmod +x dist/UASFlightGenerator

echo
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo
echo "Files created:"
echo "- Executable: dist/UASFlightGenerator"
echo
echo "To test the application:"
echo "1. Run: ./dist/UASFlightGenerator"
echo
echo "To create a desktop shortcut:"
echo "1. Create a .desktop file in ~/.local/share/applications/"
echo "2. Add the following content:"
echo "   [Desktop Entry]"
echo "   Name=VERSATILE UAS Flight Generator"
echo "   Exec=/path/to/dist/UASFlightGenerator"
echo "   Icon=/path/to/icon.png"
echo "   Type=Application"
echo "   Categories=Utility;"
echo

# Create a simple desktop file
echo "Creating desktop file..."
cat > UASFlightGenerator.desktop << EOF
[Desktop Entry]
Name=VERSATILE UAS Flight Generator
Comment=VERSATILE UAS Flight Planning and Mission Generation Tool
Exec=$(pwd)/dist/UASFlightGenerator
Icon=$(pwd)/Images/icon.png
Terminal=false
Type=Application
Categories=Utility;Science;Education;
Version=2.0.0
EOF

echo "Desktop file created: UASFlightGenerator.desktop"
echo "To install it system-wide, run:"
echo "sudo cp UASFlightGenerator.desktop /usr/share/applications/"
echo "Or copy it to ~/.local/share/applications/ for current user only"
echo
