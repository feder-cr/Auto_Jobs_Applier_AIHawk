import atexit
import os
import random
import sys
import time
from selenium import webdriver
from loguru import logger
from app_config import LOG_CONFIG

from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

from constants import LOG_TO_CONSOLE, LOG_TO_FILE, MINIMUM_LOG_LEVEL
selenium_logger.setLevel(LOG_CONFIG[MINIMUM_LOG_LEVEL])

log_file = "log/app.log"

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Remove default logger
logger.remove()

# Add file logger if LOG_TO_FILE is True
if LOG_CONFIG[LOG_TO_FILE] :
    logger.add(
        log_file,
        level=LOG_CONFIG[MINIMUM_LOG_LEVEL],
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True
    )

# Add console logger if LOG_TO_CONSOLE is True
if LOG_CONFIG[LOG_TO_CONSOLE]:
    logger.add(
        sys.stderr,
        level=LOG_CONFIG[MINIMUM_LOG_LEVEL],
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True
    )


