@echo off
setlocal

REM Define paths and URLs
set REPO_URL=https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application
set REPO_DIR=LinkedIn_AIHawk_automatic_job_application
set PYTHON_EXE=python
set CONFIG_EXAMPLE=data_folder_example

REM Check if Python is installed
where %PYTHON_EXE% >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Downloading and installing Python...
    start https://www.python.org/downloads/
    echo Please install Python manually and run this script again.
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

REM Install Python packages and ChromeDriver
echo Installing required Python packages and ChromeDriver...
%PYTHON_EXE% -m pip install -r requirements.txt
%PYTHON_EXE% -m pip install webdriver-manager

REM Copy example configuration files
echo Setting up configuration files...
if not exist data_folder (
    mkdir data_folder
)
xcopy /E /I %CONFIG_EXAMPLE% data_folder\
echo Please update data_folder\secrets.yaml and data_folder\config.yaml with your credentials and preferences.

REM Run the application with ChromeDriver managed automatically
echo Running the application...
%PYTHON_EXE% -c "from webdriver_manager.chrome import ChromeDriverManager; from selenium import webdriver; driver = webdriver.Chrome(ChromeDriverManager().install()); driver.get('https://www.google.com');"

endlocal
pause
