# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(SPEC))

# Collect all data files and hidden imports
datas = []
hiddenimports = []

# Add HTML files - include all map HTML files
html_files = [
    'map.html', 
    'enhanced_map.html', 
    'enhanced_map_backup.html',
    'enhanced_map_with_faa.html',
    'mapping_map.html',
    'qgc_style_map.html',
    'map_with_uasfm_integrated.html',
    'map_with_uasfm_example.html',
    'map_uasfm_minimal_integration.html',
    'test_visualization.html'
]
for html_file in html_files:
    html_path = os.path.join(current_dir, html_file)
    if os.path.exists(html_path):
        datas.append((html_path, '.'))

# Add Images directory
images_dir = os.path.join(current_dir, 'Images')
if os.path.exists(images_dir):
    for file in os.listdir(images_dir):
        if file.endswith(('.svg', '.png', '.jpg', '.jpeg')):
            datas.append((os.path.join(images_dir, file), 'Images'))

# Add JSON configuration files
config_files = ['app_settings.json', 'aircraft_profiles.json', 'user_profiles.json']
for config_file in config_files:
    config_path = os.path.join(current_dir, config_file)
    if os.path.exists(config_path):
        datas.append((config_path, '.'))

# Add aircraft_parameters directory
aircraft_params_dir = os.path.join(current_dir, 'aircraft_parameters')
if os.path.exists(aircraft_params_dir):
    datas.append((aircraft_params_dir, 'aircraft_parameters'))

# Collect PyQt5 data files
try:
    datas.extend(collect_data_files('PyQt5'))
    hiddenimports.extend(collect_submodules('PyQt5'))
except:
    pass

# Collect PyQtWebEngine data files
try:
    datas.extend(collect_data_files('PyQtWebEngine'))
    hiddenimports.extend(collect_submodules('PyQtWebEngine'))
except:
    pass

# Add additional hidden imports for dependencies
additional_imports = [
    'shapely',
    'shapely.geometry',
    'shapely.prepared',
    'numpy',
    'numpy.core._methods',
    'numpy.lib.format',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_agg',
    'matplotlib.backends.backend_qt5agg',
    'geopy',
    'geopy.distance',
    'geopy.geocoders',
    'cpu_optimizer',
    'shared_toolbar',
    'settings_manager',
    'mission_library',
    'enhanced_forms',
    'enhanced_map',
    'utils',
    'error_handler',
    'plan_visualizer',
    'deliveryroute',
    'multidelivery',
    'securityroute',
    'linearflightroute',
    'towerinspection',
    'mapping_flight',
    'structure_scan',
    'atob_mission_planner',
    'aircraft_parameters',
    'aircraft_parameters.parameter_file_manager',
    'aircraft_parameters.flight_characteristics_analyzer',
    'aircraft_parameters.mission_tool_integration',
    'aircraft_parameters.parameter_ui_component',
    'aircraft_parameters.configuration_manager',
    'aircraft_parameters.parameter_validator',
    'aircraft_parameters.parameter_import_export',
    'aircraft_parameters.parameter_preview',
    'aircraft_parameters.advanced_configuration_editor',
    'aircraft_parameters.configuration_editor',
    'aircraft_parameters.dashboard_integration',
    'aircraft_parameters.settings_integration',
    'aircraft_parameters.mission_tool_base',
    'tutorial_dialog',
    'video_config',
    'video_player_widget',
    'faa_maps_integration',
    'mission_file_generator',
    'parameter_aware_waypoint_generator',
    'aircraft_parameter_manager',
    'aircraft_configuration_dialog',
    'progress_manager',
    'performance_optimizer',
    'input_validator',
    'smart_suggestions',
    'adaptive_layout',
    'responsive_layout'
]

hiddenimports.extend(additional_imports)

# Collect all Python modules - PyInstaller will automatically find them via hiddenimports
# We don't need to add them as data files, they'll be compiled into the executable

a = Analysis(
    ['dashboard.py'],  # Main entry point
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='AutoFlightGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid compatibility issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one (e.g., 'Images/icon.ico' for Windows)
)
