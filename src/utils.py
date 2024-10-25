import os
import random
import sys
import time
import queue
import threading
from selenium import webdriver
from loguru import logger

from app_config import MINIMUM_LOG_LEVEL, LOG_TO_FILE, LOG_TO_CONSOLE

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

# Define log_queue before the log_worker function
log_queue = queue.Queue()

# Worker function to process log messages
def log_worker():
    while True:
        record = log_queue.get()
        if record is None:
            break
        with open(log_file, "a") as log_file_handle:
            print(record, file=log_file_handle)
        if LOG_TO_CONSOLE:
            print(record, file=sys.stderr)

# Start the log worker thread
log_thread = threading.Thread(target=log_worker, daemon=True)
log_thread.start()

# Intercept Selenium's logging
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger
selenium_logger.setLevel(MINIMUM_LOG_LEVEL)

chromeProfilePath = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")

def ensure_chrome_profile():
    logger.debug(f"Ensuring Chrome profile exists at path: {chromeProfilePath}")
    profile_dir = os.path.dirname(chromeProfilePath)
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        logger.debug(f"Created directory for Chrome profile: {profile_dir}")
    if not os.path.exists(chromeProfilePath):
        os.makedirs(chromeProfilePath)
        logger.debug(f"Created Chrome profile directory: {chromeProfilePath}")
    return chromeProfilePath


def is_scrollable(element):
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    scrollable = int(scroll_height) > int(client_height)
    logger.debug(f"Element scrollable check: scrollHeight={scroll_height}, clientHeight={client_height}, scrollable={scrollable}")
    return scrollable


def scroll_slow(driver, scrollable_element, start=0, end=3600, step=300, reverse=False):
    logger.debug(f"Starting slow scroll: start={start}, end={end}, step={step}, reverse={reverse}")

    if reverse:
        start, end = end, start
        step = -step

    if step == 0:
        logger.error("Step value cannot be zero.")
        raise ValueError("Step cannot be zero.")

    max_scroll_height = int(scrollable_element.get_attribute("scrollHeight"))
    current_scroll_position = int(float(scrollable_element.get_attribute("scrollTop")))
    logger.debug(f"Max scroll height of the element: {max_scroll_height}")
    logger.debug(f"Current scroll position: {current_scroll_position}")

    if reverse:
        if current_scroll_position < start:
            start = current_scroll_position
        logger.debug(f"Adjusted start position for upward scroll: {start}")
    else:
        if end > max_scroll_height:
            logger.warning(f"End value exceeds the scroll height. Adjusting end to {max_scroll_height}")
            end = max_scroll_height

    script_scroll_to = "arguments[0].scrollTop = arguments[1];"

    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                logger.warning("The element is not scrollable.")
                return

            if (step > 0 and start >= end) or (step < 0 and start <= end):
                logger.warning("No scrolling will occur due to incorrect start/end values.")
                return

            position = start
            previous_position = None  # Tracking the previous position to avoid duplicate scrolls
            while (step > 0 and position < end) or (step < 0 and position > end):
                if position == previous_position:
                    # Avoid re-scrolling to the same position
                    logger.debug(f"Stopping scroll as position hasn't changed: {position}")
                    break

                try:
                    driver.execute_script(script_scroll_to, scrollable_element, position)
                    logger.debug(f"Scrolled to position: {position}")
                except Exception as e:
                    logger.error(f"Error during scrolling: {e}")

                previous_position = position
                position += step

                # Decrease the step but ensure it doesn't reverse direction
                step = max(10, abs(step) - 10) * (-1 if reverse else 1)

                time.sleep(random.uniform(0.6, 1.5))

            # Ensure the final scroll position is correct
            driver.execute_script(script_scroll_to, scrollable_element, end)
            logger.debug(f"Scrolled to final position: {end}")
            time.sleep(0.5)
        else:
            logger.warning("The element is not visible.")
    except Exception as e:
        logger.error(f"Exception occurred during scrolling: {e}")


def chrome_browser_options():
    logger.debug("Setting Chrome browser options")
    ensure_chrome_profile()
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1200x800")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-autofill")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-animations")
    options.add_argument("--disable-cache")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    prefs = {
        "profile.default_content_setting_values.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    if len(chromeProfilePath) > 0:
        initial_path = os.path.dirname(chromeProfilePath)
        profile_dir = os.path.basename(chromeProfilePath)
        options.add_argument('--user-data-dir=' + initial_path)
        options.add_argument("--profile-directory=" + profile_dir)
        logger.debug(f"Using Chrome profile directory: {chromeProfilePath}")
    else:
        options.add_argument("--incognito")
        logger.debug("Using Chrome in incognito mode")

    return options


def printred(text):
    red = "\033[91m"
    reset = "\033[0m"
    logger.debug("Printing text in red: %s", text)
    print(f"{red}{text}{reset}")


def printyellow(text):
    yellow = "\033[93m"
    reset = "\033[0m"
    logger.debug("Printing text in yellow: %s", text)
    print(f"{yellow}{text}{reset}")

# Make sure to add this at the end of your main script
def cleanup():
    log_queue.put(None)
    log_thread.join()

# Register the cleanup function to be called at exit
import atexit
atexit.register(cleanup)
