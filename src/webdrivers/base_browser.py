import os

from abc import ABC, abstractmethod
from enum import Enum
from loguru import logger


class BrowserType(Enum):
    """Enum for supported browser types"""
    CHROME = 'chrome'
    FIREFOX = 'firefox'

class BrowserProfile:
    """Manages browser profile creation and configuration"""
    def __init__(self, browser_type: BrowserType):
        self.browser_type: BrowserType = browser_type.name.lower()
        self.profile_path = os.path.join(
            os.getcwd(),
            f"{self.browser_type}_profile",
            "linkedin_profile"
        )

    def ensure_profile_exists(self) -> str:
        """
        Ensures the browser profile directory exists
        Returns: Path to the profile directory
        """
        logger.debug(f"Ensuring {self.browser_type} profile exists at path: {self.profile_path}")
        profile_dir = os.path.dirname(self.profile_path)

        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
            logger.debug(f"Created directory for {self.browser_type} profile: {profile_dir}")

        if not os.path.exists(self.profile_path):
            os.makedirs(self.profile_path)
            logger.debug(f"Created {self.browser_type} profile directory: {self.profile_path}")

        return self.profile_path

class Browser(ABC):
    """Abstract base class for browser implementations"""
    def __init__(self):
        self.profile = BrowserProfile(self.browser_type)

    @property
    def browser_type(self) -> str:
        """Return the browser type identifier"""
        return self.__class__.browser_type

    @abstractmethod
    def create_options(self):
        """Create and return browser-specific options"""

    @abstractmethod
    def create_service(self):
        """Create and return browser-specific service"""

    def create_driver(self):
        """Create and return browser-specific WebDriver instance"""
        try:
            options = self.create_options()
            service = self.create_service()
            driver = self._create_driver_instance(service, options)
            logger.debug(f"{self.browser_type} WebDriver instance created successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to create {self.browser_type} WebDriver: {e}")
            raise RuntimeError(f"Failed to initialize {self.browser_type} browser: {str(e)}")

    @abstractmethod
    def _create_driver_instance(self, service, options):
        """Create the specific driver instance"""
