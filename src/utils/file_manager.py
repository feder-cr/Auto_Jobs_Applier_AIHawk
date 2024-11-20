import json
from pathlib import Path
from typing import Optional

import yaml

from constants import SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML
from src.logging import logger


class FileManager:
    """Class for handling file operations related to the application."""

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> tuple:
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

    @staticmethod
    def file_paths_to_dict(resume_file: Optional[Path], plain_text_resume_file: Path) -> dict:
        """
        Returns a dictionary containing paths to the resume and plain text resume files.
        """
        if not plain_text_resume_file.exists():
            raise FileNotFoundError(
                f"Plain text resume file not found: {plain_text_resume_file}"
            )

        result = {"plainTextResume": plain_text_resume_file}

        if resume_file:
            if not resume_file.exists():
                raise FileNotFoundError(f"Resume file not found: {resume_file}")
            result["resume"] = resume_file

        return result

    @staticmethod
    def read_secrets(secrets_path: Path) -> dict:
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

    @staticmethod
    def write_to_file(job, file_name, output_file_directory, reason=None, applicants_count=None):
        logger.debug(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.resume_path).resolve().as_uri() if job.resume_path else None
        data = {
            "company": job.company or "N/A",
            "job_title": job.title or "N/A",
            "link": job.link or "N/A",
            "job_recruiter": job.recruiter_link or "N/A",
            "job_location": job.location or "N/A",
            "pdf_path": pdf_path or "N/A",
            "reason": reason or "N/A"
        }

        if applicants_count is not None:
            data["applicants_count"] = applicants_count

        file_path = output_file_directory / f"{file_name}.json"
        temp_file_path = file_path.with_suffix('.tmp')

        try:
            if not file_path.exists():
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump([data], f, indent=4)
                temp_file_path.rename(file_path)
                logger.debug(f"Job data written to new file: {file_path}")
            else:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error in file: {file_path}. Creating a backup.")
                        file_path.rename(file_path.with_suffix('.bak'))
                        existing_data = []

                    existing_data.append(data)
                    f.seek(0)
                    json.dump(existing_data, f, indent=4)
                    f.truncate()
                    logger.debug(f"Job data appended to existing file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write data to file {file_path}: {e}")
