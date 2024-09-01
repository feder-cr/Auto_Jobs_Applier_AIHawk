import os
from typing import Optional

from webdriver_manager.core.download_manager import DownloadManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.core.os_manager import OperationSystemManager
from webdriver_manager.drivers.edge import EdgeChromiumDriver
from webdriver_manager.drivers.ie import IEDriver
from webdriver_manager.core.manager import DriverManager


class IEDriverManager(DriverManager):
    def __init__(
            self,
            version: Optional[str] = None,
            name: str = "IEDriverServer",
            url: str = "https://github.com/seleniumhq/selenium/releases/download",
            latest_release_url: str = "https://api.github.com/repos/seleniumhq/selenium/releases",
            ie_release_tag: str = "https://api.github.com/repos/seleniumhq/selenium/releases/tags/selenium-{0}",
            download_manager: Optional[DownloadManager] = None,
            cache_manager: Optional[DriverCacheManager] = None,
            os_system_manager: Optional[OperationSystemManager] = None
    ):
        super().__init__(
            download_manager=download_manager,
            cache_manager=cache_manager
        )

        self.driver = IEDriver(
            driver_version=version,
            name=name,
            url=url,
            latest_release_url=latest_release_url,
            ie_release_tag=ie_release_tag,
            http_client=self.http_client,
            os_system_manager=os_system_manager
        )

    def install(self) -> str:
        return self._get_driver_binary_path(self.driver)

    def get_os_type(self):
        return "x64" if self._os_system_manager.get_os_type() == "win64" else "Win32"


class EdgeChromiumDriverManager(DriverManager):
    def __init__(
            self,
            version: Optional[str] = None,
            name: str = "edgedriver",
            url: str = "https://msedgedriver.azureedge.net",
            latest_release_url: str = "https://msedgedriver.azureedge.net/LATEST_RELEASE",
            download_manager: Optional[DownloadManager] = None,
            cache_manager: Optional[DriverCacheManager] = None,
            os_system_manager: Optional[OperationSystemManager] = None
    ):
        super().__init__(
            download_manager=download_manager,
            cache_manager=cache_manager,
            os_system_manager=os_system_manager
        )

        self.driver = EdgeChromiumDriver(
            driver_version=version,
            name=name,
            url=url,
            latest_release_url=latest_release_url,
            http_client=self.http_client,
            os_system_manager=os_system_manager
        )

    def install(self) -> str:
        driver_path = self._get_driver_binary_path(self.driver)
        os.chmod(driver_path, 0o755)
        return driver_path
