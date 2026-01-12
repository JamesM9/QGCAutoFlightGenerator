; UAS Flight Generator Inno Setup Script
; This script creates a professional Windows installer for the PyInstaller-built application

#define MyAppName "AutoFlightGenerator"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "VERSATILE UAS Flight Generator"
#define MyAppURL "https://github.com/your-repo/uasflightgenerator"
#define MyAppExeName "AutoFlightGenerator.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=AutoFlightGenerator_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main application executable (single file from PyInstaller)
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; HTML files for map functionality
Source: "map.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "enhanced_map.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "enhanced_map_backup.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "enhanced_map_with_faa.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "mapping_map.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "qgc_style_map.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "map_uasfm_minimal_integration.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "map_with_uasfm_example.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "map_with_uasfm_integrated.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "test_visualization.html"; DestDir: "{app}"; Flags: ignoreversion

; Images directory
Source: "Images\*"; DestDir: "{app}\Images"; Flags: ignoreversion recursesubdirs

; Configuration files
Source: "app_settings.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "aircraft_profiles.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "user_profiles.json"; DestDir: "{app}"; Flags: ignoreversion

; Aircraft Parameters System
Source: "aircraft_parameters\*"; DestDir: "{app}\aircraft_parameters"; Flags: ignoreversion recursesubdirs

; Documentation files
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

; Python source files (for reference and debugging)
Source: "dashboard.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "deliveryroute.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "multidelivery.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "securityroute.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "linearflightroute.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "towerinspection.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "atob_mission_planner.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "settings_manager.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "settings_dialog.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "mission_library.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "enhanced_forms.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "enhanced_map.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "shared_toolbar.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "utils.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "mapping_flight.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "structure_scan.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "tutorial_dialog.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "cpu_optimizer.py"; DestDir: "{app}\source"; Flags: ignoreversion

; Phase 3 Enhancement Files
Source: "error_handler.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "plan_visualizer.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "progress_manager.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "responsive_layout.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "breadcrumb_navigator.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "input_validator.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "adaptive_layout.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "advanced_preferences.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "smart_suggestions.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "performance_optimizer.py"; DestDir: "{app}\source"; Flags: ignoreversion

; Aircraft Parameters System Files
Source: "aircraft_parameter_manager.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "aircraft_configuration_dialog.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "parameter_aware_waypoint_generator.py"; DestDir: "{app}\source"; Flags: ignoreversion

; Additional Enhancement Files
Source: "mission_file_generator.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "faa_maps_integration.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "video_config.py"; DestDir: "{app}\source"; Flags: ignoreversion
Source: "video_player_widget.py"; DestDir: "{app}\source"; Flags: ignoreversion

; Requirements file
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
; Add uninstall information to registry
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayName"; ValueData: "{#MyAppName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "UninstallString"; ValueData: "{uninstallexe}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayIcon"; ValueData: "{app}\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "Publisher"; ValueData: "{#MyAppPublisher}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "URLInfoAbout"; ValueData: "{#MyAppURL}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: dword; ValueName: "NoModify"; ValueData: 1; Flags: uninsdeletekey
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}"; ValueType: dword; ValueName: "NoRepair"; ValueData: 1; Flags: uninsdeletekey