# In this file, you can set the configurations of the app.
from pathlib import Path

from constants import DEBUG, LLM_MODEL, OPENAI

#config related to logging must have prefix LOG_
LOG_LEVEL = DEBUG
LOG_SELENIUM_LEVEL = DEBUG
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

MINIMUM_WAIT_TIME_IN_SECONDS = 60
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE_DIRECTORY = BASE_DIR / 'data_folder' / 'output'

JOB_APPLICATIONS_DIR = "job_applications"
JOB_SUITABILITY_SCORE = 7

JOB_MAX_APPLICATIONS = 100
JOB_MIN_APPLICATIONS = 0

LLM_MODEL_TYPE = 'openai'
LLM_MODEL = 'gpt-4o-mini'
# Only required for OLLAMA models
LLM_API_URL = ''

ABBREVIATIONS = {
    "Senior": "Sr",
    "Junior": "Jr",
    "Data Engineer": "DE",
    "Data engineer": "DE",
    "data engineer": "DE",
    "Software Engineer": "SWE",
    "Developer": "Dev",
    "Python": "Py",
    "Data Scientist": "DS",
    "Machine Learning Engineer": "MLE",
    "Frontend Developer": "FE Dev",
    "Backend Developer": "BE Dev",
    "Full Stack Developer": "FS Dev",
    "DevOps Engineer": "DevOps",
    "Quality Assurance Engineer": "QA",
    "Product Manager": "PM",
    "Project Manager": "ProjM",
    "Business Analyst": "BA",
    "Scrum Master": "ScrumM",
    "UI/UX Designer": "UIUX",
    "Database Administrator": "DBA",
    "System Administrator": "SysAdmin",
    "Cloud Engineer": "CloudE",
    "Security Engineer": "SecE",
    "Network Engineer": "NetE",
    "IT Support Specialist": "ITSupport",
    "Solution Architect": "SA",
    "Technical Lead": "TechLead",
    "Chief Technology Officer": "CTO",
    "Chief Information Officer": "CIO",
    "Cybersecurity Specialist": "CyberSec",
    "Mobile App Developer": "MobileDev",
    "Blockchain Developer": "BlockDev",
    "Site Reliability Engineer": "SRE",
    "AI Engineer": "AIE",
    "Big Data Engineer": "BigDE",
    "Embedded Systems Engineer": "EmbedE",
    "Hardware Engineer": "HwE",
    "Network Administrator": "NetAdmin",
    "Game Developer": "GameDev",
    "Research Scientist": "RS",
    "Test Automation Engineer": "TestAuto",
    "Digital Marketing Specialist": "DMS",
    "Technical Support Engineer": "TechSupport",
    "Data Analyst": "DA",
    "Cloud Architect": "CloudArch"
}