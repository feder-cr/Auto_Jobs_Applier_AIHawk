import os

from loguru import logger
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

from src.webdrivers.base_browser import Browser, BrowserType

firefoxProfilePath = os.path.join(os.getcwd(), "firefox_profile", "linkedin_profile")

class Firefox(Browser):
    """Firefox browser implementation"""
    browser_type: BrowserType = BrowserType.FIREFOX

    def create_options(self) -> webdriver.FirefoxOptions:
        """Create Firefox-specific options"""
        self.profile.ensure_profile_exists()
        options = webdriver.FirefoxOptions()

        firefox_arguments = [
            "--start-maximized", "--no-sandbox", "--disable-dev-shm-usage",
            "--ignore-certificate-errors", "--disable-extensions", "--disable-gpu",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows", "--disable-translate",
            "--disable-popup-blocking", "--no-first-run", "--no-default-browser-check",
            "--disable-logging", "--disable-autofill", "--disable-plugins",
            "--disable-animations", "--disable-cache"
        ]

        for arg in firefox_arguments:
            options.add_argument(arg)

        prefs = {
            "permissions.default.image": 2,
            "permissions.default.stylesheet": 2,
        }
        for key, value in prefs.items():
            options.set_preference(key, value)

        if self.profile.profile_path:
            profile = webdriver.FirefoxProfile(self.profile.profile_path)
            options.profile = profile
            logger.debug(f"Using Firefox profile directory: {self.profile.profile_path}")
        else:
            options.set_preference("browser.privatebrowsing.autostart", True)
            logger.debug("Using Firefox in private browsing mode")

        return options

    def create_service(self) -> FirefoxService:
        """Create Firefox-specific service"""
        return FirefoxService(GeckoDriverManager().install())

    def _create_driver_instance(self, service, options):
        """Create Firefox WebDriver instance"""
        return webdriver.Firefox(service=service, options=options)
