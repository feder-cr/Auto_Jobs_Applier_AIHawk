#!/bin/bash

# Define paths and URLs
REPO_URL="https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application"
REPO_DIR="LinkedIn_AIHawk_automatic_job_application"
PYTHON_EXE="python3"
CONFIG_EXAMPLE="data_folder_example"

# Check if Python is installed
if ! command -v $PYTHON_EXE &> /dev/null
then
    echo "Python is not installed. Please install Python and rerun the script."
    exit 1
fi

# Clone the repository
if [ -d "$REPO_DIR" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd $REPO_DIR
    git pull
    cd ..
else
    echo "Cloning the repository..."
    git clone $REPO_URL
    cd $REPO_DIR
fi

# Install Python packages and ChromeDriver
echo "Installing required Python packages and ChromeDriver..."
$PYTHON_EXE -m pip install -r requirements.txt
$PYTHON_EXE -m pip install webdriver-manager

# Copy example configuration files
echo "Setting up configuration files..."
mkdir -p data_folder
cp -r $CONFIG_EXAMPLE/* data_folder/
echo "Please update data_folder/secrets.yaml and data_folder/config.yaml with your credentials and preferences."

# Run the application with ChromeDriver managed automatically
echo "Running the application..."
$PYTHON_EXE -c "from webdriver_manager.chrome import ChromeDriverManager; from selenium import webdriver; driver = webdriver.Chrome(ChromeDriverManager().install()); driver.get('https://www.google.com');"

exit 0
