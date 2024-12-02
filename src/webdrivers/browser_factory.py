from typing import Union

from selenium import webdriver
from loguru import logger

from config import BROWSER_TYPE_CONFIG
from src.webdrivers.browser_type import BrowserType


class BrowserFactory:
    """Factory class for creating browser instances"""
    _browser_type: BrowserType = BROWSER_TYPE_CONFIG
    @classmethod
    def get_browser_type(cls) -> BrowserType:
        """Get current browser type"""
        return cls._browser_type

    @classmethod
    def set_browser_type(cls, browser_type: BrowserType) -> None:
        """Set browser type"""
        # safety check additional to type check.
        if browser_type not in BrowserType:
            raise ValueError(f"Unsupported browser type: {browser_type}")
        cls._browser_type = browser_type
        logger.debug(f"Browser type set to: {browser_type}")

    @classmethod
    def get_browser(cls) -> Union[webdriver.Chrome, webdriver.Firefox]:
        """
        Create and return a WebDriver instance for the specified browser type
        Args:
            browser_type: BrowserType enum value
        Returns:
            WebDriver instance
        Raises:
            RuntimeError: If browser initialization fails
        """
        if cls._browser_type not in BrowserType:
            raise ValueError("Unsupported browser type: {cls._browser_type}")

        browser = cls._browser_type.value()

        return browser.create_driver()
