import yaml
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Dict, Optional, Union

# Definizione dei modelli Pydantic
class PersonalInformation(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    date_of_birth: Optional[str]
    country: Optional[str]
    city: Optional[str]
    address: Optional[str]
    phone_prefix: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    github: Optional[HttpUrl]
    linkedin: Optional[HttpUrl]

class EducationDetails(BaseModel):
    degree: Optional[str]
    university: Optional[str]
    gpa: Optional[str]
    graduation_year: Optional[int]
    field_of_study: Optional[str]
    exam: Optional[Union[List[Dict[str, str]], Dict[str, str]]]

class ExperienceDetails(BaseModel):
    position: Optional[str]
    company: Optional[str]
    employment_period: Optional[str]
    location: Optional[str]
    industry: Optional[str]
    key_responsibilities: Optional[List[Dict[str, str]]]
    skills_acquired: Optional[List[str]]

class Project(BaseModel):
    name: Optional[str]
    description: Optional[str]
    link: Optional[HttpUrl]

class Achievement(BaseModel):
    name: Optional[str]
    description: Optional[str]

class Language(BaseModel):
    language: Optional[str]
    proficiency: Optional[str]

class Availability(BaseModel):
    notice_period: Optional[str]

class SalaryExpectations(BaseModel):
    salary_range_usd: Optional[str]

class SelfIdentification(BaseModel):
    gender: Optional[str]
    pronouns: Optional[str]
    veteran: Optional[str]
    disability: Optional[str]
    ethnicity: Optional[str]

class LegalAuthorization(BaseModel):
    eu_work_authorization: Optional[str]
    us_work_authorization: Optional[str]
    requires_us_visa: Optional[str]
    requires_us_sponsorship: Optional[str]
    requires_eu_visa: Optional[str]  # Added field
    legally_allowed_to_work_in_eu: Optional[str]  # Added field
    legally_allowed_to_work_in_us: Optional[str]  # Added field
    requires_eu_sponsorship: Optional[str]

class Resume(BaseModel):
    personal_information: Optional[PersonalInformation]
    education_details: Optional[List[EducationDetails]]
    experience_details: Optional[List[ExperienceDetails]]
    projects: Optional[List[Project]]
    achievements: Optional[List[Achievement]]
    certifications: Optional[List[str]]
    languages: Optional[List[Language]]
    interests: Optional[List[str]]
    availability: Optional[Availability]
    salary_expectations: Optional[SalaryExpectations]
    self_identification: Optional[SelfIdentification]
    legal_authorization: Optional[LegalAuthorization]
    
    @staticmethod
    def normalize_exam_format(exam):
        if isinstance(exam, dict):
            return [{k: v} for k, v in exam.items()]
        return exam

    
    def __init__(self, yaml_str: str):
        try:
            # Parse the YAML string
            data = yaml.safe_load(yaml_str)

            # Normalize the exam format
            if 'education_details' in data:
                for ed in data['education_details']:
                    if 'exam' in ed:
                        ed['exam'] = self.normalize_exam_format(ed['exam'])

            # Create an instance of Resume from the parsed data
            super().__init__(**data)
        except yaml.YAMLError as e:
            raise ValueError("Error parsing YAML file.") from e
        except Exception as e:
            raise Exception(f"Unexpected error while parsing YAML: {e}") from e
