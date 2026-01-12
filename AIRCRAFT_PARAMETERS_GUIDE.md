# Aircraft Parameters System Guide

## Overview

The VERSATILE UAS Flight Generator includes a revolutionary Aircraft Parameters System that automatically optimizes flight plans based on your specific aircraft's capabilities and firmware settings. This system imports real ArduPilot or PX4 parameter files and applies those settings to ensure your generated missions are perfectly tailored to your aircraft.

## Key Benefits

- **Safety**: Missions stay within your aircraft's certified limits
- **Optimization**: Flight plans optimized for your specific aircraft
- **Consistency**: Same parameters applied across all mission types
- **Efficiency**: No manual configuration in each tool
- **Accuracy**: Waypoint spacing and speeds match aircraft capabilities
- **Compliance**: Ensures missions comply with firmware safety settings

## How It Works

### 1. Global Parameter Control
- **Dashboard Control**: Enable/disable parameters globally from the main dashboard
- **Automatic Application**: When enabled, all mission tools automatically use your aircraft's parameters
- **No Per-Tool Setup**: No need to configure parameters in each individual tool
- **Seamless Integration**: Parameters are applied automatically during mission generation

### 2. Aircraft Configuration Management
- **Import Parameter Files**: Load .param, .params, or .txt files from your aircraft
- **Create Configurations**: Save aircraft configurations with custom names
- **Multiple Aircraft Support**: Manage configurations for different aircraft
- **Automatic Detection**: System automatically detects aircraft type from parameters

### 3. Smart Parameter Application
- **Altitude Optimization**: Uses PILOT_ALT_MAX or MPC_ALT_MODE for safe altitudes
- **Waypoint Spacing**: Applies WPNAV_RADIUS or NAV_ACC_RAD for optimal spacing
- **Speed Settings**: Uses WPNAV_SPEED, MPC_XY_CRUISE, or AIRSPEED_CRUISE
- **Safety Margins**: Automatically applies firmware safety limits

## Step-by-Step Setup Guide

### Step 1: Import Your Aircraft Parameters
1. Connect to your aircraft with Mission Planner, QGroundControl, or similar
2. Export/download your current parameter file (.param, .params, or .txt format)
3. In the dashboard, click "Import Parameter File" in the Aircraft Parameters section
4. Select your parameter file and import it

### Step 2: Create Aircraft Configuration
1. Click "Manage" in the Aircraft Parameters section
2. Click "New Configuration" to create a new aircraft profile
3. Give your configuration a descriptive name (e.g., "DJI Phantom 4 Pro")
4. Select the imported parameter file
5. Add a description and save the configuration

### Step 3: Enable Parameters Globally
1. Check "Enable Aircraft Parameters" in the dashboard
2. Select your aircraft configuration from the dropdown
3. All mission tools will now automatically use these parameters

### Step 4: Use Mission Tools Normally
1. Open any mission planning tool (Delivery Route, Mapping, etc.)
2. Configure your mission as usual
3. Parameters are automatically applied during mission generation
4. No additional setup required in individual tools

## Supported Aircraft Types

### ArduPilot Firmware
- **ArduCopter (Multicopter)**: MC_, WPNAV_, PILOT_ALT_MAX parameters
- **ArduPlane (Fixed-Wing)**: FW_, AIRSPEED_, FW_AIRSPD_ parameters
- **ArduRover (Ground Vehicle)**: ROV_ parameters
- **ArduSub (Underwater)**: SUB_ parameters

### PX4 Firmware
- **Multicopter**: MPC_, EKF2_, NAV_ parameters
- **Fixed-Wing**: FW_, EKF2_, NAV_ parameters
- **VTOL**: VT_, VTOL_, VT_FW_ parameters
- **Rover**: GND_, EKF2_, NAV_ parameters

## Automatic Aircraft Detection

The system automatically detects your aircraft type from the parameter file:
- **Multicopter**: Detected by MC_, WPNAV_, PILOT_ALT_MAX parameters
- **Fixed-Wing**: Detected by FW_, AIRSPEED_, FW_AIRSPD_ parameters
- **VTOL**: Detected by VT_, VTOL_, VT_FW_ parameters
- **PX4 Variants**: Detected by MPC_, EKF2_, NAV_ parameters

## Key Parameters Used

### Altitude and Safety
- **PILOT_ALT_MAX**: Maximum altitude limit (ArduCopter)
- **MPC_ALT_MODE**: Altitude mode settings (PX4)
- **RTL_ALT**: Return-to-launch altitude

### Navigation and Waypoints
- **WPNAV_RADIUS**: Waypoint acceptance radius (ArduCopter)
- **NAV_ACC_RAD**: Navigation acceptance radius (PX4)
- **WPNAV_SPEED**: Waypoint navigation speed (ArduCopter)

### Speed and Performance
- **MC_XY_CRUISE**: Multicopter cruise speed (ArduCopter)
- **AIRSPEED_CRUISE**: Fixed-wing cruise speed (ArduPlane)
- **MPC_XY_CRUISE**: Multicopter cruise speed (PX4)

## Mission Tool Integration

All mission planning tools automatically benefit from parameter integration:

### Delivery Route Tool
- Automatic altitude optimization based on PILOT_ALT_MAX
- Waypoint spacing adjusted for WPNAV_RADIUS
- Speed settings from WPNAV_SPEED or MPC_XY_CRUISE

### Mapping Flight Tool
- Survey altitude limited by aircraft maximum altitude
- Grid spacing optimized for waypoint acceptance radius
- Flight speed adjusted for optimal coverage

### Security Route Tool
- Patrol altitude within aircraft limits
- Waypoint density optimized for navigation accuracy
- Speed settings for efficient patrol patterns

### All Other Tools
- Linear Flight, Tower Inspection, Structure Scan, A-to-B Mission
- All tools automatically apply aircraft-specific parameters
- Consistent behavior across all mission types

## Troubleshooting

### Parameter Import Issues
- **Unsupported Format**: Ensure file is .param, .params, or .txt format
- **Corrupted File**: Re-export parameters from your ground station
- **Empty Parameters**: Verify parameter file contains actual data

### Configuration Issues
- **No Aircraft Detected**: Check if parameter file contains recognizable parameters
- **Wrong Aircraft Type**: Verify parameter file is from correct firmware
- **Missing Parameters**: Some parameters may not be present in all configurations

### Mission Generation Issues
- **Parameters Not Applied**: Ensure parameters are enabled globally
- **Configuration Not Selected**: Select a configuration from dropdown
- **Fallback to Defaults**: System falls back to default values if parameters unavailable

## Best Practices

- **Regular Updates**: Re-import parameters after firmware updates
- **Multiple Configurations**: Create separate configurations for different aircraft
- **Descriptive Names**: Use clear names for easy identification
- **Backup Parameters**: Keep copies of parameter files for reference
- **Test Missions**: Always test parameter-optimized missions in simulation
- **Verify Settings**: Check that parameters are being applied correctly

## Integration with Mission Planning

The Aircraft Parameters System seamlessly integrates with all mission planning tools:

- **Automatic Application**: Parameters are applied without user intervention
- **Smart Fallbacks**: Uses default values when parameters unavailable
- **Real-time Updates**: Changes to global settings immediately affect all tools
- **Consistent Behavior**: Same parameter logic across all mission types

## File Format Support

The system supports multiple parameter file formats:
- **.param**: Standard ArduPilot parameter files
- **.params**: Alternative ArduPilot parameter files
- **.txt**: Text-based parameter files
- **.parm**: Legacy parameter files

## Advanced Features

### Parameter Validation
- Automatic validation of imported parameters
- Detection of corrupted or invalid parameter files
- Warning system for missing critical parameters

### Configuration Management
- Create, edit, and delete aircraft configurations
- Duplicate configurations for similar aircraft
- Export configurations for backup or sharing

### Real-time Updates
- Global parameter state changes immediately affect all tools
- No need to restart tools when changing configurations
- Seamless switching between different aircraft configurations

## Technical Details

### Parameter Processing
- Automatic parsing of ArduPilot and PX4 parameter files
- Intelligent parameter mapping and validation
- Fallback mechanisms for missing parameters

### Mission Optimization
- Dynamic altitude adjustment based on aircraft limits
- Intelligent waypoint spacing optimization
- Speed and performance parameter integration

### Safety Integration
- Automatic application of firmware safety limits
- Terrain clearance optimization
- Geofence parameter integration

This revolutionary feature ensures your flight plans are perfectly optimized for your specific aircraft, enhancing safety, efficiency, and mission success!
