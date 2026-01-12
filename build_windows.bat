@echo off
echo ========================================
echo VERSATILE UAS Flight Generator - Windows Build Script
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

:: Check if pip is available
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

:: Upgrade pip to latest version
echo Upgrading pip to latest version...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)

:: Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller>=6.15.0
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Check if required packages are installed
echo Checking dependencies...
python -c "import PyQt5, PyQtWebEngine, requests, shapely, numpy, matplotlib" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        echo Trying to install packages individually...
        
        pip install requests>=2.31.0
        pip install PyQt5>=5.15.9
        pip install PyQtWebEngine>=5.15.6
        pip install shapely>=2.0.2
        pip install numpy>=1.26.0
        pip install matplotlib>=3.8.0
        
        if errorlevel 1 (
            echo ERROR: Failed to install packages individually
            pause
            exit /b 1
        )
    )
)

:: Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
:: Don't delete spec files as they are needed for the build

:: Build with PyInstaller using the spec file
echo Building application with PyInstaller...
pyinstaller AutoFlightGenerator.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    echo Check the error messages above for details
    pause
    exit /b 1
)

:: Check if executable was created
if not exist "dist\AutoFlightGenerator.exe" (
    echo ERROR: Executable not found in dist folder
    echo Build may have failed or executable was not created
    echo Checking dist folder contents:
    if exist "dist" dir dist
    pause
    exit /b 1
)

echo.
echo ========================================
echo PyInstaller build completed successfully!
echo ========================================
echo.
echo Executable created: dist\AutoFlightGenerator.exe
echo.

:: Check if Inno Setup is available
echo Checking for Inno Setup...
iscc /? >nul 2>&1
if errorlevel 1 (
    echo WARNING: Inno Setup (iscc) not found in PATH
    echo Please install Inno Setup from: https://jrsoftware.org/isinfo.php
    echo Or manually run: iscc "AutoFlightGenerator_Setup.iss"
    echo.
    echo PyInstaller executable is ready at: dist\AutoFlightGenerator.exe
    echo You can test it by running: dist\AutoFlightGenerator.exe
    pause
    exit /b 0
)

:: Create installer directory
if not exist "installer" mkdir "installer"

:: Build installer with Inno Setup
echo Building Windows installer...
iscc "AutoFlightGenerator_Setup.iss"
if errorlevel 1 (
    echo ERROR: Inno Setup build failed
    echo Check the error messages above for details
    echo.
    echo Common issues:
    echo 1. Make sure all source files exist in the project directory
    echo 2. Check that the dist\AutoFlightGenerator.exe file exists
    echo 3. Verify that all HTML and configuration files are present
    pause
    exit /b 1
)

:: Check if installer was created
if exist "installer\UASFlightGenerator_Setup.exe" (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Files created:
    echo - Executable: dist\AutoFlightGenerator.exe
    echo - Installer: installer\AutoFlightGenerator_Setup.exe
    echo.
    echo You can now distribute the installer to users.
    echo.
    echo To test the application:
    echo 1. Run: dist\AutoFlightGenerator.exe
    echo 2. Or install using: installer\AutoFlightGenerator_Setup.exe
) else (
    echo ERROR: Installer not found
    echo Check if Inno Setup completed successfully
    echo Checking installer folder contents:
    if exist "installer" dir installer
    pause
    exit /b 1
)

echo.
pause
