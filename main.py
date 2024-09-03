import os
import re
import sys
from pathlib import Path
import yaml
import click
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException
from lib_resume_builder_AIHawk import Resume,StyleManager,FacadeManager,ResumeGenerator
from src.utils import chromeBrowserOptions
from src.gpt import GPTAnswerer
from src.linkedIn_authenticator import LinkedInAuthenticator
from src.linkedIn_bot_facade import LinkedInBotFacade
from src.linkedIn_job_manager import LinkedInJobManager
from src.job_application_profile import JobApplicationProfile

# Suppress stderr
sys.stderr = open(os.devnull, 'w')

class ConfigError(Exception):
    pass

class ConfigValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is not None
    
    @staticmethod
    def validate_yaml_file(yaml_path: Path) -> dict:
        try:
            with open(yaml_path, 'r') as stream:
                return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading file {yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"File not found: {yaml_path}")
    
    
    def validate_config(config_yaml_path: Path) -> dict:
        parameters = ConfigValidator.validate_yaml_file(config_yaml_path)
        required_keys = {
            'remote': bool,
            'experienceLevel': dict,
            'jobTypes': dict,
            'date': dict,
            'positions': list,
            'locations': list,
            'distance': int,
            'companyBlacklist': list,
            'titleBlacklist': list
        }

        for key, expected_type in required_keys.items():
            if key not in parameters:
                if key in ['companyBlacklist', 'titleBlacklist']:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Missing or invalid key '{key}' in config file {config_yaml_path}")
            elif not isinstance(parameters[key], expected_type):
                if key in ['companyBlacklist', 'titleBlacklist'] and parameters[key] is None:
                    parameters[key] = []
                else:
                    raise ConfigError(f"Invalid type for key '{key}' in config file {config_yaml_path}. Expected {expected_type}.")

        experience_levels = ['internship', 'entry', 'associate', 'mid-senior level', 'director', 'executive']
        for level in experience_levels:
            if not isinstance(parameters['experienceLevel'].get(level), bool):
                raise ConfigError(f"Experience level '{level}' must be a boolean in config file {config_yaml_path}")

        job_types = ['full-time', 'contract', 'part-time', 'temporary', 'internship', 'other', 'volunteer']
        for job_type in job_types:
            if not isinstance(parameters['jobTypes'].get(job_type), bool):
                raise ConfigError(f"Job type '{job_type}' must be a boolean in config file {config_yaml_path}")

        date_filters = ['all time', 'month', 'week', '24 hours']
        for date_filter in date_filters:
            if not isinstance(parameters['date'].get(date_filter), bool):
                raise ConfigError(f"Date filter '{date_filter}' must be a boolean in config file {config_yaml_path}")

        if not all(isinstance(pos, str) for pos in parameters['positions']):
            raise ConfigError(f"'positions' must be a list of strings in config file {config_yaml_path}")
        if not all(isinstance(loc, str) for loc in parameters['locations']):
            raise ConfigError(f"'locations' must be a list of strings in config file {config_yaml_path}")

        approved_distances = {0, 5, 10, 25, 50, 100}
        if parameters['distance'] not in approved_distances:
            raise ConfigError(f"Invalid distance value in config file {config_yaml_path}. Must be one of: {approved_distances}")

        for blacklist in ['companyBlacklist', 'titleBlacklist']:
            if not isinstance(parameters.get(blacklist), list):
                raise ConfigError(f"'{blacklist}' must be a list in config file {config_yaml_path}")
            if parameters[blacklist] is None:
                parameters[blacklist] = []

        return parameters



    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> tuple:
        secrets = ConfigValidator.validate_yaml_file(secrets_yaml_path)
        mandatory_secrets = ['email', 'password', 'openai_api_key']

        for secret in mandatory_secrets:
            if secret not in secrets:
                raise ConfigError(f"Missing secret '{secret}' in file {secrets_yaml_path}")

        if not ConfigValidator.validate_email(secrets['email']):
            raise ConfigError(f"Invalid email format in secrets file {secrets_yaml_path}.")
        if not secrets['password']:
            raise ConfigError(f"Password cannot be empty in secrets file {secrets_yaml_path}.")
        if not secrets['openai_api_key']:
            raise ConfigError(f"OpenAI API key cannot be empty in secrets file {secrets_yaml_path}.")

        return secrets['email'], str(secrets['password']), secrets['openai_api_key']

class FileManager:
    @staticmethod
    def find_file(name_containing: str, with_extension: str, at_path: Path) -> Path:
        return next((file for file in at_path.iterdir() if name_containing.lower() in file.name.lower() and file.suffix.lower() == with_extension.lower()), None)

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> tuple:
        if not app_data_folder.exists() or not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")

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

def init_browser() -> webdriver.Chrome:
    try:
        options = chromeBrowserOptions()
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")

def create_and_run_bot(email: str, password: str, parameters: dict, openai_api_key: str):
    try:
        style_manager = StyleManager()
        resume_generator = ResumeGenerator()
        with open(parameters['uploads']['plainTextResume'], "r", encoding='utf-8') as file:
            plain_text_resume = file.read()
        resume_object = Resume(plain_text_resume)
        resume_generator_manager = FacadeManager(openai_api_key, style_manager, resume_generator, resume_object, Path("data_folder/output"))
        os.system('cls' if os.name == 'nt' else 'clear')
        resume_generator_manager.choose_style()
        os.system('cls' if os.name == 'nt' else 'clear')
        
        job_application_profile_object = JobApplicationProfile(plain_text_resume)
        
        browser = init_browser()
        login_component = LinkedInAuthenticator(browser)
        apply_component = LinkedInJobManager(browser)
        gpt_answerer_component = GPTAnswerer(openai_api_key)
        bot = LinkedInBotFacade(login_component, apply_component)
        bot.set_secrets(email, password)
        bot.set_job_application_profile_and_resume(job_application_profile_object, resume_object)
        bot.set_gpt_answerer_and_resume_generator(gpt_answerer_component, resume_generator_manager)
        bot.set_parameters(parameters)
        bot.start_login()
        bot.start_apply()
    except WebDriverException as e:
        print(f"WebDriver error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"Error running the bot: {str(e)}")


@click.command()
@click.option('--resume', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path), help="Path to the resume PDF file")
def main(resume: Path = None):
    try:
        data_folder = Path("data_folder")
        secrets_file, config_file, plain_text_resume_file, output_folder = FileManager.validate_data_folder(data_folder)
        
        parameters = ConfigValidator.validate_config(config_file)
        email, password, openai_api_key = ConfigValidator.validate_secrets(secrets_file)
        
        parameters['uploads'] = FileManager.file_paths_to_dict(resume, plain_text_resume_file)
        parameters['outputFileDirectory'] = output_folder
        
        create_and_run_bot(email, password, parameters, openai_api_key)
    except ConfigError as ce:
        print(f"Configuration error: {str(ce)}")
        print("Refer to the configuration guide for troubleshooting: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except FileNotFoundError as fnf:
        print(f"File not found: {str(fnf)}")
        print("Ensure all required files are present in the data folder.")
        print("Refer to the file setup guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except RuntimeError as re:

        print(f"Runtime error: {str(re)}")

        print("Refer to the configuration and troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Refer to the general troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")

if __name__ == "__main__":
    main()
