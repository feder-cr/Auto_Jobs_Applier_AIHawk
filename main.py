import logging
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
from yaml.parser import ParserError
from yaml.scanner import ScannerError
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
import time

#setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("__name__")
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



console = Console()

import traceback

def create_and_run_bot(email: str, password: str, parameters: dict, llm_api_key: str):
    try:
        logger.info("Initializing StyleManager and ResumeGenerator")
        style_manager = StyleManager()
        resume_generator = ResumeGenerator()
        
        logger.info(f"Reading plain text resume from {parameters['uploads']['plainTextResume']}")
        with open(parameters['uploads']['plainTextResume'], "r", encoding='utf-8') as file:
            plain_text_resume = file.read()
        
        logger.info("Creating Resume object")
        resume_object = Resume(plain_text_resume)
        
        logger.info("Initializing FacadeManager")
        resume_generator_manager = FacadeManager(llm_api_key, style_manager, resume_generator, resume_object, Path("data_folder/output"))
        
        logger.debug("Clearing console")
        os.system('cls' if os.name == 'nt' else 'clear')
        
        logger.info("Choosing resume style")
        resume_generator_manager.choose_style()
        
        logger.debug("Clearing console")
        os.system('cls' if os.name == 'nt' else 'clear')
        
        logger.info("Creating JobApplicationProfile object")
        job_application_profile_object = JobApplicationProfile(plain_text_resume)
        
        logger.info("Initializing browser")
        browser = init_browser()
        
        logger.info("Creating LinkedInAuthenticator")
        login_component = LinkedInAuthenticator(browser)
        
        logger.info("Creating LinkedInJobManager")
        apply_component = LinkedInJobManager(browser)
        
        print("Initializing GPTAnswerer...")
        gpt_answerer_component = GPTAnswerer()
        print("GPTAnswerer initialized successfully.")
        
        logger.info("Creating LinkedInBotFacade")
        bot = LinkedInBotFacade(login_component, apply_component)
        bot.set_secrets(email, password)
        bot.set_job_application_profile_and_resume(job_application_profile_object, resume_object)
        bot.set_gpt_answerer_and_resume_generator(gpt_answerer_component, resume_generator_manager)
        print("GPTAnswerer and ResumeGenerator set in bot.")
        bot.set_parameters(parameters)

        console.print(Panel("LinkedIn Job Application Bot", style="bold green"))

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            login_task = progress.add_task("[cyan]Logging in...", total=1)
            bot.start_login()
            progress.update(login_task, completed=1)

            search_task = progress.add_task("[yellow]Searching for jobs...", total=100)
            logger.info("Attempting to search for jobs")
            jobs_found = bot.search_jobs()  # This is where the error occurs
            for i in range(100):
                time.sleep(0.1)
                progress.update(search_task, advance=1)
            
            application_task = progress.add_task(f"[green]Applying to jobs... (0/{len(jobs_found)})", total=len(jobs_found))
            for i, job in enumerate(jobs_found):
                console.print(f"[bold blue]Applying to job {i+1}/{len(jobs_found)}:[/bold blue] {job.title} at {job.company}")
                
                # Update progress description
                progress.update(application_task, description=f"[green]Applying to jobs... ({i+1}/{len(jobs_found)})")
                
                # Simulate steps in job application process
                steps = ["Analyzing job description", "Customizing resume", "Answering questions", "Submitting application"]
                for step in steps:
                    console.print(f"  [italic]{step}...[/italic]")
                    time.sleep(1)  # Simulate work being done
                
                # Update progress bar
                progress.update(application_task, advance=1)
                
                console.print(f"[bold green]Application submitted for {job.title}[/bold green]\n")

        console.print(Panel("Job application process completed!", style="bold blue"))

    except AttributeError as e:
        console.print(f"[bold red]AttributeError:[/bold red] {str(e)}")
        console.print("[yellow]This error suggests that the 'LinkedInBotFacade' class is missing the 'search_jobs' method.[/yellow]")
        console.print("[yellow]Please check the implementation of the LinkedInBotFacade class.[/yellow]")
        console.print("\n[bold]Traceback:[/bold]")
        console.print(traceback.format_exc())
    except WebDriverException as e:
        console.print(f"[bold red]WebDriver error occurred:[/bold red] {e}")
        console.print("\n[bold]Traceback:[/bold]")
        console.print(traceback.format_exc())
    except Exception as e:
        console.print(f"[bold red]Error running the bot:[/bold red] {str(e)}")
        console.print("\n[bold]Traceback:[/bold]")
        console.print(traceback.format_exc())
    finally:
        logger.info("Bot execution completed (with or without errors)")


def read_plain_text_resume(file_path: str) -> str:
    logger.debug(f"Attempting to read plain text resume from: {file_path}")
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            content = file.read()
        logger.debug(f"File contents read. Length: {len(content)} characters")
        return content
    except FileNotFoundError:
        logger.error(f"Plain text resume file not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"IO error when reading plain text resume: {str(e)}")
        raise

def create_resume_object(plain_text_resume: str) -> Resume:
    logger.debug("Creating Resume object...")
    try:
        resume_object = Resume(plain_text_resume)
        logger.debug("Resume object created successfully")
        return resume_object
    except (ParserError, ScannerError) as e:
        logger.error(f"YAML parsing error in plain text resume: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating Resume object: {str(e)}")
        raise

def clear_console():
    logger.debug("Clearing console...")
    os.system('cls' if os.name == 'nt' else 'clear')

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
        logger.error(f"Congiguration error: {str(ce)}")
        
        print("Refer to the configuration guide for troubleshooting: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {str(fnf)}")
        print("Ensure all required files are present in the data folder.")
        print("Refer to the file setup guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except RuntimeError as re:
        logger.error(f"Runtime error: {str(re)}")
        
        print("Refer to the configuration and troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        print("Refer to the general troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")

if __name__ == "__main__":
    main()
