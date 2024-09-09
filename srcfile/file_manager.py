from pathlib import Path
from typing import Optional, Tuple

class FileManager:
    @staticmethod
    def find_file(name_containing: str, with_extension: str, at_path: Path) -> Optional[Path]:
        try:
            return next(at_path.glob(f"*{name_containing}*.{with_extension}"))
        except StopIteration:
            return None

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> Tuple[bool, str]:
        if not app_data_folder.exists():
            return False, f"Data folder does not exist: {app_data_folder}"
        if not app_data_folder.is_dir():
            return False, f"Data folder path is not a directory: {app_data_folder}"
        required_files = ['secrets.yaml', 'config.yaml', 'plain_text_resume.yaml']
        missing_files = [file for file in required_files if not (app_data_folder / file).exists()]
        
        if missing_files:
            raise FileNotFoundError(f"Missing files in the data folder: {', '.join(missing_files)}")

        output_folder = app_data_folder / 'output'
        output_folder.mkdir(exist_ok=True)
        return (app_data_folder / 'secrets.yaml', app_data_folder / 'config.yaml', app_data_folder / 'plain_text_resume.yaml', output_folder)

    @staticmethod
    def file_paths_to_dict(resume_file: Path | None, plain_text_resume_file: Path) -> dict:
        if not plain_text_resume_file.exists():
            raise FileNotFoundError(f"Plain text resume file not found: {plain_text_resume_file}")

        result = {'plainTextResume': plain_text_resume_file}

        if resume_file:
            if not resume_file.exists():
                raise FileNotFoundError(f"Resume file not found: {resume_file}")
            result['resume'] = resume_file

        return result