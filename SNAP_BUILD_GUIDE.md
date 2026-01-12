# AutoFlight Generator - Snap Package Build Guide

This guide explains how to build and publish the AutoFlight Generator as a snap package for Ubuntu and other Linux distributions.

## What is a Snap Package?

Snap packages are containerized software packages that work across a wide variety of Linux distributions. They include all dependencies and run in isolation, making them secure and easy to install.

## Prerequisites

### On Ubuntu 18.04 or later:
```bash
sudo apt update
sudo apt install snapcraft
```

### On other distributions:
```bash
sudo snap install snapcraft --classic
```

### Additional Requirements:
- Internet connection (for downloading dependencies)
- At least 4GB of free disk space
- multipass (will be installed automatically by snapcraft if needed)

## Building the Snap Package

### Method 1: Using the Build Script (Recommended)

1. **Clone or navigate to the project directory:**
   ```bash
   cd /path/to/AutoFlightGenerator
   ```

2. **Run the build script:**
   ```bash
   ./build_snap.sh
   ```

   The script will:
   - Check for snapcraft installation
   - Clean previous builds
   - Build the snap package
   - Provide instructions for installation and publishing

### Method 2: Manual Build

1. **Navigate to the project directory:**
   ```bash
   cd /path/to/AutoFlightGenerator
   ```

2. **Clean any previous builds:**
   ```bash
   snapcraft clean
   ```

3. **Build the snap:**
   ```bash
   snapcraft
   ```

## Testing the Snap Package

### Install Locally for Testing

After a successful build, you'll have a `.snap` file. Install it locally:

```bash
sudo snap install --dangerous --devmode autoflight-generator_2.0.0_amd64.snap
```

**Note:** The exact filename may vary based on version and architecture.

### Run the Application

```bash
autoflight-generator
```

### Uninstall (if needed)

```bash
sudo snap remove autoflight-generator
```

## Publishing to the Snap Store

### 1. Create a Snapcraft Developer Account

1. Go to https://snapcraft.io
2. Click "Register" and create an account
3. Verify your email address

### 2. Register Your Snap Name

```bash
snapcraft login
snapcraft register autoflight-generator
```

**Note:** Snap names must be unique. If "autoflight-generator" is taken, you'll need to choose a different name and update the `snapcraft.yaml` file.

### 3. Upload Your Snap

```bash
snapcraft upload autoflight-generator_2.0.0_amd64.snap
```

### 4. Release Your Snap

```bash
snapcraft release autoflight-generator <revision> <channel>
```

**Channels:**
- `edge`: For development builds
- `beta`: For beta testing
- `candidate`: For release candidates
- `stable`: For stable releases

Example:
```bash
snapcraft release autoflight-generator 1 stable
```

## File Structure

The snap package includes the following key files:

```
snap/
├── snapcraft.yaml          # Main snap configuration
└── local/
    ├── autoflight-generator.desktop  # Desktop integration file
    └── autoflight-generator.png      # Application icon
build_snap.sh               # Build script
```

## Snap Configuration Details

### Confinement

The snap uses `strict` confinement for security while providing necessary permissions through plugs:

- `home`: Access to user's home directory
- `network`: Internet access for terrain data
- `desktop`: Desktop environment integration
- `opengl`: Graphics acceleration
- `audio-playback`: Audio support
- `removable-media`: Access to USB drives, etc.

### Applications

The snap provides one application entry point:
- `autoflight-generator`: Main application command

### Dependencies

The snap includes all necessary dependencies:
- Python 3.10 runtime
- PyQt5 and QtWebEngine
- Scientific libraries (NumPy, Matplotlib, Shapely)
- System libraries for graphics and audio

## Troubleshooting

### Common Build Issues

1. **"snapcraft not found"**
   - Install snapcraft: `sudo snap install snapcraft --classic`

2. **Build fails with Python errors**
   - Check that all dependencies in `requirements.txt` are compatible
   - Verify Python version compatibility

3. **Missing system libraries**
   - The snapcraft.yaml includes comprehensive stage-packages
   - If issues persist, add missing packages to the stage-packages list

4. **QtWebEngine issues**
   - Ensure all Qt5 packages are included in stage-packages
   - Check that the launch script sets proper environment variables

### Testing Issues

1. **Application won't start**
   - Check logs: `snap logs autoflight-generator`
   - Try running in devmode: `sudo snap install --dangerous --devmode <snap-file>`

2. **Graphics/GUI issues**
   - Ensure you're running on a system with X11 or Wayland
   - Check that graphics drivers are properly installed

3. **File access issues**
   - The snap has limited file system access
   - Use the file picker to access files outside the home directory

### Publishing Issues

1. **Name already taken**
   - Choose a different name and update `snapcraft.yaml`
   - Consider using a prefix like `your-company-autoflight-generator`

2. **Upload fails**
   - Check your internet connection
   - Verify you're logged in: `snapcraft whoami`

## Advanced Configuration

### Custom Icons

To use your own icon:
1. Replace `snap/local/autoflight-generator.png` with your icon (256x256 PNG recommended)
2. Rebuild the snap

### Additional Features

To add more features to the snap:
1. Update the `snapcraft.yaml` file
2. Add necessary plugs for additional permissions
3. Update stage-packages if new system dependencies are needed

### Environment Variables

The launch script sets several environment variables for proper operation:
- `PYTHONPATH`: Python module search path
- `QT_QPA_PLATFORM_PLUGIN_PATH`: Qt platform plugins
- `QTWEBENGINEPROCESS_PATH`: QtWebEngine process location

## Support and Documentation

- **Snapcraft Documentation**: https://snapcraft.io/docs
- **Snap Forum**: https://forum.snapcraft.io
- **GitHub Issues**: Create issues in the project repository

## License and Distribution

When publishing to the Snap Store, ensure you comply with:
- Your application's license terms
- Snap Store policies
- Any third-party dependency licenses

The snap package will automatically include license information from your project.
