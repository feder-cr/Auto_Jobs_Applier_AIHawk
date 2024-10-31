import os
import random
import sys
import time
from selenium import webdriver
from loguru import logger
from app_config import MINIMUM_LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE

from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger
selenium_logger.setLevel(MINIMUM_LOG_LEVEL)

log_file = "log/app.log"

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Remove default logger
logger.remove()

# Configure Loguru logger
config = {
    "handlers": []
}

# Add file logger if LOG_TO_FILE is True
if LOG_TO_FILE:
    config["handlers"].append({
        "sink": log_file,
        "level": MINIMUM_LOG_LEVEL,
        "rotation": "10 MB",
        "retention": "1 week",
        "compression": "zip",
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    })

# Add console logger if LOG_TO_CONSOLE is True
if LOG_TO_CONSOLE:
    config["handlers"].append({
        "sink": sys.stderr,
        "level": MINIMUM_LOG_LEVEL,
        "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    })

# Configure Loguru with the new settings
logger.configure(**config)

