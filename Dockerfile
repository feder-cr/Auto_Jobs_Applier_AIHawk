# Dockerfile
FROM python:3.10-slim

# Install git and other necessary dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

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
