#!/bin/bash

echo "========================================"
echo "AutoFlight Generator - Snap Build Script"
echo "========================================"
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if running on Ubuntu/Debian
if ! command_exists snapcraft; then
    echo "ERROR: snapcraft is not installed"
    echo "Please install snapcraft with:"
    echo "  sudo snap install snapcraft --classic"
    echo "Or on Ubuntu 18.04+:"
    echo "  sudo apt install snapcraft"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "snapcraft.yaml" ]; then
    echo "ERROR: snapcraft.yaml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
snapcraft clean

# Build the snap
echo "Building snap package..."
echo "This may take several minutes..."
snapcraft

# Check if snap was built successfully
if [ -f *.snap ]; then
    SNAP_FILE=$(ls *.snap | head -n 1)
    echo
    echo "========================================"
    echo "Snap build completed successfully!"
    echo "========================================"
    echo
    echo "Snap package created: $SNAP_FILE"
    echo
    echo "To install the snap locally for testing:"
    echo "  sudo snap install --dangerous --devmode $SNAP_FILE"
    echo
    echo "To test the application:"
    echo "  autoflight-generator"
    echo
    echo "To publish to the Snap Store:"
    echo "1. Create a developer account at https://snapcraft.io"
    echo "2. Login: snapcraft login"
    echo "3. Upload: snapcraft upload $SNAP_FILE"
    echo "4. Release: snapcraft release <snap-name> <revision> <channel>"
    echo
    echo "For more information about publishing:"
    echo "  https://snapcraft.io/docs/releasing-your-app"
    echo
else
    echo
    echo "========================================"
    echo "Snap build failed!"
    echo "========================================"
    echo
    echo "Please check the error messages above and fix any issues."
    echo "Common issues:"
    echo "- Missing dependencies in snapcraft.yaml"
    echo "- Python package conflicts"
    echo "- Missing stage-packages"
    echo
    exit 1
fi
