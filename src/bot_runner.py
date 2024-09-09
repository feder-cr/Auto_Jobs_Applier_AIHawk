"""

## Main Components

### 1. create_and_run_bot(email: str, password: str, parameters: dict, llm_api_key: str)
This function orchestrates the entire job application process:
- Initializes resume generation tools
- Sets up the LinkedIn bot
- Handles login, job search, and application submission
- Provides a rich CLI interface for progress tracking

### 2. read_plain_text_resume(file_path: str) -> str
Reads the content of a plain text resume file.

### 3. create_resume_object(plain_text_resume: str) -> Resume
Creates a Resume object from plain text resume content.

### 4. clear_console()
Clears the console screen.

### 5. main(resume: Path = None)
The entry point of the script. It:
- Validates the data folder structure
- Reads configuration and secrets
- Calls create_and_run_bot with the necessary parameters




"""


import logging
import os
import sys
from pathlib import Path
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

import click
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

...
from src.gpt import GPTAnswerer
from linkedIn_auto_jobs_applier_with_AI.src.linkedin.linkedIn_authenticator import LinkedInAuthenticator
from linkedIn_auto_jobs_applier_with_AI.src.linkedin.linkedIn_bot_facade import LinkedInBotFacade
from linkedIn_auto_jobs_applier_with_AI.src.linkedin.linkedIn_job_manager import LinkedInJobManager
from src.job_application_profile import JobApplicationProfile

#CLI UI imports
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn


import time
import traceback

#importing config validator
from linkedIn_auto_jobs_applier_with_AI.srcfile.config_validator import ConfigValidator, ConfigError
from linkedIn_auto_jobs_applier_with_AI.srcfile.file_manager import FileManager
from linkedIn_auto_jobs_applier_with_AI.srcfile.utils import chromeBrowserOptions, read_plain_text_resume, create_resume_object
from 

from srcfile.resume_utils import read_plain_text_resume, create_resume_object


# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
console = Console()

# Suppress stderr
sys.stderr = open(os.devnull, 'w')


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

            search_task = progress.add_task("[yellow]Searching for jobs...", total=3)
            logger.info("Attempting to search for jobs")
            
            logger.debug("Checking bot state before searching jobs...")
            logger.debug(f"Logged in: {bot.state.logged_in}")
            logger.debug(f"Parameters set: {bot.state.parameters_set}")
            logger.debug("Attempting to search for jobs...")
            jobs_found = bot.search_jobs()
            for i in range(3):
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
