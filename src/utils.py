import os
import random
import time

from selenium import webdriver

import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Отключаем логирование для selenium и urllib3
logging.getLogger("selenium.webdriver.remote.remote_connection").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


chromeProfilePath = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")

def ensure_chrome_profile():
    logger.debug("Ensuring Chrome profile exists at path: %s", chromeProfilePath)
    profile_dir = os.path.dirname(chromeProfilePath)
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
        logger.debug("Created directory for Chrome profile: %s", profile_dir)
    if not os.path.exists(chromeProfilePath):
        os.makedirs(chromeProfilePath)
        logger.debug("Created Chrome profile directory: %s", chromeProfilePath)
    return chromeProfilePath

def is_scrollable(element):
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    scrollable = int(scroll_height) > int(client_height)
    logger.debug("Element scrollable check: scrollHeight=%s, clientHeight=%s, scrollable=%s", scroll_height, client_height, scrollable)
    return scrollable

def scroll_slow(driver, scrollable_element, start=0, end=3600, step=300, reverse=False):
    logger.debug("Starting slow scroll: start=%d, end=%d, step=%d, reverse=%s", start, end, step, reverse)
    if reverse:
        start, end = end, start
        step = -step
    if step == 0:
        logger.error("Step value cannot be zero.")
        raise ValueError("Step cannot be zero.")

    max_scroll_height = int(scrollable_element.get_attribute("scrollHeight"))
    logger.debug("Max scroll height of the element: %d", max_scroll_height)

    if end > max_scroll_height:
        logger.warning("End value exceeds the scroll height. Adjusting end to %d", max_scroll_height)
        end = max_scroll_height

    script_scroll_to = "arguments[0].scrollTop = arguments[1];"
    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                logger.warning("The element is not scrollable.")
                print("The element is not scrollable.")
                return
            if (step > 0 and start >= end) or (step < 0 and start <= end):
                logger.warning("No scrolling will occur due to incorrect start/end values.")
                print("No scrolling will occur due to incorrect start/end values.")
                return        
            for position in range(start, end, step):
                try:
                    driver.execute_script(script_scroll_to, scrollable_element, position)
                    logger.debug("Scrolled to position: %d", position)
                except Exception as e:
                    logger.error("Error during scrolling: %s", e)
                    print(f"Error during scrolling: {e}")
                time.sleep(random.uniform(1.0, 1.6))
            driver.execute_script(script_scroll_to, scrollable_element, end)
            logger.debug("Scrolled to final position: %d", end)
            time.sleep(1)
        else:
            logger.warning("The element is not visible.")
            print("The element is not visible.")
    except Exception as e:
        logger.error("Exception occurred during scrolling: %s", e)
        print(f"Exception occurred: {e}")

def chromeBrowserOptions():
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
        initialPath = os.path.dirname(chromeProfilePath)
        profileDir = os.path.basename(chromeProfilePath)
        options.add_argument('--user-data-dir=' + initialPath)
        options.add_argument("--profile-directory=" + profileDir)
        logger.debug("Using Chrome profile directory: %s", chromeProfilePath)
    else:
        options.add_argument("--incognito")
        logger.debug("Using Chrome in incognito mode")

    return options

def printred(text):
    RED = "\033[91m"
    RESET = "\033[0m"
    logger.debug("Printing text in red: %s", text)
    print(f"{RED}{text}{RESET}")

def printyellow(text):
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    logger.debug("Printing text in yellow: %s", text)
    print(f"{YELLOW}{text}{RESET}")
