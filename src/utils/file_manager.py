import yaml
from pathlib import Path
from typing import Optional
from constants import SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML


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
