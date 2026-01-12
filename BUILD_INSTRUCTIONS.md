# AutoFlightGenerator - Build Instructions

## Quick Start

### Windows 10/11

1. **Open Command Prompt or PowerShell in the project directory**

2. **Run the build script:**
   ```batch
   build_windows.bat
   ```

3. **Find your executable:**
   - `dist\AutoFlightGenerator.exe` - Standalone executable
   - `installer\AutoFlightGenerator_Setup.exe` - Windows installer (if Inno Setup is installed)

### macOS

1. **Open Terminal in the project directory**

2. **Make build script executable (if needed):**
   ```bash
   chmod +x build_macos.sh
   ```

3. **Run the build script:**
   ```bash
   ./build_macos.sh
   ```

4. **Find your application:**
   - `dist/AutoFlightGenerator.app` - macOS App Bundle
   - Run `./install_macos.sh` to install system-wide

## Prerequisites

### Windows
- Python 3.8 or higher
- All packages from `requirements.txt` installed
- PyInstaller 6.15.0+ (installed automatically by build script)
- (Optional) Inno Setup for creating installer

### macOS
- Python 3.8 or higher
- All packages from `requirements.txt` installed
- PyInstaller 6.15.0+ (installed automatically by build script)
- (Optional) Homebrew for system dependencies
- (Optional) create-dmg for creating DMG installer

## Installation Steps

### Step 1: Install Dependencies

**Windows:**
```batch
pip install -r requirements.txt
pip install pyinstaller>=6.15.0
```

**macOS:**
```bash
pip3 install -r requirements.txt
pip3 install pyinstaller>=6.15.0
```

### Step 2: Run Build Script

**Windows:**
```batch
build_windows.bat
```

**macOS:**
```bash
chmod +x build_macos.sh
./build_macos.sh
```

### Step 3: Test the Executable

**Windows:**
```batch
dist\AutoFlightGenerator.exe
```

**macOS:**
```bash
open dist/AutoFlightGenerator.app
# or
./dist/AutoFlightGenerator
```

## Manual Build (Alternative)

If the build scripts don't work, you can build manually:

### Windows
```batch
pyinstaller AutoFlightGenerator.spec
```

### macOS
```bash
pyinstaller AutoFlightGenerator.spec
```

## What Gets Included

The executable includes:
- All Python code and dependencies
- All HTML map files
- Images and assets
- Configuration files
- Aircraft parameter files
- PyQt5 and QtWebEngine runtime libraries

## File Sizes

Expected sizes:
- Windows: ~150-200 MB
- macOS: ~150-200 MB

The executable is self-contained - no Python installation required on target machines.

## Troubleshooting

See `PACKAGING_GUIDE.md` for detailed troubleshooting information.

## Distribution

### Windows
- Distribute `AutoFlightGenerator.exe` (standalone)
- Or create installer using Inno Setup script

### macOS
- Distribute `AutoFlightGenerator.app` (app bundle)
- Or create DMG using `create_dmg.sh` script
