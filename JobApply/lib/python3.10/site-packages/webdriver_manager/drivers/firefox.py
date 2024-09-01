from webdriver_manager.core.driver import Driver
from webdriver_manager.core.logger import log


class GeckoDriver(Driver):
    def __init__(
            self,
            name,
            driver_version,
            url,
            latest_release_url,
            mozila_release_tag,
            http_client,
            os_system_manager
    ):
        super(GeckoDriver, self).__init__(
            name,
            driver_version,
            url,
            latest_release_url,
            http_client,
            os_system_manager,
        )
        self._mozila_release_tag = mozila_release_tag

    def get_latest_release_version(self) -> str:
        determined_browser_version = self.get_browser_version_from_os()
        log(f"Get LATEST {self._name} version for {determined_browser_version} firefox")
        resp = self._http_client.get(
            url=self.latest_release_url,
            headers=self.auth_header
        )
        return resp.json()["tag_name"]

    def get_driver_download_url(self, os_type):
        """Like https://github.com/mozilla/geckodriver/releases/download/v0.11.1/geckodriver-v0.11.1-linux64.tar.gz"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest mozilla release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )
        assets = resp.json()["assets"]
        name = f"{self.get_name()}-{driver_version_to_download}-{os_type}."
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        return self._mozila_release_tag.format(version)

    def get_browser_type(self):
        return "firefox"
