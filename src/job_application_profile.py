from dataclasses import dataclass

import yaml

from src.utils import logger


@dataclass
class SelfIdentification:
    gender: str
    pronouns: str
    veteran: str
    disability: str
    ethnicity: str


@dataclass
class LegalAuthorization:
    eu_work_authorization: str
    us_work_authorization: str
    requires_us_visa: str
    legally_allowed_to_work_in_us: str
    requires_us_sponsorship: str
    requires_eu_visa: str
    legally_allowed_to_work_in_eu: str
    requires_eu_sponsorship: str


@dataclass
class WorkPreferences:
    remote_work: str
    in_person_work: str
    open_to_relocation: str
    willing_to_complete_assessments: str
    willing_to_undergo_drug_tests: str
    willing_to_undergo_background_checks: str


@dataclass
class Availability:
    notice_period: str


@dataclass
class SalaryExpectations:
    salary_range_usd: str


@dataclass
class JobApplicationProfile:
    self_identification: SelfIdentification
    legal_authorization: LegalAuthorization
    work_preferences: WorkPreferences
    availability: Availability
    salary_expectations: SalaryExpectations

    def __init__(self, yaml_str: str):
        logger.debug("Initializing JobApplicationProfile with provided YAML string")
        try:
            data = yaml.safe_load(yaml_str)
            logger.debug("YAML data successfully parsed: %s", data)
        except yaml.YAMLError as e:
            logger.error("Error parsing YAML file: %s", e)
            raise ValueError("Error parsing YAML file.") from e
        except Exception as e:
            logger.error("Unexpected error occurred while parsing the YAML file: %s", e)
            raise RuntimeError("An unexpected error occurred while parsing the YAML file.") from e

        if not isinstance(data, dict):
            logger.error("YAML data must be a dictionary, received: %s", type(data))
            raise TypeError("YAML data must be a dictionary.")

        # Process self_identification
        try:
            logger.debug("Processing self_identification")
            self.self_identification = SelfIdentification(**data['self_identification'])
            logger.debug("self_identification processed: %s", self.self_identification)
        except KeyError as e:
            logger.error("Required field %s is missing in self_identification data.", e)
            raise KeyError(f"Required field {e} is missing in self_identification data.") from e
        except TypeError as e:
            logger.error("Error in self_identification data: %s", e)
            raise TypeError(f"Error in self_identification data: {e}") from e
        except AttributeError as e:
            logger.error("Attribute error in self_identification processing: %s", e)
            raise AttributeError("Attribute error in self_identification processing.") from e
        except Exception as e:
            logger.error("An unexpected error occurred while processing self_identification: %s", e)
            raise RuntimeError("An unexpected error occurred while processing self_identification.") from e

        # Process legal_authorization
        try:
            logger.debug("Processing legal_authorization")
            self.legal_authorization = LegalAuthorization(**data['legal_authorization'])
            logger.debug("legal_authorization processed: %s", self.legal_authorization)
        except KeyError as e:
            logger.error("Required field %s is missing in legal_authorization data.", e)
            raise KeyError(f"Required field {e} is missing in legal_authorization data.") from e
        except TypeError as e:
            logger.error("Error in legal_authorization data: %s", e)
            raise TypeError(f"Error in legal_authorization data: {e}") from e
        except AttributeError as e:
            logger.error("Attribute error in legal_authorization processing: %s", e)
            raise AttributeError("Attribute error in legal_authorization processing.") from e
        except Exception as e:
            logger.error("An unexpected error occurred while processing legal_authorization: %s", e)
            raise RuntimeError("An unexpected error occurred while processing legal_authorization.") from e

        # Process work_preferences
        try:
            logger.debug("Processing work_preferences")
            self.work_preferences = WorkPreferences(**data['work_preferences'])
            logger.debug("work_preferences processed: %s", self.work_preferences)
        except KeyError as e:
            logger.error("Required field %s is missing in work_preferences data.", e)
            raise KeyError(f"Required field {e} is missing in work_preferences data.") from e
        except TypeError as e:
            logger.error("Error in work_preferences data: %s", e)
            raise TypeError(f"Error in work_preferences data: {e}") from e
        except AttributeError as e:
            logger.error("Attribute error in work_preferences processing: %s", e)
            raise AttributeError("Attribute error in work_preferences processing.") from e
        except Exception as e:
            logger.error("An unexpected error occurred while processing work_preferences: %s", e)
            raise RuntimeError("An unexpected error occurred while processing work_preferences.") from e

        # Process availability
        try:
            logger.debug("Processing availability")
            self.availability = Availability(**data['availability'])
            logger.debug("availability processed: %s", self.availability)
        except KeyError as e:
            logger.error("Required field %s is missing in availability data.", e)
            raise KeyError(f"Required field {e} is missing in availability data.") from e
        except TypeError as e:
            logger.error("Error in availability data: %s", e)
            raise TypeError(f"Error in availability data: {e}") from e
        except AttributeError as e:
            logger.error("Attribute error in availability processing: %s", e)
            raise AttributeError("Attribute error in availability processing.") from e
        except Exception as e:
            logger.error("An unexpected error occurred while processing availability: %s", e)
            raise RuntimeError("An unexpected error occurred while processing availability.") from e

        # Process salary_expectations
        try:
            logger.debug("Processing salary_expectations")
            self.salary_expectations = SalaryExpectations(**data['salary_expectations'])
            logger.debug("salary_expectations processed: %s", self.salary_expectations)
        except KeyError as e:
            logger.error("Required field %s is missing in salary_expectations data.", e)
            raise KeyError(f"Required field {e} is missing in salary_expectations data.") from e
        except TypeError as e:
            logger.error("Error in salary_expectations data: %s", e)
            raise TypeError(f"Error in salary_expectations data: {e}") from e
        except AttributeError as e:
            logger.error("Attribute error in salary_expectations processing: %s", e)
            raise AttributeError("Attribute error in salary_expectations processing.") from e
        except Exception as e:
            logger.error("An unexpected error occurred while processing salary_expectations: %s", e)
            raise RuntimeError("An unexpected error occurred while processing salary_expectations.") from e

        logger.debug("JobApplicationProfile initialization completed successfully.")

    def __str__(self):
        logger.debug("Generating string representation of JobApplicationProfile")

        def format_dataclass(obj):
            return "\n".join(f"{field.name}: {getattr(obj, field.name)}" for field in obj.__dataclass_fields__.values())

        formatted_str = (f"Self Identification:\n{format_dataclass(self.self_identification)}\n\n"
                         f"Legal Authorization:\n{format_dataclass(self.legal_authorization)}\n\n"
                         f"Work Preferences:\n{format_dataclass(self.work_preferences)}\n\n"
                         f"Availability: {self.availability.notice_period}\n\n"
                         f"Salary Expectations: {self.salary_expectations.salary_range_usd}\n\n")
        logger.debug("String representation generated: %s", formatted_str)
        return formatted_str
