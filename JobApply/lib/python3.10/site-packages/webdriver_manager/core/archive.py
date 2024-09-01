import os
import zipfile


class LinuxZipFileWithPermissions(zipfile.ZipFile):
    """Class for extract files in linux with right permissions"""

    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)  # noqa
        attr = member.external_attr >> 16
        os.chmod(ret_val, attr)
        return ret_val


class Archive(object):
    def __init__(self, path: str):
        self.file_path = path
