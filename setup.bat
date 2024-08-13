@echo off
setlocal

REM Define paths and URLs
set REPO_URL=https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application
set REPO_DIR=LinkedIn_AIHawk_automatic_job_application
set PYTHON_EXE=python
set CHROME_URL=https://dl.google.com/chrome/install/latest/chrome_installer.exe
set CONFIG_EXAMPLE=data_folder_example

REM Check if Python is installed
where %PYTHON_EXE% >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Downloading and installing Python...
    start https://www.python.org/downloads/
    echo Please install Python manually and run this script again.
    exit /b 1
)

REM Check if Google Chrome is installed
start "" "chrome://settings/help"
if %errorlevel% neq 0 (
    echo Google Chrome is not installed. Downloading and installing Chrome...
    powershell -Command "Start-BitsTransfer -Source %CHROME_URL% -Destination chrome_installer.exe"
    start chrome_installer.exe
    echo Please install Google Chrome manually and run this script again.
    exit /b 1
)

REM Clone the repository
if exist %REPO_DIR% (
    echo Repository already exists. Pulling latest changes...
    cd %REPO_DIR%
    git pull
    cd ..
) else (
    echo Cloning the repository...
    git clone %REPO_URL%
    cd %REPO_DIR%
)

REM Install Python packages
echo Installing required Python packages...
%PYTHON_EXE% -m pip install -r requirements.txt

REM Copy example configuration files
echo Setting up configuration files...
if not exist data_folder (
    mkdir data_folder
)
xcopy /E /I %CONFIG_EXAMPLE% data_folder\
echo Please update data_folder\secrets.yaml and data_folder\config.yaml with your credentials and preferences.

REM Run the application
echo Running the application...
%PYTHON_EXE% main.py

endlocal
pause
