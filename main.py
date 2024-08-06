import re
from pathlib import Path
import yaml
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import click

from utils import chromeBrowserOptions
from gpt import GPTAnswerer
from linkedIn_authenticator import LinkedInAuthenticator
from linkedIn_bot_facade import LinkedInBotFacade
from linkedIn_job_manager import LinkedInJobManager
from resume import Resume

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class ConfigValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
    
    @staticmethod
    def validate_config(config_yaml_path: Path) -> dict:
        try:
            with open(config_yaml_path, 'r') as stream:
                parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading config file {config_yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"Config file not found: {config_yaml_path}")
        

        # Validate 'remote'
        if 'remote' not in parameters or not isinstance(parameters['remote'], bool):
            raise ConfigError(f"'remote' in config file {config_yaml_path} must be a boolean value.")

        # Validate 'experienceLevel'
        experience_level = parameters.get('experienceLevel', {})
        valid_experience_levels = [
            'internship', 'entry', 'associate', 'mid-senior level', 'director', 'executive'
        ]
        for level in valid_experience_levels:
            if level not in experience_level or not isinstance(experience_level[level], bool):
                raise ConfigError(f"Experience level '{level}' must be a boolean value in config file {config_yaml_path}.")

        # Validate 'jobTypes'
        job_types = parameters.get('jobTypes', {})
        valid_job_types = [
            'full-time', 'contract', 'part-time', 'temporary', 'internship', 'other', 'volunteer'
        ]
        for job_type in valid_job_types:
            if job_type not in job_types or not isinstance(job_types[job_type], bool):
                raise ConfigError(f"Job type '{job_type}' must be a boolean value in config file {config_yaml_path}.")

        # Validate 'date'
        date = parameters.get('date', {})
        valid_dates = ['all time', 'month', 'week', '24 hours']
        for date_filter in valid_dates:
            if date_filter not in date or not isinstance(date[date_filter], bool):
                raise ConfigError(f"Date filter '{date_filter}' must be a boolean value in config file {config_yaml_path}.")

        # Validate 'positions'
        positions = parameters.get('positions', [])
        if not isinstance(positions, list) or not all(isinstance(pos, str) for pos in positions):
            raise ConfigError(f"'positions' must be a list of strings in config file {config_yaml_path}.")
        
        # Validate 'locations'
        locations = parameters.get('locations', [])
        if not isinstance(locations, list) or not all(isinstance(loc, str) for loc in locations):
            raise ConfigError(f"'locations' must be a list of strings in config file {config_yaml_path}.")

        # Validate 'distance'
        approved_distances = {0, 5, 10, 25, 50, 100}
        distance = parameters.get('distance')
        if distance not in approved_distances:
            raise ConfigError(f"Invalid distance value in config file {config_yaml_path}. Must be one of: {approved_distances}")

        # Validate 'companyBlacklist'
        company_blacklist = parameters.get('companyBlacklist', [])
        if not isinstance(company_blacklist, list) or not all(isinstance(comp, str) for comp in company_blacklist):
            company_blacklist = []
        parameters['companyBlacklist'] = company_blacklist

        # Validate 'titleBlacklist'
        title_blacklist = parameters.get('titleBlacklist', [])
        if not isinstance(title_blacklist, list) or not all(isinstance(word, str) for word in title_blacklist):
            title_blacklist = []
        parameters['titleBlacklist'] = title_blacklist
        return parameters

    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> tuple:
        try:
            with open(secrets_yaml_path, 'r') as stream:
                secrets = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Error reading secrets file {secrets_yaml_path}: {exc}")
        except FileNotFoundError:
            raise ConfigError(f"Secrets file not found: {secrets_yaml_path}")

        mandatory_secrets = ['email', 'password', 'openai_api_key']

        for secret in mandatory_secrets:
            if secret not in secrets:
                raise ConfigError(f"Missing secret in file {secrets_yaml_path}: {secret}")
           
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
        for file in at_path.iterdir():
            if name_containing.lower() in file.name.lower() and file.suffix.lower() == with_extension.lower():
                return file
        return None

    @staticmethod
    def validate_data_folder(app_data_folder: Path) -> tuple:
        if not app_data_folder.exists() or not app_data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {app_data_folder}")

        secrets_file = app_data_folder / 'secrets.yaml'
        config_file = app_data_folder / 'config.yaml'
        plain_text_resume_file = app_data_folder / 'plain_text_resume.yaml'
        
        missing_files = []
        if not config_file.exists():
            missing_files.append('config.yaml')
        if not plain_text_resume_file.exists():
            missing_files.append('plain_text_resume.yaml')
        
        if missing_files:
            raise FileNotFoundError(f"Missing files in the data folder: {', '.join(missing_files)}")
        
        output_folder = app_data_folder / 'output'
        output_folder.mkdir(exist_ok=True)
        return secrets_file, config_file, plain_text_resume_file, output_folder

    @staticmethod
    def file_paths_to_dict(resume_file: Path | None, plain_text_resume_file: Path) -> dict:
        if not plain_text_resume_file.exists():
            raise FileNotFoundError(f"Plain text resume file not found: {plain_text_resume_file}")
        
        result = {'plainTextResume': plain_text_resume_file}
        
        if resume_file is not None:
            if not resume_file.exists():
                raise FileNotFoundError(f"Resume file not found: {resume_file}")
            result['resume'] = resume_file
        
        return result

def init_browser():
    try:
        options = chromeBrowserOptions()
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize browser: {str(e)}")

def create_and_run_bot(email: str, password: str, parameters: dict, openai_api_key: str):
    try:
        browser = init_browser()
        login_component = LinkedInAuthenticator(browser)
        apply_component = LinkedInJobManager(browser)
        gpt_answerer_component = GPTAnswerer(openai_api_key)

        with open(parameters['uploads']['plainTextResume'], "r") as file:
            plain_text_resume_file = file.read()
        
        resume_object = Resume(plain_text_resume_file)
        bot = LinkedInBotFacade(login_component, apply_component)
        bot.set_secrets(email, password)
        bot.set_resume(resume_object)
        bot.set_gpt_answerer(gpt_answerer_component)
        bot.set_parameters(parameters)
        bot.start_login()
        bot.start_apply()
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
        print("Check browser setup and other runtime issues.")
        print("Refer to the configuration and troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Refer to the general troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")

if __name__ == "__main__":
    main()
