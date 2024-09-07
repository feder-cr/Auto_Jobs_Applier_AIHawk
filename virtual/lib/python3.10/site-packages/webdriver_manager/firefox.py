import os
from typing import Optional

from webdriver_manager.core.download_manager import DownloadManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.core.manager import DriverManager
from webdriver_manager.core.os_manager import OperationSystemManager
from webdriver_manager.drivers.firefox import GeckoDriver


class GeckoDriverManager(DriverManager):
    def __init__(
            self,
            version: Optional[str] = None,
            name: str = "geckodriver",
            url: str = "https://github.com/mozilla/geckodriver/releases/download",
            latest_release_url: str = "https://api.github.com/repos/mozilla/geckodriver/releases/latest",
            mozila_release_tag: str = "https://api.github.com/repos/mozilla/geckodriver/releases/tags/{0}",
            download_manager: Optional[DownloadManager] = None,
            cache_manager: Optional[DriverCacheManager] = None,
            os_system_manager: Optional[OperationSystemManager] = None
    ):
        super(GeckoDriverManager, self).__init__(
            download_manager=download_manager,
            cache_manager=cache_manager
        )

        self.driver = GeckoDriver(
            driver_version=version,
            name=name,
            url=url,
            latest_release_url=latest_release_url,
            mozila_release_tag=mozila_release_tag,
            http_client=self.http_client,
            os_system_manager=os_system_manager
        )

    def install(self) -> str:
        driver_path = self._get_driver_binary_path(self.driver)
        os.chmod(driver_path, 0o755)
        return driver_path

    def get_os_type(self):
        os_type = super().get_os_type()
        if not self._os_system_manager.is_mac_os(os_type):
            return os_type

        macos = 'macos'
        if self._os_system_manager.is_arch(os_type):
            return f"{macos}-aarch64"
        return macos
