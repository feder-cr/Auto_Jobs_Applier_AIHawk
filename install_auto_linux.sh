#!/bin/bash

# Auto_Jobs_Applier_AIHawk Automated Installation Script
# This script sets up the Auto_Jobs_Applier_AIHawk project on Ubuntu via WSL.

# Use
# chmod +x install_auto_linux.sh
# ./install_auto_linux.sh

#!/bin/bash

# Auto_Jobs_Applier_AIHawk Automated Installation Script
# This script sets up the Auto_Jobs_Applier_AIHawk project on Ubuntu via WSL.

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error
set -o pipefail  # Prevent errors in a pipeline from being masked

# Variables
PROJECT_DIR="$(pwd)"
VENV_DIR="virtual"
CRON_SCRIPT="run_auto_jobs.sh"
CRON_LOG="$PROJECT_DIR/cron.log"
RESUME_DIR="$PROJECT_DIR/resumes"
RESUME_FILE="resume.pdf"

# Function to display information messages (redirected to stderr)
function echo_info() {
    echo -e "\e[34m[INFO]\e[0m $1" >&2
}

# Function to display error messages
function echo_error() {
    echo -e "\e[31m[ERROR]\e[0m $1" >&2
}

# Function to get the correct ChromeDriver version
function get_chromedriver_version() {
    local chrome_version="$1"
    local major_version
    major_version=$(echo "$chrome_version" | cut -d. -f1)
    local chromedriver_version

    echo_info "Fetching ChromeDriver version for Chrome version: $chrome_version"

    # Attempt to get the specific ChromeDriver version based on major version
    chromedriver_version=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$major_version")

    # Check if the version was successfully retrieved
    if [[ -z "$chromedriver_version" || "$chromedriver_version" == *"NoSuchKey"* ]]; then
        echo_info "Specific ChromeDriver version for Chrome $major_version not found."
        echo_info "Fetching the latest available ChromeDriver version..."
        chromedriver_version=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE")
        
        if [[ -z "$chromedriver_version" || "$chromedriver_version" == *"NoSuchKey"* ]]; then
            echo_error "Unable to retrieve ChromeDriver version. Please check your internet connection and try again."
            exit 1
        fi

        echo_info "Retrieved ChromeDriver version: $chromedriver_version"
    else
        echo_info "Retrieved ChromeDriver version: $chromedriver_version"
    fi

    echo "$chromedriver_version"
}

# Step 1: Update and Upgrade Ubuntu Packages
echo_info "Updating and upgrading Ubuntu packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install Essential Dependencies
echo_info "Installing essential dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    wget \
    unzip \
    git \
    curl \
    gnupg \
    software-properties-common

# Step 3: Set Up Python Virtual Environment
echo_info "Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Step 4: Install Project Dependencies
echo_info "Installing project dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Install Google Chrome
echo_info "Installing Google Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt-get install -f -y
rm google-chrome-stable_current_amd64.deb

# Step 6: Install ChromeDriver
echo_info "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(get_chromedriver_version "$CHROME_VERSION")
wget "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip

# Verify ChromeDriver Installation
echo_info "Verifying ChromeDriver installation..."
chromedriver --version

# Step 7: Update Configuration Files
echo_info "Updating configuration files..."

# Paths to configuration files
CONFIG_YAML="$PROJECT_DIR/data_folder/config.yaml"
PLAIN_TEXT_RESUME_YAML="$PROJECT_DIR/data_folder/plain_text_resume.yaml"

# Ensure configuration files exist
if [[ ! -f "$CONFIG_YAML" ]]; then
    echo_error "Configuration file not found: $CONFIG_YAML"
    exit 1
fi

if [[ ! -f "$PLAIN_TEXT_RESUME_YAML" ]]; then
    echo_error "Plain text resume file not found: $PLAIN_TEXT_RESUME_YAML"
    exit 1
fi

# Step 8: Create .env File
echo_info "Setting up the .env file..."

ENV_FILE="$PROJECT_DIR/.env"
ENV_EXAMPLE_FILE="$PROJECT_DIR/.env.example"

# Create .env.example if it doesn't exist
if [[ ! -f "$ENV_EXAMPLE_FILE" ]]; then
    echo_info "Creating .env.example file..."
    cat <<EOL > "$ENV_EXAMPLE_FILE"
# .env.example

LLM_API_KEY=your_actual_api_key_here
EOL
fi

# Check if .env already exists to prevent overwriting
if [[ ! -f "$ENV_FILE" ]]; then
    # Prompt user to enter their LLM_API_KEY
    echo_info "Please enter your LLM_API_KEY (OpenAI, Ollama, or Gemini):"
    read -rp "LLM_API_KEY: " LLM_API_KEY

    # Write the LLM_API_KEY to the .env file
    echo "LLM_API_KEY=$LLM_API_KEY" > "$ENV_FILE"

    echo_info ".env file has been set up successfully."
else
    echo_info ".env file already exists. Skipping setup."
fi

# Step 9: Create Shell Script to Run the Python Script
echo_info "Creating shell script for automated execution..."

CRON_SCRIPT_PATH="$PROJECT_DIR/$CRON_SCRIPT"

cat <<EOL > "$CRON_SCRIPT_PATH"
#!/bin/bash

# Auto_Jobs_Applier_AIHawk Cron Job Script

# Redirect all output to cron.log
exec >> "$CRON_LOG" 2>&1

# Insert a timestamp
echo "----- \$(date) -----"

# Navigate to the project directory
cd "$PROJECT_DIR" || { echo "Failed to navigate to project directory"; exit 1; }

# Activate the virtual environment
source "$VENV_DIR/bin/activate" || { echo "Failed to activate virtual environment"; exit 1; }

# Run the Python script with the resume
python main.py --resume "$RESUME_DIR/$RESUME_FILE" || { echo "Python main script failed"; exit 1; }

# Deactivate the virtual environment
deactivate

echo "Script executed successfully."
EOL

# Make the shell script executable
chmod +x "$CRON_SCRIPT_PATH"

# Step 10: Set Up Cron Job with flock to Prevent Multiple Instances
echo_info "Setting up cron job for automated script execution..."

# Define the cron job line with flock
CRON_JOB="1 * * * * /usr/bin/flock -n /tmp/run_auto_jobs.lock $CRON_SCRIPT_PATH >> $CRON_LOG 2>&1"

# Add the cron job if it doesn't already exist
(crontab -l 2>/dev/null | grep -Fv "$CRON_SCRIPT_PATH" ; echo "$CRON_JOB") | crontab -

echo_info "Cron job has been set up to run every hour with flock."

# Step 11: Create Resumes Directory and Instruct User to Add Resume
echo_info "Setting up resumes directory..."

# Create resumes directory if it doesn't exist
mkdir -p "$RESUME_DIR"

# Step 12: Final Instructions
echo_info ""
echo_info "========================================"
echo_info "      Installation and Setup Complete   "
echo_info "========================================"
echo_info "🚀 Next Steps 🚀"
echo_info "1. Place resume as '$RESUME_FILE' in: $RESUME_DIR"
echo_info "2. Review and update configuration files, config.yaml and plain_text_resume.yaml"
echo_info "3. Run the application manualy: ./run_auto_jobs.sh. Login at LinkedIn."
echo_info "4. Cron job executes hourly if you uncomment utils.py line 120."
echo_info "📂 Monitor logs at: $CRON_LOG"
echo_info "🔄 Activate virtual env: source $VENV_DIR/bin/activate"
echo_info "=== You're All Set! ==="

# Deactivate the virtual environment before exiting the script
deactivate
