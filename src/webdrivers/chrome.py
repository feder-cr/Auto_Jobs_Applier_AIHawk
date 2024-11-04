import os
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from src.webdrivers.base_browser import Browser, BrowserType

chromeProfilePath = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")

class Chrome(Browser):
    """Chrome browser implementation"""
    browser_type: BrowserType = BrowserType.CHROME

    def create_options(self) -> webdriver.ChromeOptions:
        """Create Chrome-specific options"""
        self.profile.ensure_profile_exists()
        options = webdriver.ChromeOptions()

        chrome_arguments = [
            "--start-maximized", "--no-sandbox", "--disable-dev-shm-usage",
            "--ignore-certificate-errors", "--disable-extensions", "--disable-gpu",
            "window-size=1200x800", "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows", "--disable-translate",
            "--disable-popup-blocking", "--no-first-run", "--no-default-browser-check",
            "--disable-logging", "--disable-autofill", "--disable-plugins",
            "--disable-animations", "--disable-cache"
        ]

        for arg in chrome_arguments:
            options.add_argument(arg)

        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        prefs = {
            "profile.default_content_setting_values.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
        }
        options.add_experimental_option("prefs", prefs)

        if self.profile.profile_path:
            initial_path = os.path.dirname(self.profile.profile_path)
            profile_dir = os.path.basename(self.profile.profile_path)
            options.add_argument('--user-data-dir=' + initial_path)
            options.add_argument("--profile-directory=" + profile_dir)
            logger.debug(f"Using Chrome profile directory: {self.profile.profile_path}")
        else:
            options.add_argument("--incognito")
            logger.debug("Using Chrome in incognito mode")

        return options

    def create_service(self) -> ChromeService:
        """Create Chrome-specific service"""
        return ChromeService(ChromeDriverManager().install())

    def _create_driver_instance(self, service, options):
        """Create Chrome WebDriver instance"""
        return webdriver.Chrome(service=service, options=options)
