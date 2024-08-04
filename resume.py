from dataclasses import dataclass
from typing import Dict
import yaml

@dataclass
class PersonalInformation:
    name: str
    surname: str
    dateOfBirth: str
    country: str
    city: str
    address: str
    phone: str
    phonePrefix: str
    email: str
    github: str
    linkedin: str

@dataclass
class SelfIdentification:
    gender: str
    pronouns: str
    veteran: str
    disability: str
    ethnicity: str

@dataclass
class LegalAuthorization:
    euWorkAuthorization: str
    usWorkAuthorization: str
    requiresUsVisa: str
    legallyAllowedToWorkInUs: str
    requiresUsSponsorship: str
    requiresEuVisa: str
    legallyAllowedToWorkInEu: str
    requiresEuSponsorship: str

@dataclass
class WorkPreferences:
    remoteWork: str
    inPersonWork: str
    openToRelocation: str
    willingToCompleteAssessments: str
    willingToUndergoDrugTests: str
    willingToUndergoBackgroundChecks: str

@dataclass
class Education:
    degree: str
    university: str
    gpa: str
    graduationYear: str
    fieldOfStudy: str
    skillsAcquired: Dict[str, str]

@dataclass
class Experience:
    position: str
    company: str
    employmentPeriod: str
    location: str
    industry: str
    keyResponsibilities: Dict[str, str]
    skillsAcquired: Dict[str, str]

@dataclass
class Availability:
    noticePeriod: str

@dataclass
class SalaryExpectations:
    salaryRangeUSD: str

@dataclass
class Language:
    language: str
    proficiency: str

class Resume:
    def __init__(self, yaml_str: str):
        data = yaml.safe_load(yaml_str)
        self.personal_information = PersonalInformation(**data['personal_information'])
        self.self_identification = SelfIdentification(**data['self_identification'])
        self.legal_authorization = LegalAuthorization(**data['legal_authorization'])
        self.work_preferences = WorkPreferences(**data['work_preferences'])
        self.education_details = [Education(**edu) for edu in data['education_details']]
        self.experience_details = [Experience(**exp) for exp in data['experience_details']]
        self.projects = data['projects']
        self.availability = Availability(**data['availability'])
        self.salary_expectations = SalaryExpectations(**data['salary_expectations'])
        self.certifications = data['certifications']
        self.languages = [Language(**lang) for lang in data['languages']]
        self.interests = data['interests']

    def __str__(self):
        def format_dict(dict_obj):
            return "\n".join(f"{key}: {value}" for key, value in dict_obj.items())

        def format_dataclass(obj):
            return "\n".join(f"{field.name}: {getattr(obj, field.name)}" for field in obj.__dataclass_fields__.values())

        return ("Personal Information:\n" + format_dataclass(self.personal_information) + "\n\n"
                "Self Identification:\n" + format_dataclass(self.self_identification) + "\n\n"
                "Legal Authorization:\n" + format_dataclass(self.legal_authorization) + "\n\n"
                "Work Preferences:\n" + format_dataclass(self.work_preferences) + "\n\n"
                "Education Details:\n" + "\n".join(
                    f"  - {edu.degree} in {edu.fieldOfStudy} from {edu.university}, "
                    f"GPA: {edu.gpa}, Graduation Year: {edu.graduationYear}\n"
                    f"    Skills Acquired:\n{format_dict(edu.skillsAcquired)}"
                    for edu in self.education_details
                ) + "\n\n"
                "Experience Details:\n" + "\n".join(
                    f"  - {exp.position} at {exp.company} ({exp.employmentPeriod}), {exp.location}, {exp.industry}\n"
                    f"    Key Responsibilities:\n{format_dict(exp.keyResponsibilities)}\n"
                    f"    Skills Acquired:\n{format_dict(exp.skillsAcquired)}"
                    for exp in self.experience_details
                ) + "\n\n"
                "Projects:\n" + "\n".join(f"  - {proj}" for proj in self.projects.values()) + "\n\n"
                f"Availability: {self.availability.noticePeriod}\n\n"
                f"Salary Expectations: {self.salary_expectations.salaryRangeUSD}\n\n"
                "Certifications: " + ", ".join(self.certifications) + "\n\n"
                "Languages:\n" + "\n".join(
                    f"  - {lang.language} ({lang.proficiency})"
                    for lang in self.languages
                ) + "\n\n"
                "Interests:\n" + ", ".join(self.interests)
            )
