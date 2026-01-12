# Packaging Guide for AutoFlightGenerator

This guide explains how to package AutoFlightGenerator as a standalone executable for Windows 10/11 and macOS.

## Prerequisites

### Windows
- Python 3.8+ installed
- pip (comes with Python)
- PyInstaller 6.15.0+
- All dependencies from `requirements.txt`

### macOS
- Python 3.8+ installed
- pip3 (comes with Python)
- PyInstaller 6.15.0+
- Homebrew (recommended for dependencies)
- All dependencies from `requirements.txt`

## Quick Start

### Windows

1. **Install dependencies:**
   ```batch
   pip install -r requirements.txt
   pip install pyinstaller>=6.15.0
   ```

2. **Build the executable:**
   ```batch
   build_windows.bat
   ```

3. **Find your executable:**
   - Standalone: `dist\AutoFlightGenerator.exe`
   - Installer (if Inno Setup is installed): `installer\AutoFlightGenerator_Setup.exe`

### macOS

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   pip3 install pyinstaller>=6.15.0
   ```

2. **Build the application:**
   ```bash
   chmod +x build_macos.sh
   ./build_macos.sh
   ```

3. **Find your application:**
   - App Bundle: `dist/AutoFlightGenerator.app`
   - Installer script: `install_macos.sh`

## Manual Build Process

### Windows Manual Build

1. **Clean previous builds:**
   ```batch
   rmdir /s /q build dist
   ```

2. **Build with PyInstaller:**
   ```batch
   pyinstaller AutoFlightGenerator.spec
   ```

3. **Test the executable:**
   ```batch
   dist\AutoFlightGenerator.exe
   ```

### macOS Manual Build

1. **Clean previous builds:**
   ```bash
   rm -rf build dist
   ```

2. **Build with PyInstaller:**
   ```bash
   pyinstaller AutoFlightGenerator.spec
   ```

3. **Test the application:**
   ```bash
   open dist/AutoFlightGenerator.app
   # or
   ./dist/AutoFlightGenerator
   ```

## Creating Installers

### Windows Installer (Inno Setup)

1. Install [Inno Setup](https://jrsoftware.org/isinfo.php)

2. Run the installer build (automatically done by `build_windows.bat`):
   ```batch
   iscc AutoFlightGenerator_Setup.iss
   ```

3. Find installer: `installer\AutoFlightGenerator_Setup.exe`

### macOS DMG Installer

1. Install create-dmg tool:
   ```bash
   brew install create-dmg
   ```

2. Create DMG:
   ```bash
   chmod +x create_dmg.sh
   ./create_dmg.sh
   ```

3. Find DMG: `AutoFlightGenerator_Setup.dmg`

## Troubleshooting

### Common Issues

#### Windows

1. **"Python is not installed or not in PATH"**
   - Solution: Add Python to your system PATH or use full path to python.exe

2. **"PyInstaller not found"**
   - Solution: `pip install pyinstaller`

3. **"Missing modules"**
   - Solution: Check that all dependencies in `requirements.txt` are installed
   - Run: `pip install -r requirements.txt`

4. **Executable crashes on startup**
   - Solution: Run with `console=True` in the spec file to see error messages
   - Check that all HTML files and assets are included

#### macOS

1. **"Command not found: python3"**
   - Solution: Install Python 3 via Homebrew: `brew install python3`

2. **Qt5 dependencies missing**
   - Solution: `brew install qt5`

3. **Code signing issues (for distribution)**
   - Solution: Add codesign_identity in the spec file
   - Or use: `codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/AutoFlightGenerator.app`

4. **App won't open (Gatekeeper)**
   - Solution: Right-click > Open, or use: `xattr -cr dist/AutoFlightGenerator.app`

## Spec File Configuration

The `AutoFlightGenerator.spec` file contains:
- **Hidden imports**: All Python modules that need to be included
- **Data files**: HTML maps, images, JSON configs, etc.
- **Binary files**: Any compiled libraries needed
- **Console mode**: Set to `False` for GUI applications (set to `True` for debugging)

### Key Settings

- `console=False`: No console window (GUI app)
- `upx=False`: Disabled UPX compression for compatibility
- `name='AutoFlightGenerator'`: Output executable name

## Included Files

The spec file automatically includes:
- All Python modules
- HTML map files (`map.html`, `enhanced_map.html`, etc.)
- Images directory
- JSON configuration files
- Aircraft parameters directory
- PyQt5 and PyQtWebEngine data files

## Testing the Package

### Windows
1. Navigate to `dist` folder
2. Double-click `AutoFlightGenerator.exe`
3. Test all major features:
   - Dashboard opens
   - Map loads
   - Delivery Route tool works
   - File save/load functions work

### macOS
1. Double-click `dist/AutoFlightGenerator.app`
2. If blocked by Gatekeeper, right-click > Open
3. Test all major features as above

## Distribution

### Windows
- Distribute `AutoFlightGenerator.exe` (standalone)
- Or distribute `AutoFlightGenerator_Setup.exe` (installer)

### macOS
- Distribute `AutoFlightGenerator.app` (app bundle)
- Or distribute `AutoFlightGenerator_Setup.dmg` (DMG installer)

### Notes
- The executable is self-contained (includes Python interpreter)
- No Python installation required on target machines
- File size will be ~100-200 MB (includes all dependencies)
- First launch may be slower (extracting files)

## Advanced Options

### Reduce File Size
- Use `--exclude-module` to exclude unused modules
- Use UPX compression (may cause compatibility issues)
- Remove unused HTML files from spec

### Debug Build
- Set `console=True` in spec file
- Set `debug=True` in spec file
- Run executable from command line to see errors

### Custom Icon
- Add icon path to spec file: `icon='Images/icon.ico'` (Windows) or `icon='Images/icon.icns'` (macOS)

## Support

For issues or questions:
1. Check this guide
2. Review PyInstaller documentation: https://pyinstaller.org/
3. Check error messages in console (with `console=True`)
