import os
import traceback
import undetected_chromedriver as uc
from src.logging import logger

# Define the default Chrome profile path
DEFAULT_CHROME_PROFILE_DIR = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")


def ensure_chrome_profile(profile_path: str) -> str:
    """
    Ensures the Chrome profile directory exists.
    If it does not exist, it is created.

    :param profile_path: Path to the Chrome profile directory.
    :return: The validated Chrome profile path.
    """
    logger.debug(f"Ensuring Chrome profile exists at path: {profile_path}")
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        logger.debug(f"Created Chrome profile directory: {profile_path}")
    return profile_path


def chrome_browser_options(profile_path: str = DEFAULT_CHROME_PROFILE_DIR, headless: bool = False, proxy: str = None):
    """
    Sets up Chrome browser options for undetected ChromeDriver.

    :param profile_path: Path to the Chrome user profile directory.
    :param headless: Whether to run Chrome in headless mode.
    :param proxy: Proxy server address (e.g., "http://<proxy_ip>:<proxy_port>").
    :return: Configured ChromeOptions object.
    """
    logger.debug("Configuring Chrome browser options...")
    ensure_chrome_profile(profile_path)

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1200x800")
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

    # Optional: Headless mode
    if headless:
        options.add_argument("--headless=new")
        logger.debug("Running Chrome in headless mode.")

    # Optional: Proxy support
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
        logger.debug(f"Using proxy: {proxy}")

    # Optimize for performance by disabling images and stylesheets
    prefs = {
        "profile.default_content_setting_values.images": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # Use Chrome profile if specified
    if profile_path:
        initial_path = os.path.dirname(profile_path)
        profile_dir = os.path.basename(profile_path)
        options.add_argument(f'--user-data-dir={initial_path}')
        options.add_argument(f"--profile-directory={profile_dir}")
        logger.debug(f"Using Chrome profile directory: {profile_path}")
    else:
        options.add_argument("--incognito")
        logger.debug("Using Chrome in incognito mode.")

    return options


def init_browser(profile_path: str = DEFAULT_CHROME_PROFILE_DIR, headless: bool = False, proxy: str = None) -> uc.Chrome:
    """
    Initializes and returns a Chrome browser instance with the specified options.

    :param profile_path: Path to the Chrome user profile directory.
    :param headless: Whether to run Chrome in headless mode.
    :param proxy: Proxy server address (e.g., "http://<proxy_ip>:<proxy_port>").
    :return: A configured Chrome browser instance.
    """
    try:
        options = chrome_browser_options(profile_path=profile_path, headless=headless, proxy=proxy)
        browser = uc.Chrome(options=options)
        logger.info("Chrome browser initialized successfully.")
        return browser
    except Exception as e:
        logger.error(f"Failed to initialize browser: {traceback.format_exc()}")
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")


# Example usage
if __name__ == "__main__":
    try:
        # Initialize the browser with the desired configuration
        browser = init_browser(headless=False, proxy=None)
        logger.info("Browser is ready to use.")
        browser.get("https://www.linkedin.com")
    except RuntimeError as e:
        logger.error(f"Browser setup failed: {e}")
