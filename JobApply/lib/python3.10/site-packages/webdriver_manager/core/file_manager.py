import os
import re
import tarfile
import zipfile

from webdriver_manager.core.archive import Archive, LinuxZipFileWithPermissions
from webdriver_manager.core.os_manager import OperationSystemManager


class File(object):
    def __init__(self, stream, file_name):
        self.content = stream.content
        self.__stream = stream
        self.file_name = file_name
        self.__temp_name = "driver"
        self.__regex_filename = r"""filename.+"(.+)"|filename.+''(.+)|filename=([\w.-]+)"""

    @property
    def filename(self) -> str:
        if self.file_name:
            return self.file_name
        try:
            content = self.__stream.headers["content-disposition"]

            content_disposition_list = re.split(";", content)
            filenames = [re.findall(self.__regex_filename, element) for element in content_disposition_list]
            filename = next(filter(None, next(filter(None, next(filter(None, filenames))))))
        except KeyError:
            filename = f"{self.__temp_name}.zip"
        except (IndexError, StopIteration):
            filename = f"{self.__temp_name}.exe"

        if '"' in filename:
            filename = filename.replace('"', "")

        return filename


class FileManager(object):

    def __init__(self, os_system_manager: OperationSystemManager):
        self._os_system_manager = os_system_manager

    def save_archive_file(self, file: File, directory: str):
        os.makedirs(directory, exist_ok=True)

        archive_path = f"{directory}{os.sep}{file.filename}"
        with open(archive_path, "wb") as code:
            code.write(file.content)
        if not os.path.exists(archive_path):
            raise FileExistsError(f"No file has been saved on such path {archive_path}")
        return Archive(archive_path)

    def unpack_archive(self, archive_file: Archive, target_dir):
        file_path = archive_file.file_path
        if file_path.endswith(".zip"):
            return self.__extract_zip(archive_file, target_dir)
        elif file_path.endswith(".tar.gz"):
            return self.__extract_tar_file(archive_file, target_dir)

    def __extract_zip(self, archive_file, to_directory):
        zip_class = (LinuxZipFileWithPermissions if self._os_system_manager.get_os_name() == "linux" else zipfile.ZipFile)
        archive = zip_class(archive_file.file_path)
        try:
            archive.extractall(to_directory)
        except Exception as e:
            if e.args[0] not in [26, 13] and e.args[1] not in [
                "Text file busy",
                "Permission denied",
            ]:
                raise e
            file_names = []
            for n in archive.namelist():
                if "/" not in n:
                    file_names.append(n)
                else:
                    file_path, file_name = n.split("/")
                    full_file_path = os.path.join(to_directory, file_path)
                    source = os.path.join(full_file_path, file_name)
                    destination = os.path.join(to_directory, file_name)
                    os.replace(source, destination)
                    file_names.append(file_name)
            return sorted(file_names, key=lambda x: x.lower())
        return archive.namelist()

    def __extract_tar_file(self, archive_file, to_directory):
        try:
            tar = tarfile.open(archive_file.file_path, mode="r:gz")
        except tarfile.ReadError:
            tar = tarfile.open(archive_file.file_path, mode="r:bz2")
        members = tar.getmembers()
        tar.extractall(to_directory)
        tar.close()
        return [x.name for x in members]
