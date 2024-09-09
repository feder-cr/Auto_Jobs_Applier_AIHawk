import re
import yaml
from pathlib import Path

class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class ConfigValidator:
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate the format of an email address.
        
        Args:
            email (str): The email address to validate.
        
        Returns:
            bool: True if the email is valid, False otherwise.
        """
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    @staticmethod
    def validate_yaml_file(yaml_path: Path) -> dict:
        """
        Load and validate a YAML file.
        
        Args:
            yaml_path (Path): The path to the YAML file.
        
        Returns:
            dict: The parsed YAML content as a dictionary.
        
        Raises:
            ConfigError: If there's an error reading or parsing the YAML file.
        """
        try:
            with open(yaml_path, 'r') as file:
                return yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise ConfigError(f"Error parsing YAML file {yaml_path}: {str(e)}")
        except IOError as e:
            raise ConfigError(f"Error reading file {yaml_path}: {str(e)}")

    @staticmethod
    def validate_config(config_yaml_path: Path) -> dict:
        """
        Validate the main configuration file.
        
        Args:
            config_yaml_path (Path): The path to the configuration YAML file.
        
        Returns:
            dict: The validated configuration as a dictionary.
        
        Raises:
            ConfigError: If the configuration is invalid or missing required fields.
        """
        config= ConfigValidator.validate_yaml_file(config_yaml_path)
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
            if key not in config:
                if key in ['companyBlacklist', 'titleBlacklist']:
                    config[key] = []
                else:
                    raise ConfigError(f"Missing or invalid key '{key}' in config file {config_yaml_path}")
            elif not isinstance(config[key], expected_type):
                if key in ['companyBlacklist', 'titleBlacklist'] and config[key] is None:
                    config[key] = []
                else:
                    raise ConfigError(f"Invalid type for key '{key}' in config file {config_yaml_path}. Expected {expected_type}.")

        experience_levels = ['internship', 'entry', 'associate', 'mid-senior level', 'director', 'executive']
        for level in experience_levels:
            if not isinstance(config['experienceLevel'].get(level), bool):
                raise ConfigError(f"Experience level '{level}' must be a boolean in config file {config_yaml_path}")

        job_types = ['full-time', 'contract', 'part-time', 'temporary', 'internship', 'other', 'volunteer']
        for job_type in job_types:
            if not isinstance(config['jobTypes'].get(job_type), bool):
                raise ConfigError(f"Job type '{job_type}' must be a boolean in config file {config_yaml_path}")

        date_filters = ['all time', 'month', 'week', '24 hours']
        for date_filter in date_filters:
            if not isinstance(config['date'].get(date_filter), bool):
                raise ConfigError(f"Date filter '{date_filter}' must be a boolean in config file {config_yaml_path}")

        if not all(isinstance(pos, str) for pos in config['positions']):
            raise ConfigError(f"'positions' must be a list of strings in config file {config_yaml_path}")
        if not all(isinstance(loc, str) for loc in config['locations']):
            raise ConfigError(f"'locations' must be a list of strings in config file {config_yaml_path}")

        approved_distances = {0, 5, 10, 25, 50, 100}
        if config['distance'] not in approved_distances:
            raise ConfigError(f"Invalid distance value in config file {config_yaml_path}. Must be one of: {approved_distances}")

        for blacklist in ['companyBlacklist', 'titleBlacklist']:
            if not isinstance(config.get(blacklist), list):
                raise ConfigError(f"'{blacklist}' must be a list in config file {config_yaml_path}")
            if config[blacklist] is None:
                config[blacklist] = []

        return config



    @staticmethod
    def validate_secrets(secrets_yaml_path: Path) -> tuple:
        """
        Validate the secrets file containing LinkedIn credentials.
        
        Args:
            secrets_yaml_path (Path): The path to the secrets YAML file.
        
        Returns:
            tuple: A tuple containing the validated LinkedIn email and password.
        
        Raises:
            ConfigError: If the secrets are invalid or missing required fields.
        """
        secrets = ConfigValidator.validate_yaml_file(secrets_yaml_path)
        required_keys = ['email', 'password', 'openai_api_key']
        
        # Check for required keys
        for key in required_keys:
            if key not in secrets:
                raise ConfigError(f"Missing required key '{key}' in secrets file")
        
       
        if not ConfigValidator.validate_email(secrets['email']):
            raise ConfigError(f"Invalid email format: {secrets['email']}")
        if not secrets['openai_api_key']:
            raise ConfigError(f"OpenAI API key cannot be empty in secrets file {secrets_yaml_path}.")
        if not secrets['password']:
            raise ConfigError(f"Password cannot be empty in secrets file {secrets_yaml_path}.")

        return secrets['linkedin_email'], secrets['passwrod']