from dataclasses import dataclass
from typing import Dict, List
import yaml

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
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise ValueError("Error parsing YAML file.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while parsing the YAML file.") from e

        if not isinstance(data, dict):
            raise TypeError("YAML data must be a dictionary.")

        # Process self_identification
        try:
            self.self_identification = SelfIdentification(**data['self_identification'])
        except KeyError as e:
            raise KeyError(f"Required field {e} is missing in self_identification data.") from e
        except TypeError as e:
            raise TypeError(f"Error in self_identification data: {e}") from e
        except AttributeError as e:
            raise AttributeError("Attribute error in self_identification processing.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while processing self_identification.") from e

        # Process legal_authorization
        try:
            self.legal_authorization = LegalAuthorization(**data['legal_authorization'])
        except KeyError as e:
            raise KeyError(f"Required field {e} is missing in legal_authorization data.") from e
        except TypeError as e:
            raise TypeError(f"Error in legal_authorization data: {e}") from e
        except AttributeError as e:
            raise AttributeError("Attribute error in legal_authorization processing.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while processing legal_authorization.") from e

        # Process work_preferences
        try:
            self.work_preferences = WorkPreferences(**data['work_preferences'])
        except KeyError as e:
            raise KeyError(f"Required field {e} is missing in work_preferences data.") from e
        except TypeError as e:
            raise TypeError(f"Error in work_preferences data: {e}") from e
        except AttributeError as e:
            raise AttributeError("Attribute error in work_preferences processing.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while processing work_preferences.") from e

        # Process availability
        try:
            self.availability = Availability(**data['availability'])
        except KeyError as e:
            raise KeyError(f"Required field {e} is missing in availability data.") from e
        except TypeError as e:
            raise TypeError(f"Error in availability data: {e}") from e
        except AttributeError as e:
            raise AttributeError("Attribute error in availability processing.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while processing availability.") from e

        # Process salary_expectations
        try:
            self.salary_expectations = SalaryExpectations(**data['salary_expectations'])
        except KeyError as e:
            raise KeyError(f"Required field {e} is missing in salary_expectations data.") from e
        except TypeError as e:
            raise TypeError(f"Error in salary_expectations data: {e}") from e
        except AttributeError as e:
            raise AttributeError("Attribute error in salary_expectations processing.") from e
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while processing salary_expectations.") from e

        # Process additional fields



    def __str__(self):
        def format_dataclass(obj):
            return "\n".join(f"{field.name}: {getattr(obj, field.name)}" for field in obj.__dataclass_fields__.values())

        return (f"Self Identification:\n{format_dataclass(self.self_identification)}\n\n"
                f"Legal Authorization:\n{format_dataclass(self.legal_authorization)}\n\n"
                f"Work Preferences:\n{format_dataclass(self.work_preferences)}\n\n"
                f"Availability: {self.availability.notice_period}\n\n"
                f"Salary Expectations: {self.salary_expectations.salary_range_usd}\n\n")
