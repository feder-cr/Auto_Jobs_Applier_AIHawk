from enum import Enum

from src.webdrivers.chrome import Chrome
from src.webdrivers.firefox import Firefox


class BrowserType(Enum):
    """Enum for supported browser types"""
    CHROME = Chrome
    FIREFOX = Firefox
