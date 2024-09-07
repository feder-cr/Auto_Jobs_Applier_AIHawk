import os
from typing import Optional

from webdriver_manager.core.download_manager import DownloadManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.core.manager import DriverManager
from webdriver_manager.core.os_manager import OperationSystemManager
from webdriver_manager.drivers.opera import OperaDriver


class OperaDriverManager(DriverManager):
    def __init__(
            self,
            version: Optional[str] = None,
            name: str = "operadriver",
            url: str = "https://github.com/operasoftware/operachromiumdriver/"
                       "releases/",
            latest_release_url: str = "https://api.github.com/repos/"
                                      "operasoftware/operachromiumdriver/releases/latest",
            opera_release_tag: str = "https://api.github.com/repos/"
                                     "operasoftware/operachromiumdriver/releases/tags/{0}",
            download_manager: Optional[DownloadManager] = None,
            cache_manager: Optional[DriverCacheManager] = None,
            os_system_manager: Optional[OperationSystemManager] = None
    ):
        super().__init__(
            download_manager=download_manager,
            cache_manager=cache_manager
        )

        self.driver = OperaDriver(
            name=name,
            driver_version=version,
            url=url,
            latest_release_url=latest_release_url,
            opera_release_tag=opera_release_tag,
            http_client=self.http_client,
            os_system_manager=os_system_manager
        )

    def install(self) -> str:
        driver_path = self._get_driver_binary_path(self.driver)
        if not os.path.isfile(driver_path):
            for name in os.listdir(driver_path):
                if "sha512_sum" in name:
                    os.remove(os.path.join(driver_path, name))
                    break
        driver_path = os.path.join(driver_path, os.listdir(driver_path)[0])
        os.chmod(driver_path, 0o755)
        return driver_path
