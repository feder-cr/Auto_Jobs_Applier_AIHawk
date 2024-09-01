from webdriver_manager.core.driver import Driver
from webdriver_manager.core.logger import log


class OperaDriver(Driver):
    def __init__(
            self,
            name,
            driver_version,
            url,
            latest_release_url,
            opera_release_tag,
            http_client,
            os_system_manager
    ):
        super(OperaDriver, self).__init__(
            name,
            driver_version,
            url,
            latest_release_url,
            http_client,
            os_system_manager
        )
        self.opera_release_tag = opera_release_tag

    def get_latest_release_version(self) -> str:
        resp = self._http_client.get(
            url=self.latest_release_url,
            headers=self.auth_header
        )
        return resp.json()["tag_name"]

    def get_driver_download_url(self, os_type) -> str:
        """Like https://github.com/operasoftware/operachromiumdriver/releases/download/v.2.45/operadriver_linux64.zip"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest opera release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )
        assets = resp.json()["assets"]
        name = "{0}_{1}".format(self.get_name(), os_type)
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        return self.opera_release_tag.format(version)

    def get_browser_type(self):
        return "opera"
