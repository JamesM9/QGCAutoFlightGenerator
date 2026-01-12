#!/usr/bin/env python3
"""
VERSATILE UAS Flight Generator - Universal Build Script
Builds the application for Windows, macOS, and Linux platforms
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class BuildManager:
    def __init__(self):
        self.platform = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.installer_dir = self.project_root / "installer"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def run_command(self, command, shell=True, check=True):
        """Run a command and handle errors"""
        self.log(f"Running: {command}")
        try:
            result = subprocess.run(command, shell=shell, check=check, 
                                  capture_output=True, text=True)
            if result.stdout:
                self.log(f"Output: {result.stdout.strip()}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"Command failed: {e}", "ERROR")
            if e.stderr:
                self.log(f"Error: {e.stderr.strip()}", "ERROR")
            raise
            
    def check_python(self):
        """Check Python installation and version"""
        self.log("Checking Python installation...")
        try:
            result = self.run_command("python --version", check=False)
            if result.returncode != 0:
                result = self.run_command("python3 --version", check=False)
                
            version = result.stdout.strip()
            self.log(f"Found Python: {version}")
            
            # Check if version is 3.8+
            import sys
            if sys.version_info < (3, 8):
                raise RuntimeError("Python 3.8+ is required")
                
        except Exception as e:
            self.log(f"Python check failed: {e}", "ERROR")
            raise
            
    def check_dependencies(self):
        """Check and install required dependencies"""
        self.log("Checking dependencies...")
        
        # Check if requirements.txt exists
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            self.log("requirements.txt not found", "ERROR")
            return False
            
        # Install dependencies
        try:
            self.run_command(f"pip install -r {requirements_file}")
            self.log("Dependencies installed successfully")
            return True
        except Exception as e:
            self.log(f"Failed to install dependencies: {e}", "ERROR")
            return False
            
    def clean_build(self):
        """Clean previous build artifacts"""
        self.log("Cleaning previous builds...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                self.log(f"Cleaned {dir_path}")
                
        # Don't clean installer directory as it may contain final installers
        
    def build_pyinstaller(self):
        """Build using PyInstaller"""
        self.log("Building with PyInstaller...")
        
        spec_file = self.project_root / "AutoFlightGenerator.spec"
        if not spec_file.exists():
            self.log("AutoFlightGenerator.spec not found", "ERROR")
            return False
            
        try:
            self.run_command(f"pyinstaller {spec_file}")
            self.log("PyInstaller build completed")
            return True
        except Exception as e:
            self.log(f"PyInstaller build failed: {e}", "ERROR")
            return False
            
    def build_windows_installer(self):
        """Build Windows installer using Inno Setup"""
        if self.platform != "windows":
            self.log("Skipping Windows installer (not on Windows)", "INFO")
            return True
            
        self.log("Building Windows installer...")
        
        # Check if Inno Setup is available
        try:
            self.run_command("iscc /?", check=False)
        except:
            self.log("Inno Setup (iscc) not found in PATH", "WARNING")
            self.log("Please install Inno Setup from: https://jrsoftware.org/isinfo.php")
            return False
            
        iss_file = self.project_root / "AutoFlightGenerator_Setup.iss"
        if not iss_file.exists():
            self.log("AutoFlightGenerator_Setup.iss not found", "ERROR")
            return False
            
        try:
            self.run_command(f'iscc "{iss_file}"')
            self.log("Windows installer built successfully")
            return True
        except Exception as e:
            self.log(f"Windows installer build failed: {e}", "ERROR")
            return False
            
    def build_macos_dmg(self):
        """Build macOS DMG (optional)"""
        if self.platform != "darwin":
            self.log("Skipping macOS DMG (not on macOS)", "INFO")
            return True
            
        self.log("Building macOS DMG...")
        
        # Check if create-dmg is available
        try:
            self.run_command("create-dmg --version", check=False)
        except:
            self.log("create-dmg not found", "WARNING")
            self.log("Install with: brew install create-dmg")
            return False
            
        # Check if app bundle exists
        app_bundle = self.dist_dir / "UASFlightGenerator.app"
        if not app_bundle.exists():
            self.log("App bundle not found", "ERROR")
            return False
            
        try:
            dmg_script = self.project_root / "create_dmg.sh"
            if dmg_script.exists():
                self.run_command(f"chmod +x {dmg_script}")
                self.run_command(f"./{dmg_script}")
                self.log("macOS DMG built successfully")
            else:
                self.log("create_dmg.sh not found", "WARNING")
            return True
        except Exception as e:
            self.log(f"macOS DMG build failed: {e}", "ERROR")
            return False
            
    def build_snap(self):
        """Build Linux Snap package"""
        if self.platform != "linux":
            self.log("Skipping Snap build (not on Linux)", "INFO")
            return True
            
        self.log("Building Snap package...")
        
        # Check if snapcraft is available
        try:
            self.run_command("snapcraft --version", check=False)
        except:
            self.log("snapcraft not found", "WARNING")
            self.log("Install with: sudo snap install snapcraft --classic")
            return False
            
        try:
            self.run_command("snapcraft clean")
            self.run_command("snapcraft")
            self.log("Snap package built successfully")
            return True
        except Exception as e:
            self.log(f"Snap build failed: {e}", "ERROR")
            return False
            
    def verify_build(self):
        """Verify that the build was successful"""
        self.log("Verifying build...")
        
        success = True
        
        # Check for executable
        if self.platform == "windows":
            exe_path = self.dist_dir / "UASFlightGenerator.exe"
        else:
            exe_path = self.dist_dir / "UASFlightGenerator"
            
        if exe_path.exists():
            self.log(f"✓ Executable found: {exe_path}")
        else:
            self.log(f"✗ Executable not found: {exe_path}", "ERROR")
            success = False
            
        # Check for installer (platform-specific)
        if self.platform == "windows":
            installer_path = self.installer_dir / "UASFlightGenerator_Setup.exe"
            if installer_path.exists():
                self.log(f"✓ Windows installer found: {installer_path}")
            else:
                self.log(f"✗ Windows installer not found: {installer_path}", "WARNING")
                
        elif self.platform == "darwin":
            app_bundle = self.dist_dir / "UASFlightGenerator.app"
            if app_bundle.exists():
                self.log(f"✓ macOS app bundle found: {app_bundle}")
            else:
                self.log(f"✗ macOS app bundle not found: {app_bundle}", "WARNING")
                
        elif self.platform == "linux":
            snap_files = list(self.project_root.glob("*.snap"))
            if snap_files:
                self.log(f"✓ Snap package found: {snap_files[0]}")
            else:
                self.log("✗ Snap package not found", "WARNING")
                
        return success
        
    def build_all(self):
        """Main build process"""
        self.log("Starting VERSATILE UAS Flight Generator build process...")
        self.log(f"Platform: {self.platform}")
        self.log(f"Project root: {self.project_root}")
        
        try:
            # Step 1: Check Python
            self.check_python()
            
            # Step 2: Install dependencies
            if not self.check_dependencies():
                return False
                
            # Step 3: Clean previous builds
            self.clean_build()
            
            # Step 4: Build with PyInstaller
            if not self.build_pyinstaller():
                return False
                
            # Step 5: Build platform-specific installers
            if self.platform == "windows":
                self.build_windows_installer()
            elif self.platform == "darwin":
                self.build_macos_dmg()
            elif self.platform == "linux":
                self.build_snap()
                
            # Step 6: Verify build
            if self.verify_build():
                self.log("Build completed successfully!", "SUCCESS")
                return True
            else:
                self.log("Build completed with warnings", "WARNING")
                return True
                
        except Exception as e:
            self.log(f"Build failed: {e}", "ERROR")
            return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("VERSATILE UAS Flight Generator - Universal Build Script")
    print("=" * 60)
    print()
    
    build_manager = BuildManager()
    success = build_manager.build_all()
    
    print()
    print("=" * 60)
    if success:
        print("BUILD COMPLETED SUCCESSFULLY!")
        print("Check the 'dist' and 'installer' directories for output files.")
    else:
        print("BUILD FAILED!")
        print("Check the error messages above for details.")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
