import atexit
import os
import random
import sys
import time
from selenium import webdriver
from loguru import logger
from config import LOG_LEVEL, LOG_SELENIUM_LEVEL, LOG_TO_CONSOLE, LOG_TO_FILE

from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

selenium_logger.setLevel(LOG_SELENIUM_LEVEL)

def get_log_filename():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"log/app_{timestamp}.log"
  
log_file = get_log_filename()

# Ensure the log directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Remove default logger
logger.remove()

# Add file logger if LOG_TO_FILE is True
if LOG_TO_FILE:
    logger.add(
        log_file,
        level=LOG_LEVEL,
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )

# Add console logger if LOG_TO_CONSOLE is True
if LOG_TO_CONSOLE:
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=True,
        diagnose=True,
    )
