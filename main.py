"""

Exception Types Handled:

1. ConfigError:
   - Cause: Incorrect configuration settings.
   - Action: Logs the error and directs user to the configuration guide.

2. FileNotFoundError:
   - Cause: Required files missing from the data folder.
   - Action: Logs the missing file and prompts user to check the file setup guide.

3. RuntimeError:
   - Cause: Errors occurring during script execution.
   - Action: Logs the error and refers user to configuration and troubleshooting guide.

4. General Exception:
   - Cause: Any unexpected errors not covered by the above categories.
   - Action: Prints the error message and directs user to the general troubleshooting guide.

Usage:
This error handling block should be placed in the main execution flow of the script,
typically within a try-except block that wraps the core functionality.

Note for Contributors:
When adding new features or modifying existing ones, consider whether new exception
types need to be added to this section. Always provide clear, actionable feedback
to the user when an error occurs.
"""


import logging
import sys
from pathlib import Path
import click
import os

from srcfile.config_validator import ConfigValidator, ConfigError
from srcfile.file_manager import FileManager
from srcfile.bot_runner import create_and_run_bot
from srcfile.utils import setup_logging

logger = setup_logging(debug=True, suppress_stderr=False)


@click.command()
@click.option('--resume', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path), help="Path to the resume PDF file")
def main(resume: Path = None):
    try:
        # Set up directory paths
        script_dir = Path(__file__).parent
        data_folder = script_dir / "data_folder"
        
        # Validate data folder and get necessary file paths
        secrets_file, config_file, plain_text_resume_file, output_folder = FileManager.validate_data_folder(data_folder)
        
        # Validate configuration and secrets
        parameters = ConfigValidator.validate_config(config_file)
        email, password, openai_api_key = ConfigValidator.validate_secrets(secrets_file)
        
        # Prepare parameters for bot
        parameters['uploads'] = FileManager.file_paths_to_dict(resume, plain_text_resume_file)
        parameters['outputFileDirectory'] = output_folder
        
        # Run the bot with validated parameters
        create_and_run_bot(email, password, parameters, openai_api_key)

    except ConfigError as ce:
        # Handle configuration errors
        logger.error(f"Configuration error: {str(ce)}")
        print("Refer to the configuration guide for troubleshooting: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except FileNotFoundError as fnf:
        # Handle missing file errors
        logger.error(f"File not found: {str(fnf)}")
        print("Ensure all required files are present in the data folder.")
        print("Refer to the file setup guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except RuntimeError as re:
        # Handle runtime errors
        logger.error(f"Runtime error: {str(re)}")
        print("Refer to the configuration and troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")
    except Exception as e:
        # Handle unexpected errors
        print(f"An unexpected error occurred: {str(e)}")
        print("Refer to the general troubleshooting guide: https://github.com/feder-cr/LinkedIn_AIHawk_automatic_job_application/blob/main/readme.md#configuration")

if __name__ == "__main__":
    main()