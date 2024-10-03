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
    """Utility function to determine if an element is scrollable."""
    try:
        scroll_height = int(element.get_attribute("scrollHeight"))
        client_height = int(element.get_attribute("clientHeight"))
        scrollable = scroll_height > client_height
        logger.debug(f"Element scrollable check: scrollHeight={scroll_height}, clientHeight={client_height}, scrollable={scrollable}")
        return scrollable
    except Exception as e:
        logger.error(f"Error determining scrollability: {e}")
        return False

def scroll_slow(driver, scrollable_element, start=0, end=3600, step=300, reverse=False, max_attempts=10):
    """
    Scrolls a scrollable element slowly to the end (bottom) or back to the top.

    :param driver: Selenium WebDriver instance.
    :param scrollable_element: The web element to scroll.
    :param start: Starting scroll position (ignored).
    :param end: Ending scroll position (ignored).
    :param step: Scroll step size in pixels.
    :param reverse: If True, scrolls upwards to the top; otherwise, scrolls downwards to the bottom.
    :param max_attempts: Maximum number of attempts to scroll without new content (for infinite scroll).
    """
    logger.debug("Starting scroll_slow.")

    if step <= 0:
        logger.error("Step value must be positive.")
        raise ValueError("Step must be positive.")

    if not is_scrollable(scrollable_element):
        logger.warning("The element is not scrollable.")
        return

    script_scroll_to = "arguments[0].scrollTop = arguments[1];"

    try:
        # Ensure the element is visible
        if not scrollable_element.is_displayed():
            logger.warning("The element is not visible. Attempting to scroll it into view.")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", scrollable_element)
                time.sleep(1)  # Wait for the element to become visible
                if not scrollable_element.is_displayed():
                    logger.error("The element is still not visible after attempting to scroll into view.")
                    return
                else:
                    logger.debug("Element is now visible after scrolling into view.")
            except Exception as e:
                logger.error(f"Failed to scroll the element into view: {e}")
                return

        # Determine initial scroll positions
        scroll_height = int(scrollable_element.get_attribute("scrollHeight"))
        client_height = int(scrollable_element.get_attribute("clientHeight"))
        max_scroll_position = scroll_height - client_height

        logger.debug(f"Scroll height: {scroll_height}, Client height: {client_height}, Max scroll position: {max_scroll_position}")

        # Set scrolling direction and end position based on 'reverse'
        if reverse:
            step = -abs(step)  # Ensure step is negative for upward scrolling
            end_position = 0
            logger.debug("Configured to scroll upwards to the top.")
        else:
            step = abs(step)   # Ensure step is positive for downward scrolling
            end_position = max_scroll_position
            logger.debug("Configured to scroll downwards to the bottom.")

        attempts = 0
        last_scroll_height = scroll_height

        current_scroll_position = int(float(scrollable_element.get_attribute("scrollTop") or 0))
        logger.debug(f"Initial scroll position: {current_scroll_position}")

        while True:
            if reverse:
                # Scrolling upwards
                new_scroll_position = current_scroll_position + step
                if new_scroll_position <= end_position:
                    new_scroll_position = end_position
            else:
                # Scrolling downwards
                new_scroll_position = current_scroll_position + step
                if new_scroll_position >= end_position:
                    new_scroll_position = end_position

            # Execute the scroll
            try:
                driver.execute_script(script_scroll_to, scrollable_element, new_scroll_position)
                logger.debug(f"Scrolled to position: {new_scroll_position}")
            except Exception as e:
                logger.error(f"Error during scrolling to position {new_scroll_position}: {e}")
                break

            time.sleep(random.uniform(0.2, 0.5))  # Adjusted sleep time for smoother scrolling

            # Update current scroll position
            try:
                current_scroll_position = int(float(scrollable_element.get_attribute("scrollTop") or 0))
                logger.debug(f"Current scrollTop after scrolling: {current_scroll_position}")
            except Exception as e:
                logger.error(f"Error fetching current scrollTop: {e}")
                break

            if reverse:
                # Check if we've reached the top
                if current_scroll_position <= end_position:
                    logger.debug("Reached the top of the element.")
                    break
            else:
                # For infinite scroll, detect if new content has loaded
                new_scroll_height = int(scrollable_element.get_attribute("scrollHeight") or 0)
                logger.debug(f"New scroll height: {new_scroll_height}")

                if new_scroll_height > last_scroll_height:
                    logger.debug("New content detected. Updating end_position.")
                    last_scroll_height = new_scroll_height
                    end_position = new_scroll_height - client_height
                    attempts = 0  # Reset attempts if new content is loaded
                else:
                    attempts += 1
                    logger.debug(f"No new content loaded. Attempt {attempts}/{max_attempts}.")
                    if attempts >= max_attempts:
                        logger.debug("Maximum scroll attempts reached. Ending scroll.")
                        break

                # Check if we've reached the bottom
                if current_scroll_position >= end_position:
                    logger.debug("Reached the bottom of the element.")
                    break

        # Ensure the final scroll position is correct
        try:
            driver.execute_script(script_scroll_to, scrollable_element, end_position)
            logger.debug(f"Scrolled to final position: {end_position}")
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error scrolling to final position {end_position}: {e}")

    except Exception as e:
        logger.error(f"Exception occurred during scrolling: {e}")

    logger.debug("Completed scroll_slow.")

def chrome_browser_options():
    logger.debug("Setting Chrome browser options")
    ensure_chrome_profile()
    options = webdriver.ChromeOptions()
    
    # Modo Headless
    # options.add_argument("--headless")
    
    # Especifica o caminho absoluto para o binário do Chrome
    options.binary_location = '/usr/bin/google-chrome'  # Atualize conforme necessário
    
    # Outras opções já existentes
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

    # Flags adicionais para estabilidade
    options.add_argument("--disable-setuid-sandbox")
    # options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-zygote")
    options.add_argument("--single-process")
    options.add_argument("--remote-debugging-port=9222")

    # Preferências para otimizar o carregamento
    prefs = {
        "profile.default_content_setting_values.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # Configuração do perfil do Chrome
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

def stringWidth(text, font, font_size):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]