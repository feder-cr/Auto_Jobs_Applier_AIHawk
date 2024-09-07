from webdriver_manager.core.driver import Driver
from webdriver_manager.core.logger import log


class IEDriver(Driver):

    def __init__(
            self,
            name,
            driver_version,
            url,
            latest_release_url,
            ie_release_tag,
            http_client,
            os_system_manager
    ):
        super(IEDriver, self).__init__(
            name,
            driver_version,
            url,
            latest_release_url,
            http_client,
            os_system_manager
        )
        self._ie_release_tag = ie_release_tag
        # todo: for 'browser_version' implement installed IE version detection
        #       like chrome or firefox

    def get_latest_release_version(self) -> str:
        log(f"Get LATEST driver version for Internet Explorer")
        resp = self._http_client.get(
            url=self.latest_release_url,
            headers=self.auth_header
        )

        releases = resp.json()
        release = next(
            release
            for release in releases
            for asset in release["assets"]
            if asset["name"].startswith(self.get_name())
        )
        return release["tag_name"].replace("selenium-", "")

    def get_driver_download_url(self, os_type):
        """Like https://github.com/seleniumhq/selenium/releases/download/3.141.59/IEDriverServer_Win32_3.141.59.zip"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest ie release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )

        assets = resp.json()["assets"]

        name = f"{self._name}_{os_type}_{driver_version_to_download}" + "."
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        version = self.__get_divided_version(version)
        return self._ie_release_tag.format(version)

    def __get_divided_version(self, version):
        divided_version = version.split(".")
        if len(divided_version) == 2:
            return f"{version}.0"
        elif len(divided_version) == 3:
            return version
        else:
            raise ValueError(
                "Version must consist of major, minor and/or patch, "
                "but given was: '{version}'".format(version=version)
            )

    def get_browser_type(self):
        return "msie"
