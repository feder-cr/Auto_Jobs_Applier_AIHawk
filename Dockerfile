FROM python:3.10-slim

# Install necessary dependencies, including Chromium and Chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    git \
    chromium \
    chromium-driver \
    libx11-6 \
    libxrender1 \
    libxcomposite1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Ensure the target directory exists before creating the symlink
RUN mkdir -p /root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/
# Create a symlink for chromedriver
RUN ln -s /usr/bin/chromedriver /root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver.exe

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set environment variable to allow Python output to be displayed directly
ENV PYTHONUNBUFFERED=1

# The default command to run when the container starts
CMD ["bash"]
