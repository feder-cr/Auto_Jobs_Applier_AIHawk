import os
import re
import sys
from pathlib import Path
import yaml
import click
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from typing import Optional
from constants import PLAIN_TEXT_RESUME_YAML, SECRETS_YAML, WORK_PREFERENCES_YAML
from lib_resume_builder_AIHawk import (
    Resume,
    FacadeManager,
    ResumeGenerator,
    StyleManager,
)

from src.ai_hawk.authenticator import get_authenticator
from src.ai_hawk.bot_facade import AIHawkBotFacade
from src.ai_hawk.job_manager import AIHawkJobManager
from src.ai_hawk.llm.llm_manager import GPTAnswerer
from src.utils.chrome_utils import chrome_browser_options
from src.job_application_profile import JobApplicationProfile
from src.logging import logger

# Suppress stderr only during specific operations
original_stderr = sys.stderr

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).resolve().parent / "src"))



class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


class ConfigValidator:
    """Class for validating configuration and secrets files."""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validates an email address using a regex pattern."""
        return (
            re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email)
            is not None
        )

    @staticmethod
    def validate_yaml_file(yaml_path: Path) -> dict:
        """Validates and loads a YAML file."""
        try:
            with open(yaml_path, "r", encoding="utf-8") as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"File not found: {yaml_path}")

    @staticmethod
    def validate_config(config_yaml_path: Path) -> dict:
        """
        Validates the configuration file to ensure all required keys are present
        and have the correct types.
        """
        logger.info(f"Loading and validating config file: {config_yaml_path}")
        parameters = ConfigValidator.validate_yaml_file(config_yaml_path)
        logger.debug(f"Loaded config file content: {parameters}")

        required_keys = {
            "remote": bool,
            "experience_level": dict,
            "job_types": dict,
            "date": dict,
            "positions": list,
            "locations": list,
            "location_blacklist": list,
            "distance": int,
            "company_blacklist": list,
            "title_blacklist": list,
            "llm_model_type": str,
            "llm_model": str,
        }

        for key, expected_type in required_keys.items():
            if key not in parameters:
                if key in [
                    "company_blacklist",
                    "title_blacklist",
                    "location_blacklist",
                ]:
                    parameters[key] = []
                    logger.debug(f"Optional key '{key}' missing, set to empty list.")
                else:
                    logger.error(f"Missing key '{key}' in config file.")
                    raise ConfigError(
                        f"Missing or invalid key '{key}' in config file {config_yaml_path}"
                    )
            elif not isinstance(parameters[key], expected_type):
                if (
                    key in ["company_blacklist", "title_blacklist", "location_blacklist"]
                    and parameters[key] is None
                ):
                    parameters[key] = []
                    logger.debug(f"Key '{key}' was None, set to empty list.")
                else:
                    logger.error(
                        f"Invalid type for key '{key}' in config file. Expected {expected_type}, but got {type(parameters[key])}."
                    )
                    raise ConfigError(
                        f"Invalid type for key '{key}' in config file {config_yaml_path}. Expected {expected_type}, but got {type(parameters[key])}."
                    )

        # Validate experience levels
        experience_levels = [
            "internship",
            "entry",
            "associate",
            "mid_senior_level",
            "director",
            "executive",
        ]
        for level in experience_levels:
            if not isinstance(parameters["experience_level"].get(level), bool):
                logger.error(
                    f"Invalid value for experience level '{level}'. Expected a boolean (True/False)."
                )
                raise ConfigError(
                    f"Experience level '{level}' must be a boolean in config file {config_yaml_path}"
                )

        # Validate job types
        job_types = [
            "full_time",
            "contract",
            "part_time",
            "temporary",
            "internship",
            "other",
            "volunteer",
        ]
        for job_type in job_types:
            if not isinstance(parameters["job_types"].get(job_type), bool):
                logger.error(
                    f"Invalid value for job type '{job_type}'. Expected a boolean (True/False)."
                )
                raise ConfigError(
                    f"Job type '{job_type}' must be a boolean in config file {config_yaml_path}"
                )

        # Validate date filters
        date_filters = ["all_time", "month", "week", "24_hours"]
        for date_filter in date_filters:
            if not isinstance(parameters["date"].get(date_filter), bool):
                logger.error(
                    f"Invalid value for date filter '{date_filter}'. Expected a boolean (True/False)."
                )
                raise ConfigError(
                    f"Date filter '{date_filter}' must be a boolean in config file {config_yaml_path}"
                )

        # Validate positions and locations
        if not all(isinstance(pos, str) for pos in parameters["positions"]):
            logger.error(
                f"Invalid value in 'positions'. All entries must be strings."
            )
            raise ConfigError(
                f"'positions' must be a list of strings in config file {config_yaml_path}"
            )
        if not all(isinstance(loc, str) for loc in parameters["locations"]):
            logger.error(
                f"Invalid value in 'locations'. All entries must be strings."
            )
            raise ConfigError(
                f"'locations' must be a list of strings in config file {config_yaml_path}"
            )

        # Validate distance
        approved_distances = {0, 5, 10, 25, 50, 100}
        if parameters["distance"] not in approved_distances:
            logger.error(
                f"Invalid distance value '{parameters['distance']}'. Must be one of {approved_distances}."
            )
            raise ConfigError(
                f"Invalid distance value in config file {config_yaml_path}. Must be one of: {approved_distances}"
            )

        # Ensure blacklists are lists
        for blacklist in ["company_blacklist", "title_blacklist", "location_blacklist"]:
            if not isinstance(parameters.get(blacklist), list):
                raise ConfigError(
                    f"'{blacklist}' must be a list in config file {config_yaml_path}"
                )
            if parameters[blacklist] is None:
                parameters[blacklist] = []

        logger.info("Configuration validated successfully.")
        return parameters

    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> tuple:
        """
        Validates the secrets file to ensure required keys are present and valid.
        """
        secrets = ConfigValidator.validate_yaml_file(secrets_yaml_path)
        mandatory_secrets = ["email", "password", "llm_api_key"]

        for secret in mandatory_secrets:
            if secret not in secrets:
                raise ConfigError(
                    f"Missing secret '{secret}' in file {secrets_yaml_path}"
                )

        if not ConfigValidator.validate_email(secrets["email"]):
            raise ConfigError(
                f"Invalid email format in secrets file {secrets_yaml_path}."
            )
        if not secrets["password"]:
            raise ConfigError(
                f"Password cannot be empty in secrets file {secrets_yaml_path}."
            )
        if not secrets["llm_api_key"]:
            raise ConfigError(
                f"llm_api_key cannot be empty in secrets file {secrets_yaml_path}."
            )
        return secrets["email"], str(secrets["password"]), secrets["llm_api_key"]


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
        return (app_data_folder / SECRETS_YAML, app_data_folder / WORK_PREFERENCES_YAML, app_data_folder / PLAIN_TEXT_RESUME_YAML, output_folder,)

    @staticmethod
    def file_paths_to_dict(
        resume_file: Optional[Path], plain_text_resume_file: Path
    ) -> dict:
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


def init_browser() -> webdriver.Chrome:
    """Initializes the Chrome browser with specified options."""
    try:
        options = chrome_browser_options()
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")


def create_and_run_bot(email, password, parameters, llm_api_key):
    """
    Initializes and runs the AIHawk bot with the provided parameters.
    """
    try:
        logger.info("Starting bot initialization...")

        # Initialize style manager and resume generator
        style_manager = StyleManager()
        resume_generator = ResumeGenerator()

        # Read plain text resume
        logger.info("Reading plain text resume file...")
        with open(
            parameters["uploads"]["plainTextResume"], "r", encoding="utf-8"
        ) as file:
            plain_text_resume = file.read()

        # Create resume object
        resume_object = Resume(plain_text_resume)

        # Create FacadeManager for resume generation
        resume_generator_manager = FacadeManager(
            llm_api_key,
            style_manager,
            resume_generator,
            resume_object,
            Path("data_folder/output"),
        )

        # If resume PDF is not provided, generate one
        if "resume" not in parameters["uploads"]:
            logger.info("No resume PDF provided. Generating resume...")
            resume_generator_manager.choose_style()

        # Create JobApplicationProfile object
        job_application_profile_object = JobApplicationProfile(plain_text_resume)

        # Initialize the browser
        logger.info("Initializing the browser...")
        browser = init_browser()

        # Initialize login component
        login_component = get_authenticator(driver=browser, platform="linkedin")

        # Initialize job application component
        apply_component = AIHawkJobManager(browser)

        # Initialize GPT Answerer component
        gpt_answerer_component = GPTAnswerer(parameters, llm_api_key)

        # Create AIHawkBotFacade object
        bot = AIHawkBotFacade(login_component, apply_component)

        # Set secrets, job application profile, resume, and parameters
        bot.set_secrets(email, password)
        bot.set_job_application_profile_and_resume(
            job_application_profile_object, resume_object
        )
        bot.set_gpt_answerer_and_resume_generator(
            gpt_answerer_component, resume_generator_manager
        )
        bot.set_parameters(parameters)

        # Start login process
        logger.info("Starting bot login process...")
        bot.start_login()

        # Determine operation mode
        if parameters.get("collectMode", False):
            logger.info("Collecting job data...")
            bot.start_collect_data()
        else:
            logger.info("Applying to jobs...")
            bot.start_apply()

    except WebDriverException as e:
        logger.error(f"WebDriver error occurred: {e}")
    except Exception as e:
        logger.error("An unexpected error occurred in create_and_run_bot:")
        logger.exception(e)
        raise RuntimeError(f"Error running the bot: {str(e)}")


@click.command()
@click.option(
    "--resume",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to the resume PDF file",
)
@click.option(
    "--collect",
    is_flag=True,
    help="Only collects job information into data.json file",
)
def main(collect: bool = False, resume: Optional[Path] = None):
    """
    Main function to execute the bot. Parses command-line options and starts the bot.
    """
    try:
        data_folder = Path("data_folder")
        (
            secrets_file,
            config_file,
            plain_text_resume_file,
            output_folder,
        ) = FileManager.validate_data_folder(data_folder)

        parameters = ConfigValidator.validate_config(config_file)
        email, password, llm_api_key = ConfigValidator.validate_secrets(secrets_file)

        parameters["uploads"] = FileManager.file_paths_to_dict(
            resume, plain_text_resume_file
        )
        parameters["outputFileDirectory"] = output_folder
        parameters["collectMode"] = collect

        create_and_run_bot(email, password, parameters, llm_api_key)
    except ConfigError as ce:
        logger.error(f"Configuration error: {str(ce)}")
        logger.error(
            "Refer to the configuration guide for troubleshooting: "
            "https://github.com/feder-cr/Auto_Jobs_Applier_AIHawk?tab=readme-ov-file#configuration"
        )
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {str(fnf)}")
        logger.error("Ensure all required files are present in the data folder.")
    except RuntimeError as re:
        logger.error(f"Runtime error: {str(re)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    main()
