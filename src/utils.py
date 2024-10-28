import logging
import os
import random
import sys
import time

from selenium import webdriver
from loguru import logger

from app_config import MINIMUM_LOG_LEVEL

log_file = "app_log.log"


if MINIMUM_LOG_LEVEL in ["DEBUG", "TRACE", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    logger.remove()
    logger.add(sys.stderr, level=MINIMUM_LOG_LEVEL)
else:
    logger.warning(f"Invalid log level: {MINIMUM_LOG_LEVEL}. Defaulting to DEBUG.")
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

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
    """
    Improved smooth scrolling with adaptive speed and error recovery
    """
    SCROLL_CONFIGS = {
        'min_step': 10,
        'max_retries': 3,
        'retry_delay': 1.5,
        'scroll_delay': (0.6, 1.5)
    }

    def calculate_adaptive_step(current_step, progress):
        """Calculate adaptive step size based on scroll progress"""
        if progress < 0.2:  # Start slow
            return current_step * 0.8
        elif progress > 0.8:  # End slow
            return current_step * 0.6
        return current_step

    try:
        if not scrollable_element.is_displayed() or not is_scrollable(scrollable_element):
            logger.warning("Element is not scrollable or visible")
            return

        max_height = int(scrollable_element.get_attribute("scrollHeight"))
        current_pos = int(float(scrollable_element.get_attribute("scrollTop")))
        
        if reverse:
            start, end = end, start
            step = -abs(step)

        position = start
        total_distance = abs(end - start)
        retries = 0

        while (step > 0 and position < end) or (step < 0 and position > end):
            try:
                progress = abs(position - start) / total_distance
                adaptive_step = calculate_adaptive_step(step, progress)
                
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[1];", 
                    scrollable_element, 
                    position
                )
                
                new_pos = int(float(scrollable_element.get_attribute("scrollTop")))
                if new_pos == position:
                    retries += 1
                    if retries >= SCROLL_CONFIGS['max_retries']:
                        logger.warning("Scroll position stuck, breaking")
                        break
                else:
                    retries = 0

                position += adaptive_step
                time.sleep(random.uniform(*SCROLL_CONFIGS['scroll_delay']))

            except Exception as e:
                logger.error(f"Scroll error: {e}")
                time.sleep(SCROLL_CONFIGS['retry_delay'])
                retries += 1
                if retries >= SCROLL_CONFIGS['max_retries']:
                    raise

        # Final scroll to ensure target position
        driver.execute_script(
            "arguments[0].scrollTop = arguments[1];", 
            scrollable_element, 
            end
        )

    except Exception as e:
        logger.error(f"Fatal scroll error: {e}")
        raise


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
