from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

import os
import random
import sys
import time
import logging
from pathlib import Path
from selenium import webdriver
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

# Initialize Rich console for enhanced CLI output
console = Console()

def setup_logging(debug=True, suppress_stderr=False):
    """
    Set up logging configuration for the application.

    Args:
    debug (bool): If True, set log level to DEBUG. Otherwise, set to INFO.
    suppress_stderr (bool): If True, redirect stderr to /dev/null.

    Returns:
    logging.Logger: Configured logger object.
    """
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    if suppress_stderr:
        sys.stderr = open(os.devnull, 'w')
    
    return logger


def init_browser() -> webdriver.Chrome:
    """
    Initialize and return a Chrome WebDriver instance with custom options.

    Returns:
    webdriver.Chrome: Configured Chrome WebDriver instance.

    Raises:
    RuntimeError: If browser initialization fails.
    """
    try:
        options = chromeBrowserOptions()
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")


def clear_console():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def ensure_chrome_profile():
    """
    Ensure that the Chrome profile directory exists.

    Returns:
    str: Path to the Chrome profile directory.
    """
    chrome_profile_path = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")
    profile_dir = os.path.dirname(chrome_profile_path)
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    if not os.path.exists(chrome_profile_path):
        os.makedirs(chrome_profile_path)
    return chrome_profile_path

def chrome_browser_options():
    """
    Configure Chrome browser options for automation.

    Returns:
    webdriver.ChromeOptions: Configured Chrome options object.
    """
    options = webdriver.ChromeOptions()

    chrome_profile_path = ensure_chrome_profile()
    # Remove the incognito option
    # options.add_argument("--incognito")
    # options.add_argument("--disable-extensions")  # Disable browser extensions
    # options.add_argument("--disable-logging")  # Disable logging
    
    if len(chrome_profile_path) > 0:
        initialPath = os.path.dirname(chrome_profile_path)
        profileDir = os.path.basename(chrome_profile_path)
        options.add_argument('--user-data-dir=' + initialPath)
        options.add_argument("--profile-directory=" + profileDir)

    #     options.add_argument(f'--user-data-dir={os.path.dirname(chrome_profile_path)}')
    # options.add_argument(f"--profile-directory={os.path.basename(chrome_profile_path)}")

    else:
        options.add_argument("--incognito")


    
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # Launch the browser in full screen
    options.add_argument("--no-sandbox")  # Disable sandboxing to improve performance
    options.add_argument("--disable-dev-shm-usage")  # Use a temporary directory for shared memory
    options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("window-size=1200x800")  # Set the browser window size
    options.add_argument("--disable-background-timer-throttling")  # Disable background timer throttling
    options.add_argument("--disable-backgrounding-occluded-windows")  # Disable suspending occluded windows
    options.add_argument("--disable-translate")  # Disable automatic translation
    options.add_argument("--disable-popup-blocking")  # Disable popup blocking
    options.add_argument("--no-first-run")  # Disable initial browser setup
    options.add_argument("--no-default-browser-check")  # Disable default browser check
    # options.add_argument("--disable-autofill")  # Disable form autofill
    options.add_argument("--disable-plugins")  # Disable browser plugins
    options.add_argument("--disable-animations")  # Disable animations
    options.add_argument("--disable-cache")  # Disable cache
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # Exclude automation mode and logging switches

    # Content preferences
    prefs = {
        "profile.default_content_setting_values.images": 2,  # Disable image loading
        "profile.managed_default_content_settings.stylesheets": 2,  # Disable stylesheet loading
    }
    options.add_experimental_option("prefs", prefs)

    
    return options



def is_scrollable(element):
    """
    Check if a web element is scrollable.

    Args:
    element (WebElement): Selenium WebElement to check.

    Returns:
    bool: True if the element is scrollable, False otherwise.
    """
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    return int(scroll_height) > int(client_height)

def scroll_slow(driver, scrollable_element, start=0, end=3600, step=100, reverse=False):
    """
    Slowly scroll a web element.

    Args:
    driver (WebDriver): Selenium WebDriver instance.
    scrollable_element (WebElement): Element to scroll.
    start (int): Starting scroll position.
    end (int): Ending scroll position.
    step (int): Scroll step size.
    reverse (bool): If True, scroll in reverse direction.
    """
    if reverse:
        start, end = end, start
        step = -step
    if step == 0:
        raise ValueError("Step cannot be zero.")
    script_scroll_to = "arguments[0].scrollTop = arguments[1];"
    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                print("The element is not scrollable.")
                return
            if (step > 0 and start >= end) or (step < 0 and start <= end):
                print("No scrolling will occur due to incorrect start/end values.")
                return        
            for position in range(start, end, step):
                try:
                    driver.execute_script(script_scroll_to, scrollable_element, position)
                except Exception as e:
                    print(f"Error during scrolling: {e}")
                time.sleep(random.uniform(1.0, 2.6))
            driver.execute_script(script_scroll_to, scrollable_element, end)
            time.sleep(1)
        else:
            print("The element is not visible.")
    except Exception as e:
        print(f"Exception occurred: {e}")


def chromeBrowserOptions():
    """
    Configure advanced Chrome browser options for automation.

    Returns:
    webdriver.ChromeOptions: Configured Chrome options object with advanced settings.
    """
    chrome_profile_path = ensure_chrome_profile()
    options = webdriver.ChromeOptions()
    
    # Basic browser settings
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("window-size=1200x800")
    
    # Performance optimizations
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
    
    # Exclude automation-related switches
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    # Content preferences
    prefs = {
        "profile.default_content_setting_values.images": 2,  # Disable image loading
        "profile.managed_default_content_settings.stylesheets": 2,  # Disable stylesheet loading
    }
    options.add_experimental_option("prefs", prefs)

    # Set up user profile
    if chrome_profile_path:
        initial_path = os.path.dirname(chrome_profile_path)
        profile_dir = os.path.basename(chrome_profile_path)
        options.add_argument(f'--user-data-dir={initial_path}')
        options.add_argument(f"--profile-directory={profile_dir}")
    else:
        options.add_argument("--incognito")

    return options


def printred(text):
    """
    Print text in red color.

    Args:
    text (str): Text to be printed in red.
    """
    RED = "\033[91m"
    RESET = "\033[0m"
    print(f"{RED}{text}{RESET}")

def printyellow(text):
    """
    Print text in yellow color.

    Args:
    text (str): Text to be printed in yellow.
    """
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    print(f"{YELLOW}{text}{RESET}")