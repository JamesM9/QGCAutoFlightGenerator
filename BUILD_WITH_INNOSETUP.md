# Building with Inno Setup

Yes! AutoFlightGenerator can be built using Inno Setup to create a professional Windows installer.

## Prerequisites

1. **Inno Setup** (free installer tool for Windows)
   - Download from: https://jrsoftware.org/isinfo.php
   - Install the software
   - Make sure `iscc.exe` is in your system PATH (or use full path)

2. **PyInstaller executable must be built first**
   - Run `build_windows.bat` to create `dist\AutoFlightGenerator.exe`
   - Or manually: `pyinstaller AutoFlightGenerator.spec`

## Quick Build Process

### Option 1: Automatic Build (Recommended)

The `build_windows.bat` script automatically creates the Inno Setup installer:

```batch
build_windows.bat
```

This will:
1. Build the PyInstaller executable
2. Automatically run Inno Setup to create the installer
3. Output: `installer\AutoFlightGenerator_Setup.exe`

### Option 2: Manual Build

1. **First, build the executable:**
   ```batch
   pyinstaller AutoFlightGenerator.spec
   ```

2. **Then, create the installer:**
   ```batch
   iscc AutoFlightGenerator_Setup.iss
   ```

   Or if `iscc` is not in PATH:
   ```batch
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" AutoFlightGenerator_Setup.iss
   ```

3. **Find your installer:**
   - Location: `installer\AutoFlightGenerator_Setup.exe`

## What the Inno Setup Script Does

The `AutoFlightGenerator_Setup.iss` script creates an installer that:

1. **Installs the application** to `C:\Program Files\AutoFlightGenerator`
2. **Includes all necessary files:**
   - Main executable (`AutoFlightGenerator.exe`)
   - All HTML map files
   - Images directory
   - Configuration files
   - Aircraft parameters
   - Source files (for reference)
   - Documentation

3. **Creates shortcuts:**
   - Start Menu shortcut
   - Desktop shortcut (optional)
   - Uninstaller entry

4. **Registry entries:**
   - Proper uninstall information
   - Application metadata

5. **User-friendly installer:**
   - Modern wizard interface
   - Installation directory selection
   - Optional components
   - Silent installation support

## Installer Features

- **Professional appearance** with modern wizard style
- **Compression**: LZMA compression for smaller installer size
- **64-bit only**: Optimized for modern Windows systems
- **Requires admin privileges**: Installs to Program Files
- **Uninstall support**: Clean uninstallation via Control Panel

## Customizing the Installer

Edit `AutoFlightGenerator_Setup.iss` to customize:

- **App name/version**: Change `#define MyAppName` and `#define MyAppVersion`
- **Publisher info**: Update `#define MyAppPublisher` and `#define MyAppURL`
- **Installation path**: Modify `DefaultDirName` in `[Setup]` section
- **Additional files**: Add files in the `[Files]` section
- **Custom icons**: Add icon path if you have an `.ico` file

## Distribution

The installer (`installer\AutoFlightGenerator_Setup.exe`) can be distributed to users.

**End users can:**
- Double-click the installer
- Follow the installation wizard
- Launch from Start Menu or Desktop shortcut
- Uninstall via Control Panel

**No prerequisites needed** - everything is included in the installer!

## File Locations After Installation

- **Application**: `C:\Program Files\AutoFlightGenerator\AutoFlightGenerator.exe`
- **HTML Maps**: `C:\Program Files\AutoFlightGenerator\map.html` (etc.)
- **Images**: `C:\Program Files\AutoFlightGenerator\Images\`
- **Config**: `C:\Program Files\AutoFlightGenerator\app_settings.json`
- **Source**: `C:\Program Files\AutoFlightGenerator\source\` (reference only)

## Troubleshooting

### Inno Setup Not Found

If you get "iscc not found":
- Install Inno Setup from https://jrsoftware.org/isinfo.php
- Add Inno Setup to PATH, or use full path to `iscc.exe`

### Executable Not Found

If installer build fails with "executable not found":
1. Make sure `dist\AutoFlightGenerator.exe` exists
2. Run `pyinstaller AutoFlightGenerator.spec` first
3. Check that the executable was built successfully

### Build Errors

If you encounter build errors:
1. Check that all source files exist
2. Verify HTML files are in the project root
3. Ensure Images directory exists
4. Check Inno Setup script for correct paths

## Silent Installation

For automated deployments, the installer supports silent installation:

```batch
AutoFlightGenerator_Setup.exe /SILENT
```

Or completely silent (no progress window):
```batch
AutoFlightGenerator_Setup.exe /VERYSILENT
```

## Summary

✅ **Yes, Inno Setup is fully supported!**
- Script is ready to use: `AutoFlightGenerator_Setup.iss`
- Automatic build: Run `build_windows.bat`
- Manual build: `iscc AutoFlightGenerator_Setup.iss`
- Professional installer with all features
- No coding required - just run the script!
