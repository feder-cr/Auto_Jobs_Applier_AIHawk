from webdriver_manager.core.download_manager import WDMDownloadManager
from webdriver_manager.core.driver_cache import DriverCacheManager
from webdriver_manager.core.logger import log
from webdriver_manager.core.os_manager import OperationSystemManager


class DriverManager(object):
    def __init__(
            self,
            download_manager=None,
            cache_manager=None,
            os_system_manager=None
    ):
        self._cache_manager = cache_manager
        if not self._cache_manager:
            self._cache_manager = DriverCacheManager()

        self._download_manager = download_manager
        if self._download_manager is None:
            self._download_manager = WDMDownloadManager()

        self._os_system_manager = os_system_manager
        if not self._os_system_manager:
            self._os_system_manager = OperationSystemManager()
        log("====== WebDriver manager ======")

    @property
    def http_client(self):
        return self._download_manager.http_client

    def install(self) -> str:
        raise NotImplementedError("Please Implement this method")

    def _get_driver_binary_path(self, driver):
        binary_path = self._cache_manager.find_driver(driver)
        if binary_path:
            return binary_path

        os_type = self.get_os_type()
        file = self._download_manager.download_file(driver.get_driver_download_url(os_type))
        binary_path = self._cache_manager.save_file_to_cache(driver, file)
        return binary_path

    def get_os_type(self):
        return self._os_system_manager.get_os_type()
