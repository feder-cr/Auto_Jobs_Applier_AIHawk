from webdriver_manager.core.logger import log
from webdriver_manager.core.config import gh_token
from webdriver_manager.core.os_manager import OperationSystemManager


class Driver(object):
    def __init__(
            self,
            name,
            driver_version_to_download,
            url,
            latest_release_url,
            http_client,
            os_system_manager):
        self._name = name
        self._url = url
        self._latest_release_url = latest_release_url
        self._http_client = http_client
        self._browser_version = None
        self._driver_version_to_download = driver_version_to_download
        self._os_system_manager = os_system_manager
        if not self._os_system_manager:
            self._os_system_manager = OperationSystemManager()

    @property
    def auth_header(self):
        token = gh_token()
        if token:
            log("GH_TOKEN will be used to perform requests")
            return {"Authorization": f"token {token}"}
        return None

    def get_name(self):
        return self._name

    def get_driver_download_url(self, os_type):
        return f"{self._url}/{self.get_driver_version_to_download()}/{self._name}_{os_type}.zip"

    def get_driver_version_to_download(self):
        """
        Downloads version from parameter if version not None or "latest".
        Downloads latest, if version is "latest" or browser could not been determined.
        Downloads determined browser version driver in all other ways as a bonus fallback for lazy users.
        """
        if self._driver_version_to_download:
            return self._driver_version_to_download

        return self.get_latest_release_version()

    def get_latest_release_version(self):
        # type: () -> str
        raise NotImplementedError("Please implement this method")

    def get_browser_version_from_os(self):
        """
        Use-cases:
        - for key in metadata;
        - for printing nice logs;
        - for fallback if version was not set at all.
        Note: the fallback may have collisions in user cases when previous browser was not uninstalled properly.
        """
        if self._browser_version is None:
            self._browser_version = self._os_system_manager.get_browser_version_from_os(self.get_browser_type())
        return self._browser_version

    def get_browser_type(self):
        raise NotImplementedError("Please implement this method")

    def get_binary_name(self, os_type):
        driver_name = self.get_name()
        driver_binary_name = (
            "msedgedriver" if driver_name == "edgedriver" else driver_name
        )
        driver_binary_name = (
            f"{driver_binary_name}.exe" if "win" in os_type else driver_binary_name
        )
        return driver_binary_name
