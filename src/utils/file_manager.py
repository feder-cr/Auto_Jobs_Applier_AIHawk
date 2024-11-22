import json
from pathlib import Path
from typing import Optional
import yaml
from config import ABBREVIATIONS
from constants import SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML
from src.logging import logger


class FileManager:
    """Class for handling file operations related to the application."""

    def __init__(self):
        self._json_cache = {}

    def validate_data_folder(self, app_data_folder: Path) -> tuple:
        """
        Validates that the required files exist in the data folder.
        """
        if not app_data_folder.exists() or not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")

        required_files = [SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML]
        missing_files = [file for file in required_files if not (app_data_folder / file).exists()]

        if missing_files:
            raise FileNotFoundError(
                f"Missing files in the data folder: {', '.join(missing_files)}"
            )

        output_folder = app_data_folder / "output"
        output_folder.mkdir(exist_ok=True)
        return (
            app_data_folder / SECRETS_YAML,
            app_data_folder / WORK_PREFERENCES_YAML,
            app_data_folder / PLAIN_TEXT_RESUME_YAML,
            output_folder,
        )

    def open_file(self, file_path: Path, mode: str = "r", encoding: Optional[str] = "utf-8"):
        """
        Opens a file and manages its file object in the FileManager.

        Args:
            file_path (Path): The path of the file to open.
            mode (str): The mode to open the file in.
            encoding (Optional[str]): Encoding to use.

        Returns:
            file object: Opened file object.
        """
        if file_path not in self._json_cache:
            self._json_cache[file_path] = open(file_path, mode, encoding=encoding)
        return self._json_cache[file_path]

    def close_all_files(self):
        """Closes all managed file objects."""
        for file_obj in self._json_cache.values():
            file_obj.close()
        self._json_cache.clear()

    def get_file_paths(self, resume_file: Optional[Path], plain_text_resume_file: Path) -> dict:
        """
        Returns a dictionary containing paths to the resume and plain text resume files.
        """
        if not plain_text_resume_file.exists():
            raise FileNotFoundError(
                f"Plain text resume file not found: {plain_text_resume_file}"
            )

        paths = {"plain_text_resume": plain_text_resume_file}

        if resume_file:
            if not resume_file.exists():
                raise FileNotFoundError(f"Resume file not found: {resume_file}")
            paths["resume"] = resume_file

        return paths

    def read_secrets(self, secrets_path: Path) -> dict:
        """
        Reads and validates the secrets file (YAML format) and ensures required keys are present.

        Args:
            secrets_path (Path): Path to the secrets YAML file.

        Returns:
            dict: Dictionary containing the secrets.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid YAML file or required keys are missing.
        """
        if not secrets_path.exists():
            raise FileNotFoundError(f"Secrets file not found: {secrets_path}")

        try:
            with open(secrets_path, "r", encoding="utf-8") as file:
                secrets_data = yaml.safe_load(file)

                # Ensure the secrets contain the required key for API
                required_keys = ["llm_api_key"]
                missing_keys = [key for key in required_keys if key not in secrets_data]
                if missing_keys:
                    raise ValueError(
                        f"Missing required keys in secrets file: {', '.join(missing_keys)}"
                    )

                # Handle optional keys with default behavior
                secrets_data["email"] = secrets_data.get("email", None)
                secrets_data["password"] = secrets_data.get("password", None)

                return secrets_data
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing secrets file {secrets_path}: {exc}")

    def write_to_file(self, job, file_name, output_file_directory, reason=None, applicants_count=None):
        logger.debug(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.resume_path).resolve().as_uri() if job.resume_path else None
        data = {
            "company": job.company or "N/A",
            "job_title": job.title or "N/A",
            "link": job.link or "N/A",
            "job_recruiter": job.recruiter_link or "N/A",
            "job_location": job.location or "N/A",
            "pdf_path": pdf_path or "N/A",
            "reason": reason or "N/A",
        }

        if applicants_count is not None:
            data["applicants_count"] = applicants_count

        file_path = output_file_directory / f"{file_name}.json"

        try:
            if file_path in self._json_cache:
                existing_data = json.load(self._json_cache[file_path])
            else:
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                else:
                    existing_data = []

            existing_data.append(data)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=4)
                logger.debug(f"Job data updated in file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to write data to file {file_path}: {e}")

    @staticmethod
    def apply_abbreviations(text):
        """
        Replaces words in the given text based on the ABBREVIATIONS dictionary.
        If a word is not found in the dictionary, it remains unchanged.

        Args:
            text (str): The input text to process.

        Returns:
            str: The text with abbreviations applied.
        """
        for full, abbrev in ABBREVIATIONS.items():
            if full in text:
                text = text.replace(full, abbrev)
        return text
